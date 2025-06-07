from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QTextEdit, QFrame, QScrollArea)
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect, QMetaObject, Q_ARG
from PyQt5.QtGui import QFont, QPalette, QColor, QIcon
import sys
import os
import threading
from queue import Queue, Empty
from config import config
from utils.logger import get_component_logger, thread_safety_monitor, log_exceptions

class PopupWindow(QWidget):
    """Janela popup stealth otimizada para invisibilidade em gravações"""
    
    def __init__(self):
        super().__init__()
        
        # Logger específico para este componente
        self.logger = get_component_logger("PopupWindow")
        self.logger.log_init({
            'thread_name': threading.current_thread().name,
            'is_main_thread': threading.current_thread() == threading.main_thread()
        })
        
        # Thread-safe message queue
        self._message_queue = Queue()
        self._queue_timer = QTimer()
        self._queue_timer.timeout.connect(self._process_message_queue)
        self._queue_timer.start(50)  # Check queue every 50ms
        
        self.auto_hide_timer = QTimer()
        self.auto_hide_timer.timeout.connect(self._safe_hide)
        self.is_persistent = False  # Flag para mensagens persistentes
        
        self._setup_stealth_window()
        self._setup_ui()
        self._setup_animations()
        
        self.logger.log_operation("POPUP_INIT_COMPLETE", True, {
            'window_flags': int(self.windowFlags()),
            'opacity': self.windowOpacity(),
            'size': f"{self.width()}x{self.height()}"
        })
        
    @log_exceptions
    def _process_message_queue(self):
        """Processa mensagens da queue de forma thread-safe"""
        messages_processed = 0
        try:
            while True:
                message_data = self._message_queue.get_nowait()
                self._display_message_safe(message_data)
                messages_processed += 1
        except Empty:
            if messages_processed > 0:
                self.logger.log_operation("MESSAGE_QUEUE_PROCESSED", True, {
                    'messages_processed': messages_processed,
                    'queue_size_after': self._message_queue.qsize()
                })
    
    @thread_safety_monitor
    def _display_message_safe(self, message_data):
        """Exibe mensagem de forma thread-safe na main thread"""
        message = message_data['message']
        auto_hide_delay = message_data.get('auto_hide_delay')
        persistent = message_data.get('persistent', False)
        
        thread_info = {
            'is_main_thread': threading.current_thread() == threading.main_thread(),
            'thread_name': threading.current_thread().name,
            'message_length': len(message),
            'persistent': persistent
        }
        
        self.logger.log_operation("DISPLAY_MESSAGE_START", True, thread_info)
        
        # Atualiza flag de persistência
        self.is_persistent = persistent
        
        # Define o conteúdo usando QMetaObject.invokeMethod para thread safety
        if threading.current_thread() == threading.main_thread():
            self.content_area.setPlainText(message)
            self.logger.log_operation("TEXT_SET_DIRECT", True, {})
        else:
            QMetaObject.invokeMethod(
                self.content_area, "setPlainText", 
                Qt.QueuedConnection,
                Q_ARG(str, message)
            )
            self.logger.log_operation("TEXT_SET_QUEUED", True, {})
        
        # Ajusta altura baseada no conteúdo
        self._adjust_height_to_content_safe()
        
        # Mostra a janela com animação
        self._show_with_animation_safe()
        
        # Configura auto-hide apenas se não for persistente
        if not persistent and (auto_hide_delay is not None or config.AUTO_HIDE_DELAY > 0):
            delay = auto_hide_delay or config.AUTO_HIDE_DELAY
            QMetaObject.invokeMethod(
                self.auto_hide_timer, "start",
                Qt.QueuedConnection,
                Q_ARG(int, delay)
            )
            self.logger.log_operation("AUTO_HIDE_SCHEDULED", True, {'delay': delay})
        
        self.logger.log_operation("DISPLAY_MESSAGE_COMPLETE", True, thread_info)
        print(f"💬 Popup exibido: {message[:50]}{'...' if len(message) > 50 else ''}")
    
    def _setup_stealth_window(self):
        """Configura a janela para máximo stealth"""
        
        # Flags para invisibilidade em gravações
        flags = (Qt.WindowStaysOnTopHint | 
                Qt.FramelessWindowHint | 
                Qt.Tool |  # Não aparece na taskbar
                Qt.WindowDoesNotAcceptFocus)  # Não rouba foco
        
        if config.HIDE_FROM_TASKBAR:
            flags |= Qt.WindowStaysOnTopHint
        
        if config.NO_WINDOW_SHADOW:
            flags |= Qt.NoDropShadowWindowHint
        
        self.setWindowFlags(flags)
        
        # Torna a janela semi-transparente
        self.setWindowOpacity(config.POPUP_OPACITY)
        
        # Remove da captura de tela de sistema (Windows)
        try:
            import win32gui
            import win32con
            hwnd = int(self.winId())
            # WS_EX_NOACTIVATE evita que apareça em Alt+Tab
            # WS_EX_TOOLWINDOW evita que apareça na taskbar
            extended_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            extended_style |= win32con.WS_EX_NOACTIVATE | win32con.WS_EX_TOOLWINDOW
            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, extended_style)
        except ImportError:
            pass  # Não é Windows ou win32gui não disponível
        
        # Posiciona no canto superior direito
        self._position_window()
        
    def _position_window(self):
        """Posiciona a janela no canto superior direito"""
        from PyQt5.QtWidgets import QDesktopWidget
        
        desktop = QDesktopWidget()
        screen_rect = desktop.availableGeometry()
        
        # Posição no canto superior direito com margem
        margin = 20
        x = screen_rect.width() - config.POPUP_WIDTH - margin
        y = margin
        
        self.setGeometry(x, y, config.POPUP_WIDTH, config.POPUP_HEIGHT)
    
    def _setup_ui(self):
        """Configura a interface do popup"""
        
        # Layout principal
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # Header com título e botão fechar
        header_layout = QHBoxLayout()
        
        title_label = QLabel("🎯 Academic Assistant")
        title_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        title_label.setStyleSheet("color: #2c3e50; margin-bottom: 5px;")
        
        close_button = QPushButton("✕")
        close_button.setFixedSize(20, 20)
        close_button.setStyleSheet("""
            QPushButton {
                background: #e74c3c;
                color: white;
                border: none;
                border-radius: 10px;
                font-weight: bold;
                font-size: 10px;
            }
            QPushButton:hover {
                background: #c0392b;
            }
        """)
        close_button.clicked.connect(self.hide)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(close_button)
        
        # Área de conteúdo com scroll
        self.content_area = QTextEdit()
        self.content_area.setReadOnly(True)
        self.content_area.setMaximumHeight(200)
        self.content_area.setFont(QFont("Consolas", 9))
        
        # Estilo para área de conteúdo
        self.content_area.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 8px;
                color: #495057;
            }
        """)
        
        # Botões de ação
        button_layout = QHBoxLayout()
        
        copy_button = QPushButton("📋 Copiar")
        copy_button.setStyleSheet(self._get_button_style("#3498db"))
        copy_button.clicked.connect(self._copy_content)
        
        hide_button = QPushButton("👁️ Ocultar")
        hide_button.setStyleSheet(self._get_button_style("#95a5a6"))
        hide_button.clicked.connect(self.hide)
        
        button_layout.addWidget(copy_button)
        button_layout.addWidget(hide_button)
        
        # Adiciona tudo ao layout
        layout.addLayout(header_layout)
        layout.addWidget(self.content_area)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Estilo geral da janela
        self.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                border-radius: 12px;
                border: 2px solid #bdc3c7;
            }
        """)
    
    def _get_button_style(self, color: str) -> str:
        """Retorna estilo CSS para botões"""
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: bold;
                font-size: 9px;
            }}
            QPushButton:hover {{
                background-color: {self._darken_color(color)};
            }}
            QPushButton:pressed {{
                background-color: {self._darken_color(color, 0.8)};
            }}
        """
    
    def _darken_color(self, hex_color: str, factor: float = 0.85) -> str:
        """Escurece uma cor hexadecimal"""
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        darkened = tuple(int(c * factor) for c in rgb)
        return f"#{darkened[0]:02x}{darkened[1]:02x}{darkened[2]:02x}"
    
    def _setup_animations(self):
        """Configura animações para entrada e saída"""
        
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(300)
        self.fade_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        # Animação de slide
        self.slide_animation = QPropertyAnimation(self, b"geometry")
        self.slide_animation.setDuration(250)
        self.slide_animation.setEasingCurve(QEasingCurve.OutQuad)
    
    def _adjust_height_to_content_safe(self):
        """Ajusta a altura da janela baseada no conteúdo de forma thread-safe"""
        if threading.current_thread() != threading.main_thread():
            QMetaObject.invokeMethod(
                self, "_adjust_height_to_content",
                Qt.QueuedConnection
            )
            return
        
        self._adjust_height_to_content()
    
    def _show_with_animation_safe(self):
        """Mostra a janela com animação de forma thread-safe"""
        if threading.current_thread() != threading.main_thread():
            QMetaObject.invokeMethod(
                self, "_show_with_animation",
                Qt.QueuedConnection
            )
            return
        
        self._show_with_animation()
    
    def _safe_hide(self):
        """Hide method thread-safe"""
        if threading.current_thread() != threading.main_thread():
            QMetaObject.invokeMethod(
                self, "hide",
                Qt.QueuedConnection
            )
            return
        
        self.hide()
    
    def show_message(self, message: str, auto_hide_delay: int = None, persistent: bool = False):
        """
        Mostra uma mensagem no popup de forma thread-safe
        
        Args:
            message: Mensagem a ser exibida
            auto_hide_delay: Tempo em ms para auto-ocultar (None = usa configuração)
            persistent: Se True, não aplica auto-hide (para toggle de visibilidade)
        """
        
        # Adiciona mensagem à queue thread-safe
        message_data = {
            'message': message,
            'auto_hide_delay': auto_hide_delay,
            'persistent': persistent
        }
        
        self._message_queue.put(message_data)
    
    def show_persistent_message(self, message: str):
        """
        Mostra uma mensagem persistente (não desaparece automaticamente)
        Usado para toggle de visibilidade
        """
        self.show_message(message, persistent=True)
    
    def _adjust_height_to_content(self):
        """Ajusta a altura da janela baseada no conteúdo"""
        
        # Calcula altura necessária para o texto
        doc = self.content_area.document()
        doc_height = doc.size().height()
        
        # Altura mínima e máxima
        min_height = 150
        max_height = 400
        content_height = max(min_height, min(max_height, int(doc_height) + 100))
        
        # Atualiza o tamanho
        current_geo = self.geometry()
        new_geo = QRect(current_geo.x(), current_geo.y(), 
                       config.POPUP_WIDTH, content_height)
        self.setGeometry(new_geo)
    
    def _show_with_animation(self):
        """Mostra a janela com animação suave"""
        
        # Posição inicial (fora da tela)
        current_geo = self.geometry()
        start_geo = QRect(current_geo.x() + 50, current_geo.y(), 
                         current_geo.width(), current_geo.height())
        
        # Configura animação de slide
        self.setGeometry(start_geo)
        self.slide_animation.setStartValue(start_geo)
        self.slide_animation.setEndValue(current_geo)
        
        # Mostra e anima
        self.show()
        self.slide_animation.start()
        
        # Animação de fade in
        self.setWindowOpacity(0.0)
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(config.POPUP_OPACITY)
        self.fade_animation.start()
    
    def hide(self):
        """Esconde a janela com animação"""
        
        # Para o timer de forma thread-safe
        if threading.current_thread() == threading.main_thread():
            self.auto_hide_timer.stop()
        else:
            QMetaObject.invokeMethod(
                self.auto_hide_timer, "stop",
                Qt.QueuedConnection
            )
        
        self.is_persistent = False  # Reset da flag de persistência
        
        # Animação de fade out
        self.fade_animation.setStartValue(config.POPUP_OPACITY)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.finished.connect(lambda: super(PopupWindow, self).hide())
        self.fade_animation.start()
    
    def _copy_content(self):
        """Copia o conteúdo para a área de transferência"""
        from PyQt5.QtWidgets import QApplication
        
        clipboard = QApplication.clipboard()
        clipboard.setText(self.content_area.toPlainText())
        
        # Feedback visual
        original_text = self.content_area.toPlainText()
        self.content_area.setPlainText("📋 Conteúdo copiado!")
        
        # Restaura após 1 segundo usando timer thread-safe
        restore_timer = QTimer()
        restore_timer.singleShot(1000, lambda: self.content_area.setPlainText(original_text))
    
    def keyPressEvent(self, event):
        """Trata eventos de teclado"""
        
        # ESC para fechar
        if event.key() == Qt.Key_Escape:
            self.hide()
        
        # Ctrl+C para copiar
        elif event.key() == Qt.Key_C and event.modifiers() == Qt.ControlModifier:
            self._copy_content()
        
        else:
            super().keyPressEvent(event)
    
    def mousePressEvent(self, event):
        """Permite arrastar a janela"""
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        """Arrasta a janela"""
        if (event.buttons() == Qt.LeftButton and 
            hasattr(self, 'drag_start_position')):
            self.move(event.globalPos() - self.drag_start_position)
            event.accept()
    
    def enterEvent(self, event):
        """Mouse entrou na janela - para auto-hide"""
        self.auto_hide_timer.stop()
    
    def leaveEvent(self, event):
        """Mouse saiu da janela - reinicia auto-hide se configurado"""
        if config.AUTO_HIDE_DELAY > 0 and not self.is_persistent:
            self.auto_hide_timer.start(config.AUTO_HIDE_DELAY) 