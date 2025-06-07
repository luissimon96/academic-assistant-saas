#!/usr/bin/env python3
"""
Script de instalação automática para Academic Assistant Stealth
"""

import os
import sys
import subprocess
import platform
import urllib.request
import zipfile
import shutil
from pathlib import Path

def print_header():
    """Imprime cabeçalho do instalador"""
    print("=" * 60)
    print("🎯 ACADEMIC ASSISTANT STEALTH - INSTALADOR")
    print("=" * 60)
    print("Sistema stealth para assistência acadêmica com LLM")
    print("⚠️  APENAS PARA USO EDUCACIONAL")
    print("=" * 60)

def check_system():
    """Verifica se o sistema é compatível"""
    print("\n🔍 Verificando sistema...")
    
    system = platform.system()
    if system != "Windows":
        print(f"❌ Sistema {system} não suportado. Apenas Windows é suportado.")
        return False
    
    print(f"✅ Sistema compatível: {system} {platform.release()}")
    
    # Verifica Python
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        print(f"❌ Python {python_version.major}.{python_version.minor} muito antigo. Requer Python 3.8+")
        return False
    
    print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    return True

def install_dependencies():
    """Instala dependências Python"""
    print("\n📦 Instalando dependências...")
    
    try:
        # Atualiza pip
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], 
                      check=True, capture_output=True)
        
        # Instala dependências
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True)
        
        print("✅ Dependências instaladas com sucesso")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao instalar dependências: {e}")
        return False

def install_tesseract():
    """Instala Tesseract OCR para Windows"""
    print("\n🔤 Configurando Tesseract OCR...")
    
    tesseract_path = "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
    
    if os.path.exists(tesseract_path):
        print("✅ Tesseract já instalado")
        return True
    
    print("📥 Tesseract não encontrado. Instalação manual necessária:")
    print("1. Baixe de: https://github.com/UB-Mannheim/tesseract/wiki")
    print("2. Instale em: C:\\Program Files\\Tesseract-OCR\\")
    print("3. Execute novamente este instalador")
    
    return False

def setup_environment():
    """Configura ambiente e arquivos necessários"""
    print("\n⚙️ Configurando ambiente...")
    
    try:
        # Cria diretórios necessários
        dirs = ["temp", "logs", "data"]
        for dir_name in dirs:
            os.makedirs(dir_name, exist_ok=True)
            print(f"📁 Diretório criado: {dir_name}")
        
        # Verifica arquivo de configuração
        if not os.path.exists("config.py"):
            print("❌ Arquivo config.py não encontrado")
            return False
        
        print("✅ Ambiente configurado")
        return True
        
    except Exception as e:
        print(f"❌ Erro na configuração: {e}")
        return False

def create_startup_script():
    """Cria script de inicialização"""
    print("\n🚀 Criando script de inicialização...")
    
    startup_script = """@echo off
cd /d "%~dp0"
python main.py
pause
"""
    
    try:
        with open("start_assistant.bat", "w") as f:
            f.write(startup_script)
        
        print("✅ Script de inicialização criado: start_assistant.bat")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar script: {e}")
        return False

def test_installation():
    """Testa a instalação"""
    print("\n🧪 Testando instalação...")
    
    try:
        # Testa imports
        import PyQt5
        import PIL
        import mss
        import pynput
        print("✅ Imports básicos funcionando")
        
        # Testa componentes principais
        from config import config
        print("✅ Configuração carregada")
        
        from utils.screenshot_manager import ScreenshotManager
        from utils.hotkey_manager import HotkeyManager
        from utils.api_client import OpenRouterClient
        print("✅ Componentes principais importados")
        
        print("✅ Instalação testada com sucesso!")
        return True
        
    except ImportError as e:
        print(f"❌ Erro de importação: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False

def show_usage_instructions():
    """Mostra instruções de uso"""
    print("\n" + "=" * 60)
    print("🎯 INSTALAÇÃO CONCLUÍDA!")
    print("=" * 60)
    print("\n📋 COMO USAR:")
    print("1. Execute: python main.py")
    print("   ou clique em: start_assistant.bat")
    print("\n⌨️ HOTKEYS:")
    print("• CTRL+Y - Capturar tela")
    print("• CTRL+B - Toggle visibilidade")
    print("• CTRL+Enter - Processar com LLM")
    print("\n🔐 MODO STEALTH:")
    print("• Invisível em gravações de tela")
    print("• Não aparece em Alt+Tab")
    print("• Ícone minimizado no system tray")
    print("\n⚠️ IMPORTANTE:")
    print("• Configure sua OPENROUTER_API_KEY no config.py")
    print("• Use apenas para fins educacionais")
    print("• Respeite os termos de uso das plataformas")
    print("\n" + "=" * 60)

def main():
    """Função principal do instalador"""
    
    print_header()
    
    # Verificações do sistema
    if not check_system():
        input("\nPressione Enter para sair...")
        return 1
    
    # Instalação de dependências
    if not install_dependencies():
        input("\nPressione Enter para sair...")
        return 1
    
    # Configuração do Tesseract
    if not install_tesseract():
        print("\n⚠️ Continue a instalação após configurar o Tesseract")
    
    # Setup do ambiente
    if not setup_environment():
        input("\nPressione Enter para sair...")
        return 1
    
    # Criação de scripts
    if not create_startup_script():
        print("⚠️ Script de inicialização não criado (opcional)")
    
    # Teste da instalação
    if not test_installation():
        print("⚠️ Alguns componentes podem não funcionar corretamente")
    
    # Instruções finais
    show_usage_instructions()
    
    input("\nPressione Enter para finalizar...")
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n🛑 Instalação cancelada pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro durante a instalação: {e}")
        sys.exit(1) 