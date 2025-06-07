import os
import sys
from dataclasses import dataclass, field
from typing import Tuple, Optional, Dict, Any
from pathlib import Path
import logging
from cryptography.fernet import Fernet
import base64

@dataclass
class SecurityConfig:
    """Configurações de segurança do sistema"""
    enable_encryption: bool = True
    session_timeout: int = 3600  # 1 hora
    max_api_requests_per_minute: int = 60
    enable_audit_logging: bool = True
    auto_cleanup_temp_files: bool = True
    secure_temp_directory: bool = True

@dataclass
class UIConfig:
    """Configurações de interface do usuário"""
    popup_width: int = 400
    popup_height: int = 300
    popup_opacity: float = 0.95
    auto_hide_delay: int = 10000  # 10 seconds
    theme: str = "dark"
    window_flags_stealth: bool = True
    hide_from_taskbar: bool = True
    no_window_shadow: bool = True

@dataclass
class ProcessingConfig:
    """Configurações de processamento"""
    ocr_language: str = "por+eng"  # Portuguese + English
    max_text_length: int = 4000
    screenshot_quality: int = 85
    max_image_size: Tuple[int, int] = (1920, 1080)
    enable_gpu_acceleration: bool = False
    batch_processing_size: int = 1

@dataclass
class HotkeyConfig:
    """Configurações de hotkeys"""
    capture: str = "ctrl+y"
    toggle: str = "ctrl+b"
    process: str = "ctrl+enter"
    emergency_stop: str = "ctrl+shift+esc"

@dataclass
class Config:
    """Configuração centralizada e segura do Academic Assistant Stealth"""
    
    # Configurações de API (carregadas de variáveis de ambiente)
    _openrouter_api_key: Optional[str] = field(default=None, init=False)
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    model_name: str = "anthropic/claude-3.5-sonnet"
    
    # Sub-configurações
    security: SecurityConfig = field(default_factory=SecurityConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)
    hotkeys: HotkeyConfig = field(default_factory=HotkeyConfig)
    
    # Diretórios
    temp_dir: Path = field(default_factory=lambda: Path.cwd() / "temp")
    logs_dir: Path = field(default_factory=lambda: Path.cwd() / "logs")
    config_dir: Path = field(default_factory=lambda: Path.cwd() / "config")
    
    # Prompt do sistema
    system_prompt: str = """Você é um assistente acadêmico especializado em resolver questões universitárias. 
    Analise a imagem fornecida e:
    1. Identifique se há uma questão, problema ou exercício
    2. Resolva passo a passo de forma clara e didática
    3. Forneça a resposta final destacada
    4. Se for múltipla escolha, indique a alternativa correta
    5. Mantenha a resposta concisa mas completa
    
    Foque em: Matemática, Física, Química, Programação, Estatística e disciplinas exatas.
    Formato: Resposta direta e objetiva, ideal para contexto acadêmico."""

    def __post_init__(self):
        """Inicialização pós-criação do objeto"""
        self._load_environment_variables()
        self._create_directories()
        self._validate_configuration()
        self._setup_encryption()

    def _load_environment_variables(self):
        """Carrega configurações de variáveis de ambiente"""
        # API Key de variável de ambiente ou arquivo .env
        self._openrouter_api_key = os.getenv('OPENROUTER_API_KEY')
        
        # Se não encontrar na env, tenta carregar do arquivo .env
        if not self._openrouter_api_key:
            env_file = Path('.env')
            if env_file.exists():
                try:
                    from dotenv import load_dotenv
                    load_dotenv()
                    self._openrouter_api_key = os.getenv('OPENROUTER_API_KEY')
                except ImportError:
                    logging.warning("python-dotenv não está instalado. Instale com: pip install python-dotenv")

        # Configurações opcionais de variáveis de ambiente
        self.model_name = os.getenv('MODEL_NAME', self.model_name)
        self.hotkeys.capture = os.getenv('HOTKEY_CAPTURE', self.hotkeys.capture)
        self.hotkeys.toggle = os.getenv('HOTKEY_TOGGLE', self.hotkeys.toggle)
        self.hotkeys.process = os.getenv('HOTKEY_PROCESS', self.hotkeys.process)

    def _create_directories(self):
        """Cria diretórios necessários com permissões adequadas"""
        for directory in [self.temp_dir, self.logs_dir, self.config_dir]:
            directory.mkdir(exist_ok=True, parents=True)
            
            # Define permissões restritivas em sistemas Unix
            if sys.platform != 'win32':
                os.chmod(directory, 0o700)

    def _validate_configuration(self):
        """Valida configurações críticas"""
        if not self._openrouter_api_key:
            logging.error("❌ OPENROUTER_API_KEY não configurada!")
            logging.error("💡 Configure através de:")
            logging.error("   1. Variável de ambiente: export OPENROUTER_API_KEY='sua-chave'")
            logging.error("   2. Arquivo .env: OPENROUTER_API_KEY=sua-chave")
            raise ValueError("API Key não configurada. Veja instruções acima.")

        if len(self._openrouter_api_key) < 10:
            raise ValueError("API Key inválida - muito curta")

        # Validações de segurança
        if self.security.session_timeout < 300:  # Mínimo 5 minutos
            logging.warning("⚠️ Session timeout muito baixo, ajustando para 5 minutos")
            self.security.session_timeout = 300

        if self.security.max_api_requests_per_minute > 100:
            logging.warning("⚠️ Rate limit muito alto, ajustando para 100/min")
            self.security.max_api_requests_per_minute = 100

    def _setup_encryption(self):
        """Configura sistema de criptografia para dados sensíveis"""
        if self.security.enable_encryption:
            key_file = self.config_dir / 'encryption.key'
            
            if not key_file.exists():
                # Gera nova chave de criptografia
                key = Fernet.generate_key()
                key_file.write_bytes(key)
                
                # Permissões restritivas no arquivo de chave
                if sys.platform != 'win32':
                    os.chmod(key_file, 0o600)
                    
                logging.info("🔐 Nova chave de criptografia gerada")
            
            self._encryption_key = key_file.read_bytes()

    @property
    def openrouter_api_key(self) -> str:
        """Propriedade segura para acessar API key"""
        if not self._openrouter_api_key:
            raise ValueError("API Key não configurada")
        return self._openrouter_api_key

    @property
    def encryption_key(self) -> bytes:
        """Propriedade para acessar chave de criptografia"""
        if not hasattr(self, '_encryption_key'):
            raise ValueError("Sistema de criptografia não inicializado")
        return self._encryption_key

    def encrypt_data(self, data: str) -> str:
        """Criptografa dados sensíveis"""
        if not self.security.enable_encryption:
            return data
        
        f = Fernet(self.encryption_key)
        encrypted_data = f.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted_data).decode()

    def decrypt_data(self, encrypted_data: str) -> str:
        """Descriptografa dados sensíveis"""
        if not self.security.enable_encryption:
            return encrypted_data
        
        f = Fernet(self.encryption_key)
        decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
        decrypted_data = f.decrypt(decoded_data)
        return decrypted_data.decode()

    def get_safe_config_dict(self) -> Dict[str, Any]:
        """Retorna dicionário de configuração sem dados sensíveis"""
        return {
            'model_name': self.model_name,
            'openrouter_base_url': self.openrouter_base_url,
            'api_key_configured': bool(self._openrouter_api_key),
            'security': {
                'encryption_enabled': self.security.enable_encryption,
                'session_timeout': self.security.session_timeout,
                'max_api_requests_per_minute': self.security.max_api_requests_per_minute,
                'audit_logging': self.security.enable_audit_logging
            },
            'ui': {
                'theme': self.ui.theme,
                'stealth_mode': self.ui.window_flags_stealth
            },
            'hotkeys': {
                'capture': self.hotkeys.capture,
                'toggle': self.hotkeys.toggle,
                'process': self.hotkeys.process
            }
        }

    def save_config(self, config_file: Optional[str] = None):
        """Salva configuração segura em arquivo"""
        if not config_file:
            config_file = self.config_dir / 'settings.json'
        
        import json
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(self.get_safe_config_dict(), f, indent=2, ensure_ascii=False)
        
        logging.info(f"✅ Configuração salva em: {config_file}")

