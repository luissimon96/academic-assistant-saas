"""
Worker threads thread-safe para operações assíncronas
"""

import os
import time
import threading
from PyQt5.QtCore import QThread, pyqtSignal
from config import config
from utils.logger import get_component_logger, performance_monitor, thread_safety_monitor, log_exceptions

class ScreenshotWorker(QThread):
    """Worker thread para captura de tela thread-safe"""
    
    screenshot_taken = pyqtSignal(str)  # filepath
    screenshot_failed = pyqtSignal(str)  # error message
    progress_update = pyqtSignal(str)  # status message
    
    def __init__(self):
        super().__init__()
        self.pending_captures = []
        self.is_running = False
        self._thread_id = None
        
        # Logger específico para este componente
        self.logger = get_component_logger("ScreenshotWorker")
        self.logger.log_init({
            'pending_captures_size': len(self.pending_captures),
            'is_running': self.is_running
        })
    
    @thread_safety_monitor
    def request_capture(self, monitor_number: int = 1):
        """Solicita uma captura (thread-safe)"""
        self.logger.log_operation("REQUEST_CAPTURE", True, {
            'monitor_number': monitor_number,
            'queue_size_before': len(self.pending_captures),
            'thread_running': self.isRunning()
        })
        
        self.pending_captures.append(monitor_number)
        
        if not self.isRunning():
            self.logger.log_state_change("IDLE", "STARTING", {
                'pending_captures': len(self.pending_captures)
            })
            self.start()
    
    @log_exceptions
    @performance_monitor("ScreenshotWorker")
    def run(self):
        """Thread principal do worker"""
        self.is_running = True
        self._thread_id = threading.current_thread().ident
        
        self.logger.log_state_change("STARTING", "RUNNING", {
            'thread_id': self._thread_id,
            'thread_name': threading.current_thread().name,
            'pending_captures': len(self.pending_captures)
        })
        
        self.progress_update.emit("📸 Worker de captura inicializado")
        
        while self.is_running and self.pending_captures:
            try:
                monitor_number = self.pending_captures.pop(0)
                
                self.logger.log_operation("PROCESSING_CAPTURE", True, {
                    'monitor_number': monitor_number,
                    'remaining_queue': len(self.pending_captures)
                })
                
                self.progress_update.emit("📸 Capturando tela...")
                
                filepath = self._isolated_capture(monitor_number)
                
                if filepath:
                    self.screenshot_taken.emit(filepath)
                    self.logger.log_operation("CAPTURE_SUCCESS", True, {
                        'filepath': filepath,
                        'monitor_number': monitor_number
                    })
                else:
                    self.screenshot_failed.emit("Falha na captura de tela")
                    self.logger.log_operation("CAPTURE_FAILED", False, {
                        'monitor_number': monitor_number,
                        'reason': "No filepath returned"
                    })
                    
            except Exception as e:
                error_msg = f"Erro na captura: {e}"
                self.screenshot_failed.emit(error_msg)
                self.logger.log_error("CAPTURE_EXCEPTION", e, {
                    'monitor_number': monitor_number if 'monitor_number' in locals() else None
                })
        
        self.is_running = False
        self._cleanup_thread_resources()
        
        self.logger.log_state_change("RUNNING", "STOPPED", {
            'thread_id': self._thread_id,
            'cleanup_completed': True
        })
    
    @performance_monitor("ScreenshotCapture")
    def _isolated_capture(self, monitor_number: int = 1) -> str:
        """Captura isolada na thread worker com verificação de thread"""
        if threading.current_thread().ident != self._thread_id:
            error_msg = f"Operação executada em thread incorreta. Expected: {self._thread_id}, Current: {threading.current_thread().ident}"
            self.logger.log_error("THREAD_SAFETY_VIOLATION", Exception(error_msg), {
                'expected_thread_id': self._thread_id,
                'current_thread_id': threading.current_thread().ident
            })
            raise Exception(error_msg)
        
        import mss
        from PIL import Image
        
        sct = None
        start_time = time.time()
        
        try:
            self.logger.log_operation("MSS_INIT", True, {
                'monitor_number': monitor_number
            })
            
            # Cria instância MSS na thread worker
            sct = mss.mss()
            
            # Seleciona monitor
            if monitor_number == 0:
                monitor = sct.monitors[0]
            else:
                monitor = sct.monitors[monitor_number] if monitor_number < len(sct.monitors) else sct.monitors[1]
            
            self.logger.log_operation("MONITOR_SELECTED", True, {
                'monitor_number': monitor_number,
                'monitor_info': monitor,
                'available_monitors': len(sct.monitors)
            })
            
            self.progress_update.emit(f"📊 Monitor {monitor_number}: {monitor['width']}x{monitor['height']}")
            
            # Captura
            capture_start = time.time()
            screenshot = sct.grab(monitor)
            capture_duration = time.time() - capture_start
            
            self.logger.log_performance("MSS_GRAB", capture_duration)
            
            # Converte para PIL
            conversion_start = time.time()
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
            conversion_duration = time.time() - conversion_start
            
            self.logger.log_performance("PIL_CONVERSION", conversion_duration)
            
            # Redimensiona se necessário
            original_size = img.size
            if img.size[0] > config.MAX_IMAGE_SIZE[0] or img.size[1] > config.MAX_IMAGE_SIZE[1]:
                resize_start = time.time()
                img.thumbnail(config.MAX_IMAGE_SIZE, Image.Resampling.LANCZOS)
                resize_duration = time.time() - resize_start
                
                self.logger.log_operation("IMAGE_RESIZED", True, {
                    'original_size': original_size,
                    'new_size': img.size,
                    'resize_duration': resize_duration
                })
            
            # Salva
            timestamp = int(time.time() * 1000)
            filename = f"screenshot_{timestamp}.png"
            filepath = os.path.join(config.TEMP_DIR, filename)
            
            save_start = time.time()
            img.save(filepath, "PNG", quality=config.SCREENSHOT_QUALITY, optimize=True)
            save_duration = time.time() - save_start
            
            total_duration = time.time() - start_time
            
            self.logger.log_file_operation("SCREENSHOT_SAVE", filepath, True, {
                'save_duration': save_duration,
                'total_duration': total_duration,
                'file_size': os.path.getsize(filepath) if os.path.exists(filepath) else 0,
                'image_size': img.size,
                'quality': config.SCREENSHOT_QUALITY
            })
            
            self.progress_update.emit(f"✅ Screenshot salvo: {filename}")
            return filepath
            
        except Exception as e:
            self.progress_update.emit(f"❌ Erro na captura: {e}")
            self.logger.log_error("CAPTURE_FAILED", e, {
                'monitor_number': monitor_number,
                'duration_before_error': time.time() - start_time
            })
            return None
            
        finally:
            if sct:
                try:
                    sct.close()
                    self.logger.log_operation("MSS_CLEANUP", True, {})
                except Exception as cleanup_error:
                    self.logger.log_error("MSS_CLEANUP_FAILED", cleanup_error, {})
    
    def _cleanup_thread_resources(self):
        """Limpa recursos da thread"""
        try:
            cleanup_info = {
                'pending_captures_before': len(self.pending_captures),
                'thread_id_before': self._thread_id
            }
            
            # Limpa lista de capturas pendentes
            self.pending_captures.clear()
            
            # Reset thread ID
            self._thread_id = None
            
            self.logger.log_operation("RESOURCE_CLEANUP", True, cleanup_info)
            
        except Exception as e:
            self.logger.log_error("CLEANUP_FAILED", e, {})
    
    @thread_safety_monitor
    def stop_worker(self):
        """Para o worker thread com cleanup"""
        self.logger.log_state_change("RUNNING", "STOPPING", {
            'pending_captures': len(self.pending_captures),
            'is_running': self.is_running
        })
        
        self.is_running = False
        
        # Aguarda finalização
        if self.isRunning():
            wait_result = self.wait(3000)  # 3 segundos timeout
            self.logger.log_operation("THREAD_WAIT", wait_result, {
                'timeout_ms': 3000,
                'wait_success': wait_result
            })
        
        # Cleanup final
        self._cleanup_thread_resources()


