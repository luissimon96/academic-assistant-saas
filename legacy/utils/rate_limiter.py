"""
Sistema de Rate Limiting para Academic Assistant Stealth

Este módulo implementa controle de taxa de requisições para:
- Proteger contra abuse de API
- Evitar custos excessivos 
- Garantir estabilidade do sistema
- Implementar backoff exponencial
"""

import time
import threading
from typing import Dict, Optional, Callable, Any
from dataclasses import dataclass, field
from collections import defaultdict, deque
import logging
from functools import wraps
import json
from pathlib import Path

@dataclass
class RateLimitConfig:
    """Configuração de rate limiting"""
    max_requests: int = 60          # Máximo de requisições
    time_window: int = 60           # Janela de tempo em segundos  
    burst_limit: int = 10           # Limite de rajada
    backoff_factor: float = 2.0     # Fator de backoff exponencial
    max_backoff: float = 300.0      # Backoff máximo em segundos
    enable_persistence: bool = True  # Salvar estado em arquivo

class RateLimiter:
    """
    Rate Limiter thread-safe com suporte a:
    - Token bucket algorithm
    - Backoff exponencial  
    - Persistência de estado
    - Métricas de uso
    """
    
    def __init__(self, config: RateLimitConfig, name: str = "default"):
        self.config = config
        self.name = name
        self._lock = threading.RLock()
        
        # Token bucket implementation
        self._tokens = config.max_requests
        self._last_update = time.time()
        
        # Request history para janela deslizante
        self._request_history: deque = deque()
        
        # Backoff tracking
        self._consecutive_failures = 0
        self._last_failure_time = 0
        
        # Métricas
        self._total_requests = 0
        self._rejected_requests = 0
        self._reset_count = 0
        
        # Persistence
        self._state_file = Path("config") / f"rate_limit_{name}.json"
        if config.enable_persistence:
            self._load_state()
        
        self.logger = logging.getLogger(f"rate_limiter.{name}")
        self.logger.info(f"🚦 Rate Limiter inicializado: {config.max_requests}/{config.time_window}s")

    def is_allowed(self, tokens_required: int = 1) -> tuple[bool, float]:
        """
        Verifica se a requisição é permitida
        
        Returns:
            tuple[bool, float]: (permitido, tempo_para_retry)
        """
        with self._lock:
            current_time = time.time()
            
            # Atualiza tokens (token bucket algorithm)
            self._update_tokens(current_time)
            
            # Remove requisições antigas da janela
            self._clean_old_requests(current_time)
            
            # Verifica backoff se há falhas consecutivas
            if self._consecutive_failures > 0:
                backoff_time = self._calculate_backoff()
                if current_time - self._last_failure_time < backoff_time:
                    remaining_time = backoff_time - (current_time - self._last_failure_time)
                    self.logger.warning(f"⏳ Backoff ativo: {remaining_time:.1f}s restantes")
                    return False, remaining_time

            # Verifica limite de tokens
            if self._tokens >= tokens_required:
                # Verifica limite da janela deslizante
                if len(self._request_history) < self.config.max_requests:
                    # Permite a requisição
                    self._tokens -= tokens_required
                    self._request_history.append(current_time)
                    self._total_requests += 1
                    
                    # Reset consecutive failures em caso de sucesso
                    if self._consecutive_failures > 0:
                        self.logger.info(f"✅ Rate limiter recuperado após {self._consecutive_failures} falhas")
                        self._consecutive_failures = 0
                    
                    self._save_state()
                    return True, 0.0
            
            # Requisição rejeitada
            self._rejected_requests += 1
            retry_time = self._calculate_retry_time(current_time)
            
            self.logger.warning(
                f"🚫 Rate limit excedido: {len(self._request_history)}/{self.config.max_requests} "
                f"requisições na janela. Retry em {retry_time:.1f}s"
            )
            
            return False, retry_time

    def record_failure(self):
        """Registra uma falha para o sistema de backoff"""
        with self._lock:
            self._consecutive_failures += 1
            self._last_failure_time = time.time()
            
            self.logger.warning(
                f"❌ Falha registrada: {self._consecutive_failures} consecutivas. "
                f"Backoff: {self._calculate_backoff():.1f}s"
            )
            self._save_state()

    def record_success(self):
        """Registra um sucesso (reset do backoff)"""
        with self._lock:
            if self._consecutive_failures > 0:
                self.logger.info(f"✅ Sucesso após {self._consecutive_failures} falhas")
                self._consecutive_failures = 0
                self._save_state()

    def reset(self):
        """Reset completo do rate limiter"""
        with self._lock:
            self._tokens = self.config.max_requests
            self._request_history.clear()
            self._consecutive_failures = 0
            self._last_failure_time = 0
            self._reset_count += 1
            self._last_update = time.time()
            
            self.logger.info(f"🔄 Rate limiter resetado (reset #{self._reset_count})")
            self._save_state()

    def get_status(self) -> Dict[str, Any]:
        """Retorna status detalhado do rate limiter"""
        with self._lock:
            current_time = time.time()
            self._update_tokens(current_time)
            self._clean_old_requests(current_time)
            
            backoff_remaining = 0
            if self._consecutive_failures > 0:
                backoff_time = self._calculate_backoff()
                backoff_remaining = max(0, backoff_time - (current_time - self._last_failure_time))
            
            return {
                'name': self.name,
                'tokens_available': self._tokens,
                'max_tokens': self.config.max_requests,
                'requests_in_window': len(self._request_history),
                'window_size': self.config.time_window,
                'consecutive_failures': self._consecutive_failures,
                'backoff_remaining': backoff_remaining,
                'total_requests': self._total_requests,
                'rejected_requests': self._rejected_requests,
                'success_rate': (self._total_requests - self._rejected_requests) / max(1, self._total_requests) * 100,
                'reset_count': self._reset_count,
                'is_healthy': backoff_remaining == 0 and self._tokens > 0
            }

    def _update_tokens(self, current_time: float):
        """Atualiza tokens baseado no tempo decorrido"""
        time_passed = current_time - self._last_update
        self._last_update = current_time
        
        # Adiciona tokens baseado no tempo (refill rate)
        tokens_to_add = time_passed * (self.config.max_requests / self.config.time_window)
        self._tokens = min(self.config.max_requests, self._tokens + tokens_to_add)

    def _clean_old_requests(self, current_time: float):
        """Remove requisições antigas da janela"""
        cutoff_time = current_time - self.config.time_window
        while self._request_history and self._request_history[0] < cutoff_time:
            self._request_history.popleft()

    def _calculate_backoff(self) -> float:
        """Calcula tempo de backoff exponencial"""
        backoff = min(
            self.config.max_backoff,
            self.config.backoff_factor ** (self._consecutive_failures - 1)
        )
        return backoff

    def _calculate_retry_time(self, current_time: float) -> float:
        """Calcula tempo até próxima tentativa permitida"""
        if not self._request_history:
            return 0.0
        
        # Tempo até a requisição mais antiga sair da janela
        oldest_request = self._request_history[0]
        time_until_window_reset = (oldest_request + self.config.time_window) - current_time
        
        # Tempo para regenerar tokens
        tokens_needed = 1 - self._tokens
        time_for_tokens = tokens_needed * (self.config.time_window / self.config.max_requests)
        
        return max(0, min(time_until_window_reset, time_for_tokens))

    def _save_state(self):
        """Salva estado persistente"""
        if not self.config.enable_persistence:
            return
        
        try:
            state = {
                'tokens': self._tokens,
                'last_update': self._last_update,
                'consecutive_failures': self._consecutive_failures,
                'last_failure_time': self._last_failure_time,
                'total_requests': self._total_requests,
                'rejected_requests': self._rejected_requests,
                'reset_count': self._reset_count,
                'request_history': list(self._request_history)
            }
            
            self._state_file.parent.mkdir(exist_ok=True)
            with open(self._state_file, 'w') as f:
                json.dump(state, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"❌ Erro ao salvar estado: {e}")

    def _load_state(self):
        """Carrega estado persistente"""
        try:
            if not self._state_file.exists():
                return
            
            with open(self._state_file, 'r') as f:
                state = json.load(f)
            
            current_time = time.time()
            
            # Valida se o estado não é muito antigo (max 1 hora)
            if current_time - state.get('last_update', 0) > 3600:
                self.logger.info("🔄 Estado muito antigo, iniciando fresh")
                return
            
            self._tokens = state.get('tokens', self.config.max_requests)
            self._last_update = state.get('last_update', current_time)
            self._consecutive_failures = state.get('consecutive_failures', 0)
            self._last_failure_time = state.get('last_failure_time', 0)
            self._total_requests = state.get('total_requests', 0)
            self._rejected_requests = state.get('rejected_requests', 0)
            self._reset_count = state.get('reset_count', 0)
            
            # Reconstrói history válida
            history = state.get('request_history', [])
            cutoff_time = current_time - self.config.time_window
            self._request_history = deque([t for t in history if t > cutoff_time])
            
            self.logger.info(f"📄 Estado carregado: {len(self._request_history)} requisições na janela")
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao carregar estado: {e}")

