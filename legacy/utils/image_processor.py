import os
import time
from typing import Dict, List, Tuple, Optional
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import base64
from io import BytesIO
from config import config

class ImageProcessor:
    """Processador avançado de imagens para otimização de LLM"""
    
    def __init__(self):
        self.processing_cache = {}
        self.last_processed = None
        
    def process_for_llm(self, image_path: str, optimization_level: str = 'balanced') -> Dict:
        """
        Processa imagem para envio otimizado ao LLM
        
        Args:
            image_path: Caminho para a imagem
            optimization_level: 'fast', 'balanced', 'quality'
            
        Returns:
            Dicionário com imagem processada e metadados
        """
        try:
            # Carrega a imagem
            image = Image.open(image_path)
            original_size = image.size
            
            # Aplica processamento baseado no nível
            if optimization_level == 'fast':
                processed_image = self._fast_processing(image)
            elif optimization_level == 'quality':
                processed_image = self._quality_processing(image)
            else:  # balanced
                processed_image = self._balanced_processing(image)
            
            # Comprime para envio
            compressed_data = self._compress_for_api(processed_image)
            
            # Gera informações sobre o processamento
            processing_info = {
                'original_size': original_size,
                'processed_size': processed_image.size,
                'compression_ratio': len(compressed_data) / os.path.getsize(image_path),
                'optimization_level': optimization_level,
                'file_size_kb': len(compressed_data) / 1024,
                'timestamp': time.time()
            }
            
            return {
                'success': True,
                'image_data': compressed_data,
                'base64_data': base64.b64encode(compressed_data).decode('utf-8'),
                'processing_info': processing_info,
                'processed_image': processed_image
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Erro no processamento: {str(e)}',
                'image_data': None
            }
    
    def _fast_processing(self, image: Image.Image) -> Image.Image:
        """Processamento rápido com otimizações básicas"""
        
        # Redimensiona se muito grande
        if image.size[0] > 1280 or image.size[1] > 720:
            image.thumbnail((1280, 720), Image.Resampling.LANCZOS)
        
        # Melhora contraste básico
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.1)
        
        return image
    
    def _balanced_processing(self, image: Image.Image) -> Image.Image:
        """Processamento equilibrado entre qualidade e velocidade"""
        
        # Converte para RGB se necessário
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Redimensiona inteligentemente
        image = self._smart_resize(image)
        
        # Melhora qualidade da imagem
        image = self._enhance_readability(image)
        
        # Remove ruído
        image = image.filter(ImageFilter.MedianFilter(size=3))
        
        return image
    
    def _quality_processing(self, image: Image.Image) -> Image.Image:
        """Processamento de alta qualidade para melhor análise"""
        
        # Converte para RGB
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Redimensiona com qualidade máxima
        image = self._smart_resize(image, max_size=(1920, 1080))
        
        # Aplica múltiplas melhorias
        image = self._enhance_readability(image, aggressive=True)
        
        # Nitidez aprimorada
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(1.2)
        
        # Filtro avançado de ruído
        image = image.filter(ImageFilter.UnsharpMask(radius=1, percent=120, threshold=1))
        
        return image
    
    def _smart_resize(self, image: Image.Image, max_size: Tuple[int, int] = (1440, 900)) -> Image.Image:
        """
        Redimensiona inteligentemente preservando aspecto e legibilidade
        
        Args:
            image: Imagem original
            max_size: Tamanho máximo (largura, altura)
            
        Returns:
            Imagem redimensionada
        """
        width, height = image.size
        max_width, max_height = max_size
        
        # Calcula se precisa redimensionar
        if width <= max_width and height <= max_height:
            return image
        
        # Calcula nova dimensão mantendo aspecto
        ratio = min(max_width / width, max_height / height)
        new_width = int(width * ratio)
        new_height = int(height * ratio)
        
        # Usa algoritmo de alta qualidade
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    def _enhance_readability(self, image: Image.Image, aggressive: bool = False) -> Image.Image:
        """
        Melhora a legibilidade do texto na imagem
        
        Args:
            image: Imagem original
            aggressive: Se deve aplicar melhorias mais agressivas
            
        Returns:
            Imagem com legibilidade melhorada
        """
        # Melhora contraste
        contrast_factor = 1.3 if aggressive else 1.15
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(contrast_factor)
        
        # Melhora brilho se necessário
        brightness_factor = 1.05 if aggressive else 1.02
        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(brightness_factor)
        
        # Aumenta saturação ligeiramente para melhor distinção
        enhancer = ImageEnhance.Color(image)
        image = enhancer.enhance(1.1)
        
        return image
    
    def _compress_for_api(self, image: Image.Image, target_size_kb: int = 500) -> bytes:
        """
        Comprime imagem para tamanho ideal para API
        
        Args:
            image: Imagem processada
            target_size_kb: Tamanho alvo em KB
            
        Returns:
            Dados da imagem comprimida
        """
        # Primeira tentativa com qualidade alta
        quality = 85
        
        while quality > 20:
            buffer = BytesIO()
            image.save(buffer, format='JPEG', quality=quality, optimize=True)
            
            size_kb = len(buffer.getvalue()) / 1024
            
            if size_kb <= target_size_kb:
                return buffer.getvalue()
            
            quality -= 10
        
        # Se ainda muito grande, reduz resolução
        if size_kb > target_size_kb:
            scale_factor = (target_size_kb / size_kb) ** 0.5
            new_size = (
                int(image.size[0] * scale_factor),
                int(image.size[1] * scale_factor)
            )
            
            image = image.resize(new_size, Image.Resampling.LANCZOS)
            
            buffer = BytesIO()
            image.save(buffer, format='JPEG', quality=75, optimize=True)
            return buffer.getvalue()
        
        return buffer.getvalue()
    
    def extract_regions_of_interest(self, image_path: str) -> List[Dict]:
        """
        Identifica e extrai regiões de interesse da imagem
        
        Args:
            image_path: Caminho para a imagem
            
        Returns:
            Lista de regiões identificadas
        """
        try:
            image = Image.open(image_path)
            
            # Converte para análise
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            regions = []
            
            # Detecta regiões com texto (usando heurísticas simples)
            text_regions = self._detect_text_regions(image)
            regions.extend(text_regions)
            
            # Detecta possíveis diagramas ou gráficos
            diagram_regions = self._detect_diagram_regions(image)
            regions.extend(diagram_regions)
            
            return regions
            
        except Exception as e:
            return [{'error': f'Erro na análise: {str(e)}'}]
    
    def _detect_text_regions(self, image: Image.Image) -> List[Dict]:
        """Detecta regiões que provavelmente contêm texto"""
        
        # Converte para escala de cinza para análise
        gray = image.convert('L')
        width, height = gray.size
        
        # Divide a imagem em regiões e analisa densidade de pixels
        regions = []
        grid_size = 8  # 8x8 grid
        
        region_width = width // grid_size
        region_height = height // grid_size
        
        for i in range(grid_size):
            for j in range(grid_size):
                left = i * region_width
                top = j * region_height
                right = min(left + region_width, width)
                bottom = min(top + region_height, height)
                
                # Extrai região
                region = gray.crop((left, top, right, bottom))
                
                # Analisa se tem características de texto
                if self._has_text_characteristics(region):
                    regions.append({
                        'type': 'text',
                        'bbox': (left, top, right, bottom),
                        'confidence': 0.7,
                        'area': (right - left) * (bottom - top)
                    })
        
        return regions
    
    def _has_text_characteristics(self, region: Image.Image) -> bool:
        """Verifica se uma região tem características de texto"""
        
        # Converte para lista de pixels
        pixels = list(region.getdata())
        
        if not pixels:
            return False
        
        # Calcula estatísticas básicas
        avg_brightness = sum(pixels) / len(pixels)
        
        # Texto geralmente tem contraste (mix de pixels claros e escuros)
        dark_pixels = sum(1 for p in pixels if p < 100)
        light_pixels = sum(1 for p in pixels if p > 155)
        
        dark_ratio = dark_pixels / len(pixels)
        light_ratio = light_pixels / len(pixels)
        
        # Região tem texto se tiver bom contraste
        return (dark_ratio > 0.1 and light_ratio > 0.3) or (dark_ratio > 0.3 and light_ratio > 0.1)
    
    def _detect_diagram_regions(self, image: Image.Image) -> List[Dict]:
        """Detecta regiões que podem conter diagramas ou gráficos"""
        
        # Para simplicidade, detecta regiões com muitas linhas retas
        # (Implementação básica - pode ser expandida)
        
        width, height = image.size
        
        # Verifica se tem características de diagrama na imagem inteira
        has_diagram = self._has_diagram_characteristics(image)
        
        if has_diagram:
            return [{
                'type': 'diagram',
                'bbox': (0, 0, width, height),
                'confidence': 0.6,
                'area': width * height
            }]
        
        return []
    
    def _has_diagram_characteristics(self, image: Image.Image) -> bool:
        """Verifica se a imagem tem características de diagrama"""
        
        # Converte para escala de cinza
        gray = image.convert('L')
        
        # Aplica filtro de detecção de bordas simples
        edges = gray.filter(ImageFilter.FIND_EDGES)
        
        # Conta pixels de borda
        edge_pixels = list(edges.getdata())
        edge_count = sum(1 for p in edge_pixels if p > 50)
        
        # Se muitas bordas, provavelmente é diagrama
        edge_ratio = edge_count / len(edge_pixels)
        
        return edge_ratio > 0.05  # 5% de pixels com bordas
    
    def create_comparison_image(self, original_path: str, processed_image: Image.Image) -> str:
        """
        Cria imagem de comparação entre original e processada
        
        Args:
            original_path: Caminho da imagem original
            processed_image: Imagem processada
            
        Returns:
            Caminho da imagem de comparação
        """
        try:
            original = Image.open(original_path)
            
            # Redimensiona ambas para mesmo tamanho
            max_width = 800
            max_height = 600
            
            original.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            processed_image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            
            # Cria imagem lado a lado
            total_width = original.size[0] + processed_image.size[0] + 20
            max_height = max(original.size[1], processed_image.size[1])
            
            comparison = Image.new('RGB', (total_width, max_height), 'white')
            
            # Cola as imagens
            comparison.paste(original, (0, 0))
            comparison.paste(processed_image, (original.size[0] + 20, 0))
            
            # Adiciona labels
            draw = ImageDraw.Draw(comparison)
            try:
                font = ImageFont.truetype("arial.ttf", 16)
            except:
                font = ImageFont.load_default()
            
            draw.text((10, 10), "Original", fill='black', font=font)
            draw.text((original.size[0] + 30, 10), "Processada", fill='black', font=font)
            
            # Salva comparação
            comparison_path = os.path.join(config.TEMP_DIR, f"comparison_{int(time.time())}.png")
            comparison.save(comparison_path, 'PNG')
            
            return comparison_path
            
        except Exception as e:
            print(f"Erro ao criar comparação: {e}")
            return None
    
    def get_processing_stats(self) -> Dict:
        """Retorna estatísticas de processamento"""
        
        return {
            'cache_size': len(self.processing_cache),
            'last_processed': self.last_processed,
            'available_optimizations': ['fast', 'balanced', 'quality'],
            'supported_formats': ['PNG', 'JPEG', 'BMP', 'TIFF']
        } 