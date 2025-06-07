import os
import re
import tempfile
from typing import Dict, List, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont
import pytesseract
from config import config

class OCRProcessor:
    """Processador OCR otimizado para conteúdo acadêmico"""
    
    def __init__(self):
        self.tesseract_path = self._find_tesseract()
        if self.tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_path
        
        # Configurações específicas para diferentes tipos de conteúdo
        self.ocr_configs = {
            'default': '--oem 3 --psm 6',
            'single_line': '--oem 3 --psm 8',
            'single_word': '--oem 3 --psm 10',
            'math': '--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789+-=×÷√∫∑∞πesincostan()[]{}',
            'table': '--oem 3 --psm 6',
            'dense_text': '--oem 3 --psm 4'
        }
        
        # Padrões para detecção de conteúdo matemático
        self.math_patterns = [
            r'[∫∑∞π√]',  # Símbolos matemáticos
            r'\b(?:sin|cos|tan|log|ln|exp)\b',  # Funções
            r'[=+\-*/^]',  # Operadores
            r'\d+[xyz]',  # Variáveis com números
            r'[()[\]{}].*[()[\]{}]'  # Expressões com parênteses
        ]
    
    def _find_tesseract(self) -> Optional[str]:
        """Encontra o executável do Tesseract no sistema"""
        
        possible_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            r"C:\Tesseract-OCR\tesseract.exe",
            "tesseract"  # PATH do sistema
        ]
        
        for path in possible_paths:
            if os.path.exists(path) or path == "tesseract":
                try:
                    # Testa se funciona
                    test_image = Image.new('RGB', (100, 50), color='white')
                    draw = ImageDraw.Draw(test_image)
                    draw.text((10, 10), "Test", fill='black')
                    
                    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                        test_image.save(tmp.name)
                        
                        if path != "tesseract":
                            pytesseract.pytesseract.tesseract_cmd = path
                        
                        result = pytesseract.image_to_string(test_image, config='--psm 10')
                        os.unlink(tmp.name)
                        
                        if result.strip():
                            print(f"✅ Tesseract encontrado: {path}")
                            return path
                            
                except Exception:
                    continue
        
        print("❌ Tesseract não encontrado. OCR pode não funcionar.")
        return None
    
    def extract_text(self, image_path: str, content_type: str = 'default') -> Dict:
        """
        Extrai texto de uma imagem usando OCR
        
        Args:
            image_path: Caminho para a imagem
            content_type: Tipo de conteúdo (default, math, table, etc.)
            
        Returns:
            Dicionário com texto extraído e metadados
        """
        if not self.tesseract_path:
            return {
                'success': False,
                'error': 'Tesseract não instalado',
                'text': '',
                'confidence': 0
            }
        
        try:
            # Carrega e processa a imagem
            image = Image.open(image_path)
            processed_image = self._preprocess_image(image, content_type)
            
            # Seleciona configuração OCR apropriada
            config_string = self.ocr_configs.get(content_type, self.ocr_configs['default'])
            
            # Extrai texto
            text = pytesseract.image_to_string(
                processed_image, 
                lang=config.OCR_LANGUAGE,
                config=config_string
            )
            
            # Obtém dados de confiança
            data = pytesseract.image_to_data(
                processed_image,
                lang=config.OCR_LANGUAGE,
                config=config_string,
                output_type=pytesseract.Output.DICT
            )
            
            # Calcula confiança média
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            # Pós-processa o texto
            cleaned_text = self._postprocess_text(text, content_type)
            
            # Detecta tipo de conteúdo automaticamente se não especificado
            detected_type = self._detect_content_type(cleaned_text)
            
            return {
                'success': True,
                'text': cleaned_text,
                'raw_text': text,
                'confidence': avg_confidence,
                'content_type': content_type,
                'detected_type': detected_type,
                'word_count': len(cleaned_text.split()),
                'has_math': self._contains_math(cleaned_text),
                'data': data
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Erro no OCR: {str(e)}',
                'text': '',
                'confidence': 0
            }
    
    def _preprocess_image(self, image: Image.Image, content_type: str) -> Image.Image:
        """
        Pré-processa a imagem para melhorar OCR
        
        Args:
            image: Imagem PIL
            content_type: Tipo de conteúdo
            
        Returns:
            Imagem processada
        """
        # Converte para escala de cinza se colorida
        if image.mode != 'L':
            image = image.convert('L')
        
        # Redimensiona se muito pequena (melhora OCR)
        width, height = image.size
        if width < 300 or height < 100:
            scale_factor = max(300/width, 100/height)
            new_size = (int(width * scale_factor), int(height * scale_factor))
            image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        # Processamento específico por tipo
        if content_type == 'math':
            # Para matemática, aumenta contraste
            from PIL import ImageEnhance
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.5)
            
        elif content_type == 'table':
            # Para tabelas, aplica filtro para linhas
            from PIL import ImageFilter
            image = image.filter(ImageFilter.EDGE_ENHANCE)
        
        return image
    
    def _postprocess_text(self, text: str, content_type: str) -> str:
        """
        Pós-processa o texto extraído
        
        Args:
            text: Texto bruto do OCR
            content_type: Tipo de conteúdo
            
        Returns:
            Texto limpo
        """
        if not text:
            return ""
        
        # Limpeza básica
        text = text.strip()
        
        # Remove linhas muito curtas (provavelmente ruído)
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if len(line) > 2:  # Mantém apenas linhas com mais de 2 caracteres
                cleaned_lines.append(line)
        
        text = '\n'.join(cleaned_lines)
        
        # Correções específicas por tipo
        if content_type == 'math':
            text = self._fix_math_text(text)
        
        # Remove espaços excessivos
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        return text.strip()
    
    def _fix_math_text(self, text: str) -> str:
        """Corrige erros comuns em texto matemático"""
        
        # Substituições comuns de OCR em matemática
        replacements = {
            'O': '0',  # O maiúsculo -> zero
            'l': '1',  # l minúsculo -> um (em contexto numérico)
            'S': '5',  # S -> 5 (em contexto numérico)  
            '×': '*',  # Símbolo de multiplicação
            '÷': '/',  # Símbolo de divisão
            '—': '-',  # Traço longo -> hífen
            '"': '',   # Remove aspas desnecessárias
        }
        
        # Aplica substituições em contexto matemático
        for old, new in replacements.items():
            # Substitui apenas se cercado por números ou operadores
            pattern = f'(?<=[0-9+\-*/=()]){re.escape(old)}(?=[0-9+\-*/=()])'
            text = re.sub(pattern, new, text)
        
        return text
    
    def _detect_content_type(self, text: str) -> str:
        """
        Detecta automaticamente o tipo de conteúdo
        
        Args:
            text: Texto para análise
            
        Returns:
            Tipo detectado
        """
        if not text:
            return 'unknown'
        
        # Verifica se contém matemática
        if self._contains_math(text):
            return 'math'
        
        # Verifica se é tabela (múltiplas colunas alinhadas)
        lines = text.split('\n')
        if len(lines) > 2:
            # Conta espaços consecutivos (indicativo de tabela)
            space_counts = [len(re.findall(r'\s{2,}', line)) for line in lines]
            if sum(space_counts) > len(lines):
                return 'table'
        
        # Verifica se é lista de múltipla escolha
        if re.search(r'[a-e]\)|[A-E]\)', text):
            return 'multiple_choice'
        
        # Verifica se é código de programação
        code_indicators = ['def ', 'class ', 'import ', 'function', 'var ', 'int ', '{', '}', ';']
        if any(indicator in text for indicator in code_indicators):
            return 'code'
        
        return 'text'
    
    def _contains_math(self, text: str) -> bool:
        """Verifica se o texto contém elementos matemáticos"""
        
        for pattern in self.math_patterns:
            if re.search(pattern, text):
                return True
        
        return False
    
    def extract_structured_data(self, image_path: str) -> Dict:
        """
        Extrai dados estruturados (questões, alternativas, etc.)
        
        Args:
            image_path: Caminho para a imagem
            
        Returns:
            Dados estruturados extraídos
        """
        result = self.extract_text(image_path)
        
        if not result['success']:
            return result
        
        text = result['text']
        structured_data = {
            'question': '',
            'alternatives': [],
            'type': result['detected_type'],
            'has_math': result['has_math']
        }
        
        # Detecta questões de múltipla escolha
        if result['detected_type'] == 'multiple_choice':
            lines = text.split('\n')
            question_lines = []
            alternatives = []
            
            for line in lines:
                line = line.strip()
                
                # Verifica se é alternativa (a), b), etc.)
                alt_match = re.match(r'^([a-eA-E])\)\s*(.+)$', line)
                if alt_match:
                    letter, content = alt_match.groups()
                    alternatives.append({
                        'letter': letter.upper(),
                        'content': content.strip()
                    })
                else:
                    # É parte da questão
                    if line and not alternatives:  # Apenas antes das alternativas
                        question_lines.append(line)
            
            structured_data['question'] = '\n'.join(question_lines).strip()
            structured_data['alternatives'] = alternatives
        
        else:
            # Para outros tipos, todo o texto é a questão
            structured_data['question'] = text
        
        return {**result, 'structured': structured_data}
    
    def is_available(self) -> bool:
        """Verifica se o OCR está disponível"""
        return self.tesseract_path is not None
    
    def get_supported_languages(self) -> List[str]:
        """Retorna lista de idiomas suportados pelo Tesseract"""
        if not self.tesseract_path:
            return []
        
        try:
            langs = pytesseract.get_languages()
            return langs
        except Exception:
            return ['eng', 'por']  # Fallback padrão 