# Instância singleton da configuração
config = Config()

# Compatibilidade com código existente (DEPRECATED - será removido)
def get_legacy_config():
    """Função de compatibilidade - DEPRECATED"""
    import warnings
    warnings.warn(
        "Acesso direto às configurações está deprecated. Use config.* em vez disso.",
        DeprecationWarning,
        stacklevel=2
    )
    return {
        'OPENROUTER_API_KEY': config.openrouter_api_key,
        'OPENROUTER_BASE_URL': config.openrouter_base_url,
        'MODEL_NAME': config.model_name,
        'HOTKEY_CAPTURE': config.hotkeys.capture,
        'HOTKEY_TOGGLE': config.hotkeys.toggle,
        'HOTKEY_PROCESS': config.hotkeys.process,
        'SCREENSHOT_QUALITY': config.processing.screenshot_quality,
        'MAX_IMAGE_SIZE': config.processing.max_image_size,
        'TEMP_DIR': str(config.temp_dir),
        'LOGS_DIR': str(config.logs_dir),
        'POPUP_WIDTH': config.ui.popup_width,
        'POPUP_HEIGHT': config.ui.popup_height,
        'POPUP_OPACITY': config.ui.popup_opacity,
        'AUTO_HIDE_DELAY': config.ui.auto_hide_delay,
        'WINDOW_FLAGS_STEALTH': config.ui.window_flags_stealth,
        'HIDE_FROM_TASKBAR': config.ui.hide_from_taskbar,
        'NO_WINDOW_SHADOW': config.ui.no_window_shadow,
        'OCR_LANGUAGE': config.processing.ocr_language,
        'MAX_TEXT_LENGTH': config.processing.max_text_length,
        'SYSTEM_PROMPT': config.system_prompt
    }

# Mantém variáveis para compatibilidade (DEPRECATED)
OPENROUTER_API_KEY = property(lambda: config.openrouter_api_key)
OPENROUTER_BASE_URL = config.openrouter_base_url
MODEL_NAME = config.model_name
HOTKEY_CAPTURE = config.hotkeys.capture
HOTKEY_TOGGLE = config.hotkeys.toggle  
HOTKEY_PROCESS = config.hotkeys.process
SCREENSHOT_QUALITY = config.processing.screenshot_quality
MAX_IMAGE_SIZE = config.processing.max_image_size
TEMP_DIR = str(config.temp_dir)
LOGS_DIR = str(config.logs_dir)
POPUP_WIDTH = config.ui.popup_width
POPUP_HEIGHT = config.ui.popup_height
POPUP_OPACITY = config.ui.popup_opacity
AUTO_HIDE_DELAY = config.ui.auto_hide_delay
WINDOW_FLAGS_STEALTH = config.ui.window_flags_stealth
HIDE_FROM_TASKBAR = config.ui.hide_from_taskbar
NO_WINDOW_SHADOW = config.ui.no_window_shadow
OCR_LANGUAGE = config.processing.ocr_language
MAX_TEXT_LENGTH = config.processing.max_text_length
SYSTEM_PROMPT = config.system_prompt