class ProcessingWorker(QThread):
    """Worker thread para processamento com LLM thread-safe"""
    
    processing_started = pyqtSignal()
    processing_progress = pyqtSignal(str)
    processing_completed = pyqtSignal(str)
    processing_failed = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.pending_jobs = []
        self._thread_id = None
        self._api_client = None
        self._image_processor = None
        self._ocr_processor = None
        
        # Logger específico para este componente
        self.logger = get_component_logger("ProcessingWorker")
        self.logger.log_init({
            'pending_jobs_size': len(self.pending_jobs)
        })
    
    @thread_safety_monitor
    def request_processing(self, filepath: str):
        """Solicita processamento de imagem"""
        self.logger.log_operation("REQUEST_PROCESSING", True, {
            'filepath': filepath,
            'queue_size_before': len(self.pending_jobs),
            'thread_running': self.isRunning()
        })
        
        self.pending_jobs.append(filepath)
        
        if not self.isRunning():
            self.logger.log_state_change("IDLE", "STARTING", {
                'pending_jobs': len(self.pending_jobs)
            })
            self.start()
    
    @log_exceptions
    @performance_monitor("ProcessingWorker")
    def run(self):
        """Thread principal do worker de processamento"""
        self._thread_id = threading.current_thread().ident
        
        self.logger.log_state_change("STARTING", "RUNNING", {
            'thread_id': self._thread_id,
            'thread_name': threading.current_thread().name,
            'pending_jobs': len(self.pending_jobs)
        })
        
        self.processing_progress.emit("🔧 Worker de processamento inicializado")
        
        # Inicializa componentes na thread worker
        self._initialize_components()
        
        while self.pending_jobs:
            try:
                filepath = self.pending_jobs.pop(0)
                
                self.logger.log_operation("PROCESSING_JOB", True, {
                    'filepath': filepath,
                    'remaining_queue': len(self.pending_jobs)
                })
                
                self._process_image(filepath)
                
            except Exception as e:
                self.processing_failed.emit(f"Erro no processamento: {e}")
                self.logger.log_error("PROCESSING_EXCEPTION", e, {
                    'filepath': filepath if 'filepath' in locals() else None
                })
        
        # Cleanup ao finalizar
        self._cleanup_thread_resources()
        
        self.logger.log_state_change("RUNNING", "STOPPED", {
            'thread_id': self._thread_id,
            'cleanup_completed': True
        })
    
    @performance_monitor("ComponentInit")
    def _initialize_components(self):
        """Inicializa componentes na thread worker"""
        try:
            self.logger.log_operation("COMPONENT_INIT_START", True, {})
            
            from utils.api_client import OpenRouterClient
            from utils.image_processor import ImageProcessor
            
            self._api_client = OpenRouterClient()
            self._image_processor = ImageProcessor()
            
            # OCR opcional
            try:
                from utils.ocr_processor import OCRProcessor
                self._ocr_processor = OCRProcessor()
                ocr_available = self._ocr_processor.is_available() if self._ocr_processor else False
            except Exception as ocr_error:
                self._ocr_processor = None
                ocr_available = False
                self.logger.log_error("OCR_INIT_FAILED", ocr_error, {})
            
            self.logger.log_operation("COMPONENT_INIT_COMPLETE", True, {
                'api_client_ready': self._api_client is not None,
                'image_processor_ready': self._image_processor is not None,
                'ocr_available': ocr_available
            })
                
        except Exception as e:
            self.processing_failed.emit(f"Erro na inicialização: {e}")
            self.logger.log_error("COMPONENT_INIT_FAILED", e, {})
    
    @performance_monitor("ImageProcessing")
    def _process_image(self, filepath: str):
        """Processa imagem com OCR + LLM com verificação de thread"""
        if threading.current_thread().ident != self._thread_id:
            error_msg = f"Processamento executado em thread incorreta. Expected: {self._thread_id}, Current: {threading.current_thread().ident}"
            self.logger.log_error("THREAD_SAFETY_VIOLATION", Exception(error_msg), {
                'expected_thread_id': self._thread_id,
                'current_thread_id': threading.current_thread().ident,
                'filepath': filepath
            })
            raise Exception(error_msg)
        
        try:
            start_time = time.time()
            
            self.processing_started.emit()
            self.processing_progress.emit("📷 Processando imagem...")
            
            # Verifica se componentes foram inicializados
            if not self._api_client or not self._image_processor:
                error_msg = "Componentes não inicializados"
                self.processing_failed.emit(error_msg)
                self.logger.log_error("COMPONENTS_NOT_READY", Exception(error_msg), {
                    'api_client_ready': self._api_client is not None,
                    'image_processor_ready': self._image_processor is not None
                })
                return
            
            # Processamento de imagem
            image_start = time.time()
            image_result = self._image_processor.process_for_llm(filepath, 'balanced')
            image_duration = time.time() - image_start
            
            self.logger.log_performance("IMAGE_PROCESSING", image_duration, {
                'success': image_result.get('success', False)
            })
            
            processed_image_path = filepath  # Usa original se processamento falhar
            if image_result['success']:
                processed_image_path = filepath
            
            # OCR se disponível
            ocr_text = ""
            ocr_duration = 0
            if self._ocr_processor and self._ocr_processor.is_available():
                self.processing_progress.emit("🔤 Extraindo texto com OCR...")
                try:
                    ocr_start = time.time()
                    ocr_text = self._ocr_processor.extract_text(processed_image_path or filepath)
                    ocr_duration = time.time() - ocr_start
                    
                    self.logger.log_performance("OCR_EXTRACTION", ocr_duration, {
                        'text_length': len(ocr_text)
                    })
                except Exception as ocr_error:
                    self.logger.log_error("OCR_EXTRACTION_FAILED", ocr_error, {
                        'filepath': processed_image_path or filepath
                    })
            
            # Análise com LLM
            self.processing_progress.emit("🧠 Analisando com LLM...")
            
            # Cria prompt otimizado
            prompt = self._create_prompt(ocr_text)
            
            # Envia para API
            api_start = time.time()
            result = self._api_client.analyze_image(processed_image_path or filepath, prompt)
            api_duration = time.time() - api_start
            
            self.logger.log_api_request("analyze_image", api_duration, 
                                      result and result.get('success', False))
            
            if result and result.get('success'):
                # Formata resultado com estatísticas
                content = result['content']
                formatted_content = self._api_client.format_response_for_display(content)
                
                # Adiciona informações do processamento
                stats = f"\n\n📊 ESTATÍSTICAS:\n"
                stats += f"• OCR: {'✅ Ativo' if ocr_text else '❌ Não disponível'}\n"
                if image_result.get('success'):
                    stats += f"• Processamento: ✅ {image_result['processing_info']['optimization_level']}\n"
                    stats += f"• Tamanho: {image_result['processing_info']['file_size_kb']:.1f}KB\n"
                stats += f"• Tokens: {result.get('tokens_used', 'N/A')}\n"
                stats += f"• Tempo: {result.get('response_time', 0):.2f}s"
                
                final_content = formatted_content + stats
                self.processing_completed.emit(final_content)
                
                total_duration = time.time() - start_time
                self.logger.log_operation("PROCESSING_SUCCESS", True, {
                    'total_duration': total_duration,
                    'image_duration': image_duration,
                    'ocr_duration': ocr_duration,
                    'api_duration': api_duration,
                    'ocr_text_length': len(ocr_text),
                    'tokens_used': result.get('tokens_used', 0)
                })
                
            else:
                error_msg = result.get('error', 'Falha na análise com LLM') if result else 'Falha na análise com LLM'
                self.processing_failed.emit(error_msg)
                self.logger.log_error("LLM_ANALYSIS_FAILED", Exception(error_msg), {
                    'result': result,
                    'filepath': processed_image_path or filepath
                })
                
        except Exception as e:
            self.processing_failed.emit(f"Erro no processamento: {e}")
            self.logger.log_error("PROCESSING_FAILED", e, {
                'filepath': filepath
            })

    def _create_prompt(self, ocr_text: str) -> str:
        """Cria prompt otimizado"""
        base_prompt = config.SYSTEM_PROMPT
        
        if ocr_text:
            enhanced_prompt = base_prompt + f"""

TEXTO EXTRAÍDO POR OCR:
{ocr_text}

INSTRUÇÕES ADICIONAIS:
- Use o texto extraído como contexto principal
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
"""
        
        return enhanced_prompt
    
    def _cleanup_thread_resources(self):
        """Limpa recursos da thread"""
        try:
            cleanup_info = {
                'pending_jobs_before': len(self.pending_jobs),
                'thread_id_before': self._thread_id,
                'components_before': {
                    'api_client': self._api_client is not None,
                    'image_processor': self._image_processor is not None,
                    'ocr_processor': self._ocr_processor is not None
                }
            }
            
            # Limpa lista de jobs pendentes
            self.pending_jobs.clear()
            
            # Limpa componentes
            self._api_client = None
            self._image_processor = None
            self._ocr_processor = None
            
            # Reset thread ID
            self._thread_id = None
            
            self.logger.log_operation("RESOURCE_CLEANUP", True, cleanup_info)
            
        except Exception as e:
            self.logger.log_error("CLEANUP_FAILED", e, {})
    
    @thread_safety_monitor
    def stop_worker(self):
        """Para o worker thread com cleanup"""
        self.logger.log_state_change("RUNNING", "STOPPING", {
            'pending_jobs': len(self.pending_jobs)
        })
        
        # Limpa jobs pendentes
        self.pending_jobs.clear()
        
        # Aguarda finalização
        if self.isRunning():
            wait_result = self.wait(3000)  # 3 segundos timeout
            self.logger.log_operation("THREAD_WAIT", wait_result, {
                'timeout_ms': 3000,
                'wait_success': wait_result
            })
        
        # Cleanup final
        self._cleanup_thread_resources() 