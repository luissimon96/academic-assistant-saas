"""
Sistema de Cache Inteligente para Academic Assistant Stealth

Este módulo implementa cache multi-nível para:
- Reduzir chamadas à API desnecessárias
- Melhorar tempo de resposta
- Otimizar uso de recursos
- Cache de imagens processadas
- Cache de respostas de IA
"""

import hashlib
import json
import time
import threading
from typing import Dict, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import pickle
import logging
import sqlite3
from collections import OrderedDict
import os
import zlib
from PIL import Image
import io

@dataclass
class CacheConfig:
    """Configuração do sistema de cache"""
    max_memory_items: int = 1000        # Máximo de itens na memória
    max_disk_size_mb: int = 500         # Máximo em disco em MB
    default_ttl: int = 3600             # TTL padrão em segundos
    image_ttl: int = 86400              # TTL para imagens (24h)
    response_ttl: int = 7200            # TTL para respostas (2h)
    enable_compression: bool = True      # Compressão para cache em disco
    enable_persistence: bool = True      # Persistência em disco
    cleanup_interval: int = 300         # Intervalo de limpeza em segundos

class CacheEntry:
    """Entrada de cache com metadados"""
    
    def __init__(self, key: str, value: Any, ttl: int = 3600):
        self.key = key
        self.value = value
        self.created_at = time.time()
        self.expires_at = self.created_at + ttl
        self.access_count = 1
        self.last_accessed = self.created_at
        self.size_bytes = self._calculate_size(value)
    
    def _calculate_size(self, value: Any) -> int:
        """Calcula tamanho aproximado do valor em bytes"""
        try:
            if isinstance(value, (str, bytes)):
                return len(value.encode() if isinstance(value, str) else value)
            elif isinstance(value, dict):
                return len(json.dumps(value).encode())
            else:
                return len(pickle.dumps(value))
        except:
            return 1024  # Estimativa padrão
    
    def is_expired(self) -> bool:
        """Verifica se a entrada expirou"""
        return time.time() > self.expires_at
    
    def access(self):
        """Registra acesso à entrada"""
        self.access_count += 1
        self.last_accessed = time.time()
    
    def get_age(self) -> float:
        """Retorna idade da entrada em segundos"""
        return time.time() - self.created_at

class ImageCache:
    """Cache especializado para imagens"""
    
    def __init__(self, cache_dir: Path, max_size_mb: int = 100):
        self.cache_dir = cache_dir / "images"
        self.cache_dir.mkdir(exist_ok=True, parents=True)
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.logger = logging.getLogger("cache.images")
    
    def _get_image_hash(self, image_data: bytes) -> str:
        """Gera hash único para a imagem"""
        return hashlib.sha256(image_data).hexdigest()[:16]
    
    def _get_cache_path(self, image_hash: str) -> Path:
        """Retorna caminho do arquivo de cache"""
        return self.cache_dir / f"{image_hash}.cache"
    
    def store(self, image_data: bytes, processed_text: str, 
             metadata: Optional[Dict] = None) -> str:
        """Armazena imagem processada no cache"""
        try:
            image_hash = self._get_image_hash(image_data)
            cache_path = self._get_cache_path(image_hash)
            
            cache_entry = {
                'text': processed_text,
                'metadata': metadata or {},
                'timestamp': time.time(),
                'image_size': len(image_data)
            }
            
            # Comprime e salva
            compressed_data = zlib.compress(json.dumps(cache_entry).encode())
            cache_path.write_bytes(compressed_data)
            
            self.logger.debug(f"🖼️ Imagem cached: {image_hash}")
            self._cleanup_if_needed()
            
            return image_hash
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao cachear imagem: {e}")
            return ""
    
    def get(self, image_data: bytes) -> Optional[Tuple[str, Dict]]:
        """Recupera texto processado da imagem"""
        try:
            image_hash = self._get_image_hash(image_data)
            cache_path = self._get_cache_path(image_hash)
            
            if not cache_path.exists():
                return None
            
            # Descomprime e carrega
            compressed_data = cache_path.read_bytes()
            cache_entry = json.loads(zlib.decompress(compressed_data).decode())
            
            # Verifica TTL (24 horas para imagens)
            if time.time() - cache_entry['timestamp'] > 86400:
                cache_path.unlink(missing_ok=True)
                return None
            
            # Atualiza timestamp de acesso
            cache_path.touch()
            
            self.logger.debug(f"🎯 Cache hit para imagem: {image_hash}")
            return cache_entry['text'], cache_entry['metadata']
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao recuperar imagem do cache: {e}")
            return None
    
    def _cleanup_if_needed(self):
        """Limpa cache se exceder tamanho máximo"""
        try:
            total_size = sum(
                f.stat().st_size for f in self.cache_dir.glob("*.cache")
                if f.is_file()
            )
            
            if total_size > self.max_size_bytes:
                # Remove arquivos mais antigos
                files = list(self.cache_dir.glob("*.cache"))
                files.sort(key=lambda f: f.stat().st_atime)
                
                removed_count = 0
                for file in files:
                    if total_size <= self.max_size_bytes * 0.8:  # Remove até 80%
                        break
                    
                    file_size = file.stat().st_size
                    file.unlink(missing_ok=True)
                    total_size -= file_size
                    removed_count += 1
                
                self.logger.info(f"🧹 Limpeza de cache: {removed_count} imagens removidas")
                
        except Exception as e:
            self.logger.error(f"❌ Erro na limpeza do cache: {e}")

