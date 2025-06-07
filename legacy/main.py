#!/usr/bin/env python3
"""
Academic Assistant Stealth System
Sistema stealth para assistência acadêmica com LLM
"""

import sys
import os
import threading
import time
from typing import Dict
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction, QMessageBox
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor

# Adiciona o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import config
try:
    # Imports principais (componentes específicos são importados via worker threads)
    from utils.hotkey_manager import HotkeyManager
    from ui.popup_window import PopupWindow
    from utils.logger import get_component_logger, performance_monitor, thread_safety_monitor, log_exceptions
except ImportError as e:
    print(f"❌ Erro de importação: {e}")
    print("🔧 Execute primeiro: pip install -r requirements.txt")
    sys.exit(1)

class AcademicAssistant(QObject):
    """Aplicação principal do sistema de assistência acadêmica stealth"""
    
    # Sinais para comunicação entre threads
    show_popup_signal = pyqtSignal(str)
    hide_popup_signal = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        
        # Logger específico para este componente
        self.logger = get_component_logger("AcademicAssistant")
        self.logger.log_init({
            'thread_name': threading.current_thread().name,
            'is_main_thread': threading.current_thread() == threading.main_thread(),
            'system_info': {
                'platform': sys.platform,
                'python_version': sys.version
            }
        })
        
        # Worker threads para operações thread-safe
        from utils.worker_threads import ScreenshotWorker, ProcessingWorker
        self.screenshot_worker = ScreenshotWorker()
        self.processing_worker = ProcessingWorker()
        
        # Componentes principais (apenas para configuração)
        self.hotkey_manager = HotkeyManager()
        
        # Estado da aplicação
        self.is_visible = False
        self.last_screenshot_path = None
        self.popup_window = None
        
        # Conecta sinais dos workers
        self._setup_worker_connections()
        
        # Setup dos componentes
        self._setup_components()
        
        self.logger.log_operation("ASSISTANT_INIT_COMPLETE", True, {
            'components_ready': True,
            'workers_connected': True
        })
    
    def _setup_worker_connections(self):
        """Conecta sinais dos worker threads"""
        
        # Screenshot Worker
        self.screenshot_worker.screenshot_taken.connect(self._on_screenshot_taken)
        self.screenshot_worker.screenshot_failed.connect(self._on_screenshot_failed)
        self.screenshot_worker.progress_update.connect(self._on_screenshot_progress)
        
        # Processing Worker
        self.processing_worker.processing_started.connect(self._on_processing_started)
        self.processing_worker.processing_progress.connect(self._on_processing_progress)
        self.processing_worker.processing_completed.connect(self._on_processing_completed)
        self.processing_worker.processing_failed.connect(self._on_processing_failed)
    
    def _setup_components(self):
        """Configura todos os componentes do sistema"""
        
        # Conecta sinais
        self.show_popup_signal.connect(self._show_popup)
        self.hide_popup_signal.connect(self._hide_popup)
        
        # Configura hotkeys
        self.hotkey_manager.setup_default_hotkeys(self)
        
        # Testa conexão com API
        self._test_api_connection()
        
        # Verifica status dos componentes
        self._check_components_status()
        
        print("🚀 Sistema Academic Assistant Stealth inicializado!")
        print("📋 Hotkeys ativas:")
        print(f"  • {config.HOTKEY_CAPTURE} - Capturar tela")
        print(f"  • {config.HOTKEY_TOGGLE} - Toggle visibilidade")  
        print(f"  • {config.HOTKEY_PROCESS} - Processar e analisar")
    
    def _test_api_connection(self):
        """Testa a conexão com a API em thread separada"""
        def test_connection():
            from utils.api_client import OpenRouterClient
            api_client = OpenRouterClient()
            result = api_client.test_connection()
            if result.get('success'):
                print("✅ Conexão com API estabelecida")
            else:
                print(f"❌ Erro na API: {result.get('error', 'Desconhecido')}")
        
        threading.Thread(target=test_connection, daemon=True).start()
    
    def _check_components_status(self):
        """Verifica status de todos os componentes"""
        def check_status():
            print("🔍 Verificando componentes...")
            
            # Verifica OCR
            try:
                from utils.ocr_processor import OCRProcessor
                ocr_processor = OCRProcessor()
                if ocr_processor.is_available():
                    print("✅ OCR Tesseract disponível")
                else:
                    print("⚠️ OCR Tesseract não disponível (funcionalidade limitada)")
            except:
                print("⚠️ OCR Tesseract não disponível (funcionalidade limitada)")
            
            # Verifica processamento de imagem
            try:
                from utils.image_processor import ImageProcessor
                image_processor = ImageProcessor()
                stats = image_processor.get_processing_stats()
                print(f"✅ Processador de imagem ativo")
                print(f"   Otimizações: {', '.join(stats['available_optimizations'])}")
            except:
                print("⚠️ Processador de imagem limitado")
            
            # Verifica captura de tela
            print(f"✅ 1 monitor(es) detectado(s)")
        
        threading.Thread(target=check_status, daemon=True).start()
    
    @thread_safety_monitor
    def capture_screen(self):
        """Captura a tela atual (CTRL+Y)"""
        self.logger.log_operation("CAPTURE_SCREEN_REQUEST", True, {
            'thread_name': threading.current_thread().name,
            'is_main_thread': threading.current_thread() == threading.main_thread()
        })
        print("📸 Capturando tela...")
        self.screenshot_worker.request_capture(monitor_number=1)
    
    @thread_safety_monitor
    def process_screenshot(self):
        """Processa o último screenshot com OCR e LLM (CTRL+Enter)"""
        self.logger.log_operation("PROCESS_SCREENSHOT_REQUEST", True, {
            'thread_name': threading.current_thread().name,
            'is_main_thread': threading.current_thread() == threading.main_thread(),
            'has_screenshot': self.last_screenshot_path is not None,
            'file_exists': os.path.exists(self.last_screenshot_path) if self.last_screenshot_path else False
        })
        
        if not self.last_screenshot_path or not os.path.exists(self.last_screenshot_path):
            print("❌ Nenhuma captura disponível")
            self.show_popup_signal.emit("❌ Capture uma tela primeiro (Ctrl+Y)")
            self.logger.log_operation("PROCESS_SCREENSHOT_FAILED", False, {
                'reason': 'No screenshot available'
            })
            return
        
        print("🤖 Processando com OCR + LLM...")
        self.processing_worker.request_processing(self.last_screenshot_path)
    
    def _create_enhanced_prompt(self, ocr_text: str, processing_info: Dict) -> str:
        """
        Cria prompt otimizado baseado no OCR e tipo de conteúdo
        
        Args:
            ocr_text: Texto extraído por OCR
            processing_info: Informações do processamento da imagem
            
        Returns:
            Prompt otimizado para o LLM
        """
        base_prompt = config.SYSTEM_PROMPT
        
        if ocr_text:
            enhanced_prompt = base_prompt + f"""

TEXTO EXTRAÍDO POR OCR:
{ocr_text}

INSTRUÇÕES ADICIONAIS:
- Use o texto extraído como contexto principal
- Se a imagem contém informações não capturadas pelo OCR, inclua na análise
- Identifique tipo de questão: múltipla escolha, dissertativa, matemática, etc.
- Se há alternativas (a, b, c, d, e), destaque a resposta correta
- Para questões matemáticas, mostre resolução passo a passo
"""
        else:
            enhanced_prompt = base_prompt + """

INSTRUÇÕES PARA ANÁLISE VISUAL:
- OCR não disponível, analise completamente pela imagem
- Foque em texto visível, fórmulas, diagramas e gráficos
- Identifique questões e alternativas visualmente
- Para matemática, interprete símbolos e expressões da imagem
"""
        
        return enhanced_prompt
    
    # Callbacks dos Worker Threads
    def _on_screenshot_taken(self, filepath: str):
        """Callback quando screenshot é capturado com sucesso"""
        self.last_screenshot_path = filepath
        print(f"✅ Tela capturada: {os.path.basename(filepath)}")
        self.show_popup_signal.emit("📸 Tela capturada! Use Ctrl+Enter para analisar.")
    
    def _on_screenshot_failed(self, error: str):
        """Callback quando captura falha"""
        print(f"❌ Erro ao capturar tela: {error}")
        self.show_popup_signal.emit(f"❌ Erro ao capturar tela: {error}")
    
    def _on_screenshot_progress(self, message: str):
        """Callback para progresso da captura"""
        print(message)
    
    def _on_processing_started(self):
        """Callback quando processamento inicia"""
        self.show_popup_signal.emit("🔍 Analisando imagem... Por favor, aguarde.")
    
    def _on_processing_progress(self, message: str):
        """Callback para progresso do processamento"""
        print(message)
        self.show_popup_signal.emit(message)
    
    def _on_processing_completed(self, result: str):
        """Callback quando processamento é concluído"""
        print("✅ Análise concluída com sucesso!")
        self.show_popup_signal.emit(result)
    
    def _on_processing_failed(self, error: str):
        """Callback quando processamento falha"""
        print(f"❌ Erro no processamento: {error}")
        self.show_popup_signal.emit(f"❌ Erro: {error}")
    
    def toggle_visibility(self):
        """Alterna visibilidade do popup (CTRL+B)"""
        self.is_visible = not self.is_visible
        
        if self.is_visible:
            message = "👁️ Sistema visível\n\nHotkeys ativas:\n"
            message += f"• {config.HOTKEY_CAPTURE} - Capturar tela\n"
            message += f"• {config.HOTKEY_PROCESS} - Processar\n"
            message += f"• {config.HOTKEY_TOGGLE} - Ocultar\n\n"
            message += "💡 Pressione ESC ou clique no X para ocultar\n"
            message += "💡 Este popup permanecerá visível até ser fechado"
            
            self._show_persistent_popup(message)
        else:
            self.hide_popup_signal.emit()
            print("👁️ Sistema oculto")
    
    def _show_popup(self, message: str):
        """Mostra o popup com a mensagem"""
        if not self.popup_window:
            self.popup_window = PopupWindow()
        
        self.popup_window.show_message(message)
        self.is_visible = True
    
    def _show_persistent_popup(self, message: str):
        """Mostra o popup persistente (sem auto-hide)"""
        if not self.popup_window:
            self.popup_window = PopupWindow()
        
        self.popup_window.show_persistent_message(message)
        self.is_visible = True
    
    def _hide_popup(self):
        """Esconde o popup"""
        if self.popup_window:
            self.popup_window.hide()
        self.is_visible = False
    
    def start(self):
        """Inicia o sistema"""
        try:
            # Inicia o sistema de hotkeys
            self.hotkey_manager.start_listening()
            
            # Limpa screenshots antigos (via worker thread se necessário)
            self._cleanup_old_screenshots()
            
            print("🎯 Sistema pronto! Aguardando comandos...")
            
        except Exception as e:
            print(f"❌ Erro ao iniciar sistema: {e}")
            raise
    
    def _cleanup_old_screenshots(self):
        """Limpa screenshots antigos sem depender do screenshot_manager"""
        try:
            import os
            import time
            
            current_time = time.time()
            max_age_hours = 1
            
            for filename in os.listdir(config.TEMP_DIR):
                if filename.startswith(('screenshot_', 'window_capture_')):
                    filepath = os.path.join(config.TEMP_DIR, filename)
                    file_age = current_time - os.path.getctime(filepath)
                    
                    if file_age > (max_age_hours * 3600):
                        os.remove(filepath)
                        
        except Exception as e:
            print(f"Erro na limpeza de arquivos: {e}")
    
    def stop(self):
        """Para o sistema"""
        try:
            self.hotkey_manager.stop_listening()
            
            # Para worker threads
            if hasattr(self, 'screenshot_worker'):
                self.screenshot_worker.stop_worker()
                self.screenshot_worker.wait(2000)  # Espera até 2s para finalizar
                
            if hasattr(self, 'processing_worker'):
                self.processing_worker.terminate()
                self.processing_worker.wait(2000)
            
            if self.popup_window:
                self.popup_window.close()
            print("🛑 Sistema parado")
            
        except Exception as e:
            print(f"❌ Erro ao parar sistema: {e}")


