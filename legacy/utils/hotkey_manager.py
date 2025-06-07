import keyboard
import threading
import time
from typing import Callable, Dict, Any
from config import config

class HotkeyManager:
    """Gerenciador de hotkeys globais usando biblioteca keyboard (mais confiável)"""
    
    def __init__(self):
        self.callbacks = {}
        self.active = False
        
    def register_hotkey(self, hotkey: str, callback: Callable, *args, **kwargs):
        """
        Registra uma hotkey global usando biblioteca keyboard
        
        Args:
            hotkey: String da hotkey (ex: "ctrl+y")
            callback: Função a ser chamada
            *args, **kwargs: Argumentos para a função callback
        """
        try:
            # Wrapper para incluir argumentos se fornecidos
            if args or kwargs:
                def wrapped_callback():
                    callback(*args, **kwargs)
                keyboard.add_hotkey(hotkey, wrapped_callback)
            else:
                keyboard.add_hotkey(hotkey, callback)
                
            self.callbacks[hotkey] = callback
            print(f"✅ Hotkey registrada: {hotkey}")
            return True
        except Exception as e:
            print(f"❌ Erro ao registrar hotkey {hotkey}: {e}")
            return False
    
    def start_listening(self):
        """Inicia o listener de hotkeys"""
        if self.active:
            print("🎯 Sistema de hotkeys ativo!")
            # A biblioteca keyboard já gerencia as hotkeys automaticamente
        else:
            print("❌ Nenhuma hotkey ativa")
    
    def stop_listening(self):
        """Para o listener de hotkeys"""
        try:
            keyboard.clear_all_hotkeys()
            self.active = False
            print("🛑 Sistema de hotkeys parado")
        except Exception as e:
            print(f"Erro ao parar hotkeys: {e}")
    
    def setup_default_hotkeys(self, app_instance):
        """
        Configura as hotkeys padrão do sistema
        
        Args:
            app_instance: Instância da aplicação principal
        """
        print("🔧 Configurando hotkeys...")
        
        # Registra as hotkeys
        success_count = 0
        
        if self.register_hotkey(config.HOTKEY_CAPTURE, app_instance.capture_screen):
            success_count += 1
            
        if self.register_hotkey(config.HOTKEY_TOGGLE, app_instance.toggle_visibility):
            success_count += 1
            
        if self.register_hotkey(config.HOTKEY_PROCESS, app_instance.process_screenshot):
            success_count += 1
        
        print(f"✅ {success_count}/3 hotkeys configuradas")
        print(f"   • {config.HOTKEY_CAPTURE} - Capturar tela")
        print(f"   • {config.HOTKEY_TOGGLE} - Toggle visibilidade")
        print(f"   • {config.HOTKEY_PROCESS} - Processar e analisar")
        
        self.active = True
    
    def is_active(self) -> bool:
        """Retorna se o sistema de hotkeys está ativo"""
        return self.active
    
    def get_registered_hotkeys(self) -> Dict[str, Any]:
        """Retorna dicionário com todas as hotkeys registradas"""
        return {name: data['keys'] for name, data in self.callbacks.items()} 