class InMemoryCache:
    """Cache em memória com LRU eviction"""
    
    def __init__(self, config: CacheConfig):
        self.config = config
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self.logger = logging.getLogger("cache.memory")
        
        # Estatísticas
        self._hits = 0
        self._misses = 0
        self._evictions = 0
    
    def get(self, key: str) -> Optional[Any]:
        """Recupera valor do cache"""
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None
            
            entry = self._cache[key]
            
            # Verifica expiração
            if entry.is_expired():
                del self._cache[key]
                self._misses += 1
                return None
            
            # Move para o final (LRU)
            self._cache.move_to_end(key)
            entry.access()
            
            self._hits += 1
            self.logger.debug(f"🎯 Cache hit: {key}")
            return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Armazena valor no cache"""
        with self._lock:
            if ttl is None:
                ttl = self.config.default_ttl
            
            entry = CacheEntry(key, value, ttl)
            
            # Remove entrada existente se houver
            if key in self._cache:
                del self._cache[key]
            
            # Verifica limite de itens
            while len(self._cache) >= self.config.max_memory_items:
                # Remove item mais antigo (LRU)
                oldest_key, _ = self._cache.popitem(last=False)
                self._evictions += 1
                self.logger.debug(f"🗑️ Cache eviction: {oldest_key}")
            
            self._cache[key] = entry
            self.logger.debug(f"💾 Cache set: {key}")
            return True
    
    def delete(self, key: str) -> bool:
        """Remove entrada do cache"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self):
        """Limpa todo o cache"""
        with self._lock:
            self._cache.clear()
            self.logger.info("🧹 Cache em memória limpo")
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do cache"""
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'items': len(self._cache),
                'max_items': self.config.max_memory_items,
                'hits': self._hits,
                'misses': self._misses,
                'hit_rate': hit_rate,
                'evictions': self._evictions,
                'memory_usage_mb': sum(entry.size_bytes for entry in self._cache.values()) / 1024 / 1024
            }

class DiskCache:
    """Cache persistente em disco usando SQLite"""
    
    def __init__(self, cache_dir: Path, config: CacheConfig):
        self.cache_dir = cache_dir
        self.config = config
        self.db_path = cache_dir / "cache.db"
        self.cache_dir.mkdir(exist_ok=True, parents=True)
        
        self.logger = logging.getLogger("cache.disk")
        self._init_database()
        
        # Thread de limpeza
        self._cleanup_thread = threading.Thread(target=self._periodic_cleanup, daemon=True)
        self._cleanup_thread.start()
    
    def _init_database(self):
        """Inicializa banco de dados SQLite"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS cache_entries (
                        key TEXT PRIMARY KEY,
                        value BLOB,
                        created_at REAL,
                        expires_at REAL,
                        access_count INTEGER DEFAULT 1,
                        last_accessed REAL,
                        size_bytes INTEGER
                    )
                """)
                
                # Índices para performance
                conn.execute("CREATE INDEX IF NOT EXISTS idx_expires_at ON cache_entries(expires_at)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_last_accessed ON cache_entries(last_accessed)")
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"❌ Erro ao inicializar banco: {e}")
    
    def get(self, key: str) -> Optional[Any]:
        """Recupera valor do cache em disco"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT value, expires_at FROM cache_entries WHERE key = ?",
                    (key,)
                )
                row = cursor.fetchone()
                
                if not row:
                    return None
                
                value_blob, expires_at = row
                
                # Verifica expiração
                if time.time() > expires_at:
                    conn.execute("DELETE FROM cache_entries WHERE key = ?", (key,))
                    conn.commit()
                    return None
                
                # Atualiza acesso
                conn.execute(
                    "UPDATE cache_entries SET access_count = access_count + 1, last_accessed = ? WHERE key = ?",
                    (time.time(), key)
                )
                conn.commit()
                
                # Descomprime se necessário
                if self.config.enable_compression:
                    value = pickle.loads(zlib.decompress(value_blob))
                else:
                    value = pickle.loads(value_blob)
                
                self.logger.debug(f"🎯 Disk cache hit: {key}")
                return value
                
        except Exception as e:
            self.logger.error(f"❌ Erro ao recuperar do cache em disco: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Armazena valor no cache em disco"""
        try:
            if ttl is None:
                ttl = self.config.default_ttl
            
            current_time = time.time()
            expires_at = current_time + ttl
            
            # Serializa e comprime
            value_blob = pickle.dumps(value)
            if self.config.enable_compression:
                value_blob = zlib.compress(value_blob)
            
            size_bytes = len(value_blob)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """INSERT OR REPLACE INTO cache_entries 
                       (key, value, created_at, expires_at, access_count, last_accessed, size_bytes)
                       VALUES (?, ?, ?, ?, 1, ?, ?)""",
                    (key, value_blob, current_time, expires_at, current_time, size_bytes)
                )
                conn.commit()
            
            self.logger.debug(f"💾 Disk cache set: {key}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao armazenar no cache em disco: {e}")
            return False
    
    def _periodic_cleanup(self):
        """Thread de limpeza periódica"""
        while True:
            try:
                time.sleep(self.config.cleanup_interval)
                self._cleanup()
            except Exception as e:
                self.logger.error(f"❌ Erro na limpeza periódica: {e}")
    
    def _cleanup(self):
        """Remove entradas expiradas e controla tamanho"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                current_time = time.time()
                
                # Remove expiradas
                cursor = conn.execute("DELETE FROM cache_entries WHERE expires_at < ?", (current_time,))
                expired_count = cursor.rowcount
                
                # Verifica tamanho total
                cursor = conn.execute("SELECT SUM(size_bytes) FROM cache_entries")
                total_size = cursor.fetchone()[0] or 0
                max_size_bytes = self.config.max_disk_size_mb * 1024 * 1024
                
                if total_size > max_size_bytes:
                    # Remove mais antigos até ficar em 80% do limite
                    target_size = max_size_bytes * 0.8
                    cursor = conn.execute(
                        "SELECT key, size_bytes FROM cache_entries ORDER BY last_accessed ASC"
                    )
                    
                    removed_count = 0
                    for key, size_bytes in cursor:
                        if total_size <= target_size:
                            break
                        
                        conn.execute("DELETE FROM cache_entries WHERE key = ?", (key,))
                        total_size -= size_bytes
                        removed_count += 1
                    
                    if removed_count > 0:
                        self.logger.info(f"🧹 Limpeza de disco: {removed_count} itens removidos por tamanho")
                
                conn.commit()
                
                if expired_count > 0:
                    self.logger.info(f"🧹 Limpeza de disco: {expired_count} itens expirados removidos")
                
        except Exception as e:
            self.logger.error(f"❌ Erro na limpeza do cache em disco: {e}")

class CacheManager:
    """Gerenciador principal do sistema de cache multi-nível"""
    
    def __init__(self, cache_dir: Path, config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig()
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(exist_ok=True, parents=True)
        
        # Caches especializados
        self.memory_cache = InMemoryCache(self.config)
        self.disk_cache = DiskCache(cache_dir, self.config) if self.config.enable_persistence else None
        self.image_cache = ImageCache(cache_dir)
        
        self.logger = logging.getLogger("cache_manager")
        self.logger.info("🚀 Cache Manager inicializado")
    
    def get(self, key: str, category: str = "default") -> Optional[Any]:
        """Recupera valor do cache (memory -> disk)"""
        # Tenta memória primeiro
        value = self.memory_cache.get(key)
        if value is not None:
            return value
        
        # Tenta disco se disponível
        if self.disk_cache:
            value = self.disk_cache.get(key)
            if value is not None:
                # Promove para memória
                self.memory_cache.set(key, value)
                return value
        
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None, 
            category: str = "default", persist: bool = True) -> bool:
        """Armazena valor no cache"""
        # Sempre na memória
        success_memory = self.memory_cache.set(key, value, ttl)
        
        # No disco se habilitado e solicitado
        success_disk = True
        if persist and self.disk_cache:
            success_disk = self.disk_cache.set(key, value, ttl)
        
        return success_memory and success_disk
    
    def cache_image_result(self, image_data: bytes, processed_text: str, 
                          metadata: Optional[Dict] = None) -> str:
        """Cache específico para resultados de processamento de imagem"""
        return self.image_cache.store(image_data, processed_text, metadata)
    
    def get_cached_image_result(self, image_data: bytes) -> Optional[Tuple[str, Dict]]:
        """Recupera resultado cached de processamento de imagem"""
        return self.image_cache.get(image_data)
    
    def clear_all(self):
        """Limpa todos os caches"""
        self.memory_cache.clear()
        # Note: não limpa disk cache para preservar dados entre execuções
        self.logger.info("🧹 Caches em memória limpos")
    
    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas completas do sistema de cache"""
        stats = {
            'memory': self.memory_cache.get_stats(),
            'config': {
                'max_memory_items': self.config.max_memory_items,
                'max_disk_size_mb': self.config.max_disk_size_mb,
                'default_ttl': self.config.default_ttl,
                'compression_enabled': self.config.enable_compression,
                'persistence_enabled': self.config.enable_persistence
            }
        }
        
        if self.disk_cache:
            try:
                with sqlite3.connect(self.disk_cache.db_path) as conn:
                    cursor = conn.execute("SELECT COUNT(*), SUM(size_bytes) FROM cache_entries")
                    count, total_size = cursor.fetchone()
                    
                    stats['disk'] = {
                        'items': count or 0,
                        'size_mb': (total_size or 0) / 1024 / 1024,
                        'max_size_mb': self.config.max_disk_size_mb
                    }
            except Exception as e:
                stats['disk'] = {'error': str(e)}
        
        return stats