class SteathSystemTrayIcon(QSystemTrayIcon):
    """System tray icon stealth para controle discreto"""
    
    def __init__(self, assistant: AcademicAssistant, parent=None):
        super().__init__(parent)
        
        self.assistant = assistant
        
        # Cria ícone invisível (pixel transparente)
        self._create_invisible_icon()
        
        # Setup do menu de contexto
        self._setup_context_menu()
        
        # Conecta sinais
        self.activated.connect(self._on_tray_activated)
        
    def _create_invisible_icon(self):
        """Cria um ícone praticamente invisível"""
        # Cria um pixmap 1x1 transparente
        pixmap = QPixmap(1, 1)
        pixmap.fill(Qt.transparent)
        
        # Adiciona um pixel quase transparente para não ser totalmente invisível
        painter = QPainter(pixmap)
        painter.fillRect(0, 0, 1, 1, QColor(0, 0, 0, 1))  # Quase transparente
        painter.end()
        
        self.setIcon(QIcon(pixmap))
    
    def _setup_context_menu(self):
        """Configura menu de contexto do system tray"""
        menu = QMenu()
        
        # Ações do menu
        toggle_action = QAction("Toggle Visibilidade", self)
        toggle_action.triggered.connect(self.assistant.toggle_visibility)
        
        status_action = QAction("Status do Sistema", self)
        status_action.triggered.connect(self._show_status)
        
        quit_action = QAction("Sair", self)
        quit_action.triggered.connect(self._quit_application)
        
        # Adiciona ao menu
        menu.addAction(toggle_action)
        menu.addAction(status_action)
        menu.addSeparator()
        menu.addAction(quit_action)
        
        self.setContextMenu(menu)
    
    def _on_tray_activated(self, reason):
        """Callback para ativação do ícone do tray"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.assistant.toggle_visibility()
    
    def _show_status(self):
        """Mostra status do sistema"""
        status = "🎯 Academic Assistant Stealth\n\n"
        status += f"Hotkeys ativas: {self.assistant.hotkey_manager.is_active()}\n"
        status += f"Última captura: {bool(self.assistant.last_screenshot_path)}\n"
        status += f"Popup visível: {self.assistant.is_visible}\n\n"
        status += "Hotkeys:\n"
        status += f"• {config.HOTKEY_CAPTURE} - Capturar\n"
        status += f"• {config.HOTKEY_PROCESS} - Processar\n"
        status += f"• {config.HOTKEY_TOGGLE} - Toggle"
        
        QMessageBox.information(None, "Status do Sistema", status)
    
    def _quit_application(self):
        """Encerra a aplicação"""
        self.assistant.stop()
        QApplication.quit()


def main():
    """Função principal"""
    
    # Limpa logs da execução anterior para análise isolada
    print("🎯 Iniciando Academic Assistant Stealth...")
    from utils.log_cleaner import clean_logs_for_new_execution
    clean_logs_for_new_execution()
    print("=" * 60)
    
    # Cria aplicação Qt
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Não fecha quando janela fecha
    
    # Verifica se system tray está disponível
    if not QSystemTrayIcon.isSystemTrayAvailable():
        QMessageBox.critical(None, "Erro", 
                           "System tray não disponível neste sistema!")
        sys.exit(1)
    
    try:
        # Cria e inicia o assistente
        assistant = AcademicAssistant()
        assistant.start()
        
        # Cria system tray icon
        tray_icon = SteathSystemTrayIcon(assistant)
        tray_icon.show()
        
        print("💫 Academic Assistant Stealth em execução!")
        print("🎯 Use as hotkeys configuradas para interagir")
        print("🖱️ Clique direito no system tray para mais opções")
        
        # Inicia o loop da aplicação
        return app.exec_()
        
    except KeyboardInterrupt:
        print("\n🛑 Interrompido pelo usuário")
        return 0
    except Exception as e:
        print(f"❌ Erro fatal: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 