class RateLimitManager:
    """Gerenciador global de rate limiters"""
    
    def __init__(self):
        self._limiters: Dict[str, RateLimiter] = {}
        self._lock = threading.RLock()
        self.logger = logging.getLogger("rate_limit_manager")

    def get_limiter(self, name: str, config: Optional[RateLimitConfig] = None) -> RateLimiter:
        """Obtém ou cria um rate limiter"""
        with self._lock:
            if name not in self._limiters:
                if config is None:
                    config = RateLimitConfig()  # Configuração padrão
                
                self._limiters[name] = RateLimiter(config, name)
                self.logger.info(f"🆕 Rate limiter '{name}' criado")
            
            return self._limiters[name]

    def get_global_status(self) -> Dict[str, Any]:
        """Status de todos os rate limiters"""
        with self._lock:
            return {
                name: limiter.get_status() 
                for name, limiter in self._limiters.items()
            }

    def reset_all(self):
        """Reset de todos os rate limiters"""
        with self._lock:
            for limiter in self._limiters.values():
                limiter.reset()
            self.logger.info("🔄 Todos os rate limiters resetados")

# Instância global
rate_limit_manager = RateLimitManager()

# Decorador para rate limiting
def rate_limited(limiter_name: str = "default", 
                config: Optional[RateLimitConfig] = None,
                retry_attempts: int = 3,
                retry_delay: float = 1.0):
    """
    Decorador para aplicar rate limiting a funções
    
    Args:
        limiter_name: Nome do rate limiter
        config: Configuração específica (opcional)
        retry_attempts: Tentativas de retry
        retry_delay: Delay entre retries
    """
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            limiter = rate_limit_manager.get_limiter(limiter_name, config)
            
            for attempt in range(retry_attempts + 1):
                allowed, wait_time = limiter.is_allowed()
                
                if allowed:
                    try:
                        result = func(*args, **kwargs)
                        limiter.record_success()
                        return result
                    except Exception as e:
                        limiter.record_failure()
                        if attempt == retry_attempts:
                            raise
                        
                        # Espera antes de retry
                        time.sleep(retry_delay * (2 ** attempt))
                else:
                    if attempt == retry_attempts:
                        raise RuntimeError(
                            f"Rate limit excedido para '{limiter_name}'. "
                            f"Tente novamente em {wait_time:.1f}s"
                        )
                    
                    # Espera o tempo sugerido
                    time.sleep(min(wait_time, retry_delay * (2 ** attempt)))
        
        return wrapper
    return decorator 