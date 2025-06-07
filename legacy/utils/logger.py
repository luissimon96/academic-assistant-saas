"""
Sistema de logging robusto para Academic Assistant Stealth
Captura todos os eventos importantes para análise e debug
"""

import logging
import logging.handlers
import os
import sys
import threading
import time
import traceback
from datetime import datetime
from typing import Any, Dict, Optional
from functools import wraps
from config import config

class ThreadSafeLogger:
    """Logger thread-safe com funcionalidades avançadas"""
    
    def __init__(self, name: str = "AcademicAssistant"):
        self.name = name
        self.logger = self._setup_logger()
        self._thread_data = threading.local()
        
    def _setup_logger(self) -> logging.Logger:
        """Configura o sistema de logging"""
        
        # Cria logger principal
        logger = logging.getLogger(self.name)
        logger.setLevel(logging.DEBUG)
        
        # Evita duplicação de handlers
        if logger.handlers:
            return logger
        
        # Formatter simples e robusto
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(threadName)-15s | %(name)-20s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Handler para console com ASCII compatível (Windows cp1252)
        class ASCIIFormatter(logging.Formatter):
            def format(self, record):
                # Converte emojis para texto ASCII para compatibilidade Windows
                msg = super().format(record)
                emoji_map = {
                    '🔧': '[INIT]',
                    '✅': '[OK]',
                    '❌': '[ERROR]',
                    '⚠️': '[WARN]',
                    '🎯': '[SYSTEM]',
                    '🧵': '[THREAD]',
                    '⚡': '[PERF]',
                    '📊': '[DATA]',
                    '🔍': '[DEBUG]',
                    '🚀': '[START]',
                    '💾': '[SAVE]',
                    '🔄': '[PROC]',
                    '⏱️': '[TIME]',
                    '🖥️': '[UI]',
                    '🌐': '[API]',
                    '📁': '[FILE]'
                }
                for emoji, text in emoji_map.items():
                    msg = msg.replace(emoji, text)
                return msg
        
        console_formatter = ASCIIFormatter(
            '%(asctime)s | %(levelname)-8s | %(threadName)-15s | %(name)-20s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # Handler para arquivo principal (UTF-8 para manter emojis)
        if not os.path.exists(config.LOGS_DIR):
            os.makedirs(config.LOGS_DIR, exist_ok=True)
            
        file_handler = logging.handlers.RotatingFileHandler(
            os.path.join(config.LOGS_DIR, 'academic_assistant.log'),
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'  # UTF-8 para suportar emojis nos arquivos
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Handler para erros críticos (UTF-8)
        error_handler = logging.handlers.RotatingFileHandler(
            os.path.join(config.LOGS_DIR, 'errors.log'),
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        logger.addHandler(error_handler)
        
        # Handler para threading debug (UTF-8)
        threading_handler = logging.handlers.RotatingFileHandler(
            os.path.join(config.LOGS_DIR, 'threading.log'),
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        threading_handler.setLevel(logging.DEBUG)
        threading_handler.addFilter(self._threading_filter)
        threading_handler.setFormatter(formatter)
        logger.addHandler(threading_handler)
        
        return logger
    
    def _threading_filter(self, record):
        """Filtro para logs relacionados a threading"""
        threading_keywords = [
            'thread', 'worker', 'signal', 'queue', 'mutex', 
            'lock', 'async', 'concurrent', 'main_thread'
        ]
        return any(keyword in record.getMessage().lower() for keyword in threading_keywords)
    
    def _get_thread_info(self) -> Dict[str, Any]:
        """Obtém informações detalhadas da thread atual"""
        current_thread = threading.current_thread()
        is_main = current_thread == threading.main_thread()
        
        return {
            'thread_id': current_thread.ident,
            'thread_name': current_thread.name,
            'is_main_thread': is_main,
            'is_daemon': current_thread.daemon,
            'is_alive': current_thread.is_alive()
        }
    
    def debug(self, message: str, **kwargs):
        """Log debug com informações de thread"""
        thread_info = self._get_thread_info()
        self.logger.debug(f"[{thread_info['thread_name']}] {message}", extra=kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info"""
        self.logger.info(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning"""
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """Log error com traceback detalhado"""
        thread_info = self._get_thread_info()
        
        error_msg = f"[{thread_info['thread_name']}] {message}"
        
        if exception:
            error_msg += f"\nException: {type(exception).__name__}: {exception}"
            error_msg += f"\nTraceback: {traceback.format_exc()}"
        
        self.logger.error(error_msg, extra=kwargs)
    
    def critical(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """Log critical com informações completas"""
        thread_info = self._get_thread_info()
        
        critical_msg = f"[CRITICAL][{thread_info['thread_name']}] {message}"
        critical_msg += f"\nThread Info: {thread_info}"
        
        if exception:
            critical_msg += f"\nException: {type(exception).__name__}: {exception}"
            critical_msg += f"\nTraceback: {traceback.format_exc()}"
        
        self.logger.critical(critical_msg, extra=kwargs)
    
    def log_performance(self, operation: str, duration: float, **kwargs):
        """Log performance de operações"""
        self.info(f"⏱️ PERFORMANCE: {operation} completed in {duration:.3f}s", **kwargs)
    
    def log_threading_operation(self, operation: str, details: Dict[str, Any]):
        """Log específico para operações de threading"""
        thread_info = self._get_thread_info()
        
        message = f"🧵 THREADING: {operation}"
        message += f"\nCurrent Thread: {thread_info}"
        message += f"\nOperation Details: {details}"
        
        self.debug(message)
    
    def log_qt_operation(self, operation: str, widget_info: Dict[str, Any]):
        """Log específico para operações Qt"""
        thread_info = self._get_thread_info()
        
        message = f"🖥️ QT_UI: {operation}"
        message += f"\nThread: {thread_info['thread_name']} (Main: {thread_info['is_main_thread']})"
        message += f"\nWidget Info: {widget_info}"
        
        self.debug(message)
    
    def log_api_request(self, endpoint: str, duration: float, success: bool, **kwargs):
        """Log específico para requisições API"""
        status = "✅ SUCCESS" if success else "❌ FAILED"
        self.info(f"🌐 API: {endpoint} - {status} ({duration:.3f}s)", **kwargs)
    
    def log_file_operation(self, operation: str, filepath: str, success: bool, **kwargs):
        """Log específico para operações de arquivo"""
        status = "✅ SUCCESS" if success else "❌ FAILED"
        self.info(f"📁 FILE: {operation} - {filepath} - {status}", **kwargs)
    
    def log_system_event(self, event: str, details: Dict[str, Any]):
        """Log para eventos do sistema"""
        self.info(f"🎯 SYSTEM: {event} - {details}")


def performance_monitor(operation_name: str):
    """Decorator para monitorar performance de funções"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = None
            error = None
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                error = e
                raise
            finally:
                duration = time.time() - start_time
                
                # Log performance
                logger.log_performance(
                    f"{operation_name}::{func.__name__}",
                    duration,
                    success=(error is None),
                    args_count=len(args),
                    kwargs_count=len(kwargs)
                )
                
                if error:
                    logger.error(f"Performance monitor caught error in {operation_name}::{func.__name__}", error)
        
        return wrapper
    return decorator


def thread_safety_monitor(func):
    """Decorator para monitorar thread safety"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        thread_info = {
            'function': f"{func.__module__}.{func.__name__}",
            'thread_id': threading.current_thread().ident,
            'thread_name': threading.current_thread().name,
            'is_main_thread': threading.current_thread() == threading.main_thread()
        }
        
        logger.log_threading_operation(f"CALL: {func.__name__}", thread_info)
        
        try:
            result = func(*args, **kwargs)
            logger.log_threading_operation(f"SUCCESS: {func.__name__}", thread_info)
            return result
        except Exception as e:
            logger.log_threading_operation(f"ERROR: {func.__name__}", {
                **thread_info,
                'error': str(e),
                'error_type': type(e).__name__
            })
            raise
    
    return wrapper


def log_exceptions(func):
    """Decorator para capturar e logar todas as exceções"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(
                f"Exception in {func.__module__}.{func.__name__}",
                exception=e,
                args_count=len(args),
                kwargs_keys=list(kwargs.keys()) if kwargs else []
            )
            raise
    
    return wrapper


class ComponentLogger:
    """Logger específico para componentes com delegação completa"""
    
    def __init__(self, component_name: str):
        self.component_name = component_name
        self.logger = logger
    
    def log_init(self, details: Dict[str, Any]):
        """Log inicialização do componente"""
        self.logger.info(f"🔧 INIT: {self.component_name}", component=self.component_name, **details)
    
    def log_operation(self, operation: str, success: bool, details: Dict[str, Any] = None):
        """Log operação do componente"""
        status = "✅" if success else "❌"
        self.logger.info(
            f"{status} {self.component_name}: {operation}",
            component=self.component_name,
            operation=operation,
            success=success,
            **(details or {})
        )
    
    def log_error(self, operation: str, error: Exception, details: Dict[str, Any] = None):
        """Log erro do componente"""
        self.logger.error(
            f"❌ {self.component_name}: {operation} FAILED",
            exception=error,
            component=self.component_name,
            operation=operation,
            **(details or {})
        )
    
    def log_state_change(self, from_state: str, to_state: str, details: Dict[str, Any] = None):
        """Log mudança de estado"""
        self.logger.info(
            f"🔄 {self.component_name}: {from_state} → {to_state}",
            component=self.component_name,
            from_state=from_state,
            to_state=to_state,
            **(details or {})
        )
    
    def log_performance(self, operation: str, duration: float, details: Dict[str, Any] = None):
        """Log performance do componente"""
        self.logger.info(
            f"⏱️ {self.component_name}: {operation} ({duration:.3f}s)",
            component=self.component_name,
            operation=operation,
            duration=duration,
            **(details or {})
        )
    
    # ===== MÉTODOS DELEGADOS PARA COMPATIBILIDADE COMPLETA =====
    
    def log_file_operation(self, operation: str, filepath: str, success: bool, details: Dict[str, Any] = None):
        """Log operação de arquivo com contexto do componente"""
        status = "✅ SUCCESS" if success else "❌ FAILED" 
        self.logger.info(
            f"📁 {self.component_name}: FILE_{operation} - {filepath} - {status}",
            component=self.component_name,
            operation=f"FILE_{operation}",
            filepath=filepath,
            success=success,
            **(details or {})
        )
    
    def log_api_request(self, endpoint: str, duration: float, success: bool, details: Dict[str, Any] = None):
        """Log requisição API com contexto do componente"""
        status = "✅ SUCCESS" if success else "❌ FAILED"
        self.logger.info(
            f"🌐 {self.component_name}: API_{endpoint} - {status} ({duration:.3f}s)",
            component=self.component_name,
            operation=f"API_{endpoint}",
            duration=duration,
            success=success,
            **(details or {})
        )
    
    def log_qt_operation(self, operation: str, widget_info: Dict[str, Any]):
        """Log operação Qt com contexto do componente"""
        self.logger.info(
            f"🖥️ {self.component_name}: QT_{operation}",
            component=self.component_name,
            operation=f"QT_{operation}",
            widget_info=widget_info
        )
    
    def log_threading_operation(self, operation: str, details: Dict[str, Any]):
        """Log operação de threading com contexto do componente"""
        self.logger.info(
            f"🧵 {self.component_name}: THREAD_{operation}",
            component=self.component_name,
            operation=f"THREAD_{operation}",
            thread_details=details
        )
    
    def log_system_event(self, event: str, details: Dict[str, Any]):
        """Log evento do sistema com contexto do componente"""
        self.logger.info(
            f"🎯 {self.component_name}: SYSTEM_{event}",
            component=self.component_name,
            event=event,
            system_details=details
        )
    
    # ===== DELEGAÇÃO PARA MÉTODOS BÁSICOS =====
    
    def debug(self, message: str, **kwargs):
        """Debug com contexto do componente"""
        self.logger.debug(f"[{self.component_name}] {message}", component=self.component_name, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Info com contexto do componente"""
        self.logger.info(f"{message}", component=self.component_name, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Warning com contexto do componente"""
        self.logger.warning(f"⚠️ {self.component_name}: {message}", component=self.component_name, **kwargs)
    
    def error(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """Error com contexto do componente"""
        self.logger.error(f"❌ {self.component_name}: {message}", exception=exception, component=self.component_name, **kwargs)
    
    def critical(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """Critical com contexto do componente"""
        self.logger.critical(f"🚨 {self.component_name}: {message}", exception=exception, component=self.component_name, **kwargs)


# Logger global singleton
logger = ThreadSafeLogger()

# Função para obter logger de componente
def get_component_logger(component_name: str) -> ComponentLogger:
    """Obtém logger específico para componente"""
    return ComponentLogger(component_name)


# Setup inicial
if __name__ != "__main__":
    logger.info("🚀 Academic Assistant Stealth Logger initialized")
    logger.log_system_event("LOGGER_INIT", {
        'timestamp': datetime.now().isoformat(),
        'python_version': sys.version,
        'thread_count': threading.active_count()
    }) 