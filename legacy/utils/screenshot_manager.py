import os
import time
import base64
import threading
from io import BytesIO
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
import mss
from config import config

class ScreenshotManager:
    """Gerenciador otimizado de capturas de tela com recursos stealth"""
    
    def __init__(self):
        self.sct = None
        self.last_screenshot_path = None
        self._lock = threading.Lock()  # Lock para thread safety
        self._initialize_mss()
    
    def _initialize_mss(self):
        """Inicializa o MSS de forma segura"""
        try:
            # Fecha instância anterior se existir
            if hasattr(self, 'sct') and self.sct is not None:
                try:
                    self.sct.close()
                except:
                    pass
            
            # Cria nova instância MSS
            self.sct = mss.mss()
            
        except Exception as e:
            print(f"Erro ao inicializar MSS: {e}")
            self.sct = None
    
    def _ensure_mss(self):
        """Garante que o MSS está inicializado"""
        if self.sct is None:
            self._initialize_mss()
        return self.sct is not None
        
    def capture_screen(self, monitor_number: int = 1) -> str:
        """
        Captura a tela especificada e retorna o caminho do arquivo
        
        Args:
            monitor_number: Número do monitor (1 = principal, 0 = todos)
        
        Returns:
            Caminho para o arquivo de screenshot salvo
        """
        with self._lock:  # Thread safety
            return self._capture_screen_internal(monitor_number)
    
    def _capture_screen_internal(self, monitor_number: int = 1, max_retries: int = 3) -> str:
        """
        Captura interna com retry automático
        """
        for attempt in range(max_retries):
            try:
                # Reinicializa MSS a cada tentativa para evitar problemas de thread
                if attempt > 0 or not self._ensure_mss():
                    print(f"🔄 Tentativa {attempt + 1}/{max_retries} - Reinicializando MSS...")
                    self.sct = None
                    if not self._ensure_mss():
                        continue
                
                # Seleciona o monitor
                if monitor_number == 0:
                    # Captura todos os monitores
                    monitor = self.sct.monitors[0]
                else:
                    # Captura monitor específico
                    monitor = self.sct.monitors[monitor_number] if monitor_number < len(self.sct.monitors) else self.sct.monitors[1]
                
                print(f"📊 Capturando monitor {monitor_number}: {monitor['width']}x{monitor['height']}")
                
                # Captura a tela
                screenshot = self.sct.grab(monitor)
                
                # Converte para PIL Image
                img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
                
                # Otimiza o tamanho se necessário
                img = self._optimize_image(img)
                
                # Salva temporariamente
                timestamp = int(time.time() * 1000)
                filename = f"screenshot_{timestamp}.png"
                filepath = os.path.join(config.TEMP_DIR, filename)
                
                img.save(filepath, "PNG", quality=config.SCREENSHOT_QUALITY, optimize=True)
                self.last_screenshot_path = filepath
                
                print(f"✅ Screenshot salvo: {filename}")
                return filepath
                
            except Exception as e:
                print(f"❌ Tentativa {attempt + 1} falhou: {e}")
                self.sct = None  # Force reinicialização na próxima tentativa
                if attempt < max_retries - 1:
                    time.sleep(0.1)  # Pequena pausa antes da próxima tentativa
                continue
        
        print("❌ Todas as tentativas de captura falharam")
        
        # Última tentativa: captura isolada
        print("🔄 Tentando captura isolada como último recurso...")
        return self._isolated_capture(monitor_number)
    
    def _isolated_capture(self, monitor_number: int = 1) -> str:
        """
        Captura isolada criando uma nova instância MSS do zero
        """
        sct_isolated = None
        try:
            # Cria instância MSS completamente nova e isolada
            sct_isolated = mss.mss()
            
            # Seleciona o monitor
            if monitor_number == 0:
                monitor = sct_isolated.monitors[0]
            else:
                monitor = sct_isolated.monitors[monitor_number] if monitor_number < len(sct_isolated.monitors) else sct_isolated.monitors[1]
            
            print(f"📊 Captura isolada - Monitor {monitor_number}: {monitor['width']}x{monitor['height']}")
            
            # Captura
            screenshot = sct_isolated.grab(monitor)
            
            # Converte para PIL Image
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
            
            # Otimiza
            img = self._optimize_image(img)
            
            # Salva
            timestamp = int(time.time() * 1000)
            filename = f"screenshot_{timestamp}.png"
            filepath = os.path.join(config.TEMP_DIR, filename)
            
            img.save(filepath, "PNG", quality=config.SCREENSHOT_QUALITY, optimize=True)
            self.last_screenshot_path = filepath
            
            print(f"✅ Captura isolada bem-sucedida: {filename}")
            return filepath
            
        except Exception as e:
            print(f"❌ Captura isolada também falhou: {e}")
            return None
            
        finally:
            # Sempre fecha a instância isolada
            if sct_isolated:
                try:
                    sct_isolated.close()
                except:
                    pass
    
    def capture_active_window(self) -> str:
        """
        Captura apenas a janela ativa (mais stealth)
        
        Returns:
            Caminho para o arquivo de screenshot da janela ativa
        """
        try:
            # Versão simplificada que usa MSS para evitar problemas de threading
            # Captura o monitor principal (mais estável)
            return self.capture_screen(monitor_number=1)
            
        except Exception as e:
            print(f"Erro ao capturar janela ativa: {e}")
            return self.capture_screen()  # Fallback
    
    def _optimize_image(self, img: Image.Image) -> Image.Image:
        """
        Otimiza a imagem para envio à API
        
        Args:
            img: Imagem PIL original
            
        Returns:
            Imagem otimizada
        """
        # Redimensiona se muito grande
        if img.size[0] > config.MAX_IMAGE_SIZE[0] or img.size[1] > config.MAX_IMAGE_SIZE[1]:
            img.thumbnail(config.MAX_IMAGE_SIZE, Image.Resampling.LANCZOS)
        
        # Melhora o contraste para melhor OCR
        img = self._enhance_for_ocr(img)
        
        return img
    
    def _enhance_for_ocr(self, img: Image.Image) -> Image.Image:
        """
        Melhora a imagem para melhor reconhecimento de texto
        
        Args:
            img: Imagem PIL original
            
        Returns:
            Imagem processada
        """
        # Aumenta o contraste
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.2)
        
        # Aumenta a nitidez
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(1.1)
        
        # Aplica filtro para reduzir ruído
        img = img.filter(ImageFilter.MedianFilter(size=3))
        
        return img
    
    def get_image_base64(self, filepath: str) -> str:
        """
        Converte imagem para base64 para envio à API
        
        Args:
            filepath: Caminho para o arquivo de imagem
            
        Returns:
            String base64 da imagem
        """
        try:
            with open(filepath, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            print(f"Erro ao converter imagem para base64: {e}")
            return None
    
    def cleanup_old_screenshots(self, max_age_hours: int = 1):
        """
        Remove screenshots antigos para economizar espaço
        
        Args:
            max_age_hours: Idade máxima dos arquivos em horas
        """
        try:
            current_time = time.time()
            for filename in os.listdir(config.TEMP_DIR):
                if filename.startswith(('screenshot_', 'window_capture_')):
                    filepath = os.path.join(config.TEMP_DIR, filename)
                    file_age = current_time - os.path.getctime(filepath)
                    
                    if file_age > (max_age_hours * 3600):
                        os.remove(filepath)
                        
        except Exception as e:
            print(f"Erro na limpeza de arquivos: {e}")
    
    def get_available_monitors(self) -> list:
        """
        Retorna lista de monitores disponíveis
        
        Returns:
            Lista com informações dos monitores
        """
        try:
            if not self._ensure_mss():
                return []
                
            monitors = []
            for i, monitor in enumerate(self.sct.monitors):
                if i == 0:
                    continue  # Pula o monitor "All in One"
                monitors.append({
                    'number': i,
                    'width': monitor['width'],
                    'height': monitor['height'],
                    'left': monitor['left'],
                    'top': monitor['top']
                })
            return monitors
        except Exception as e:
            print(f"Erro ao listar monitores: {e}")
            return [] 