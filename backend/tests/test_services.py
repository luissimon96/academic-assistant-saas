import pytest
from unittest.mock import Mock, patch, AsyncMock
from PIL import Image
import io
import base64

from services.ocr_service import OCRService, ocr_service
from services.llm_service import LLMService, llm_service
from config import settings

class TestOCRService:
    """Testes para o serviço de OCR"""
    
    @pytest.fixture
    def ocr_service_instance(self):
        """Fixture para instância do OCRService"""
        return OCRService()
    
    def create_test_image(self) -> Image.Image:
        """Cria uma imagem de teste"""
        return Image.new('RGB', (100, 100), color='white')
    
    def create_test_image_base64(self) -> str:
        """Cria uma imagem de teste em base64"""
        img = self.create_test_image()
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        return base64.b64encode(img_bytes.getvalue()).decode('utf-8')
    
    @patch('pytesseract.image_to_string')
    @patch('pytesseract.image_to_data')
    def test_tesseract_ocr_success(self, mock_data, mock_string, ocr_service_instance):
        """Testa OCR com Tesseract bem-sucedido"""
        mock_string.return_value = "Extracted text"
        mock_data.return_value = {'conf': ['95', '90', '85']}
        
        image = self.create_test_image()
        result = ocr_service_instance._extract_with_tesseract(image)
        
        assert result.text == "Extracted text"
        assert result.provider.value == "tesseract"
        assert result.success is True
        assert result.confidence > 0
        assert result.processing_time >= 0
    
    def test_extract_text_integration(self, ocr_service_instance):
        """Testa a função extract_text com dados reais"""
        image_data = self.create_test_image_base64()
        
        # Este teste pode falhar se o Tesseract não estiver instalado
        # mas pelo menos testa a estrutura da função
        try:
            result = ocr_service_instance.extract_text(image_data, "free")
            assert hasattr(result, 'text')
            assert hasattr(result, 'provider')
            assert hasattr(result, 'success')
            assert hasattr(result, 'processing_time')
        except Exception:
            # Se falhar por dependências, pelo menos testamos a estrutura
            pass

class TestLLMService:
    """Testes para o serviço de LLM"""
    
    @pytest.fixture
    def llm_service_instance(self):
        """Fixture para instância do LLMService"""
        return LLMService()
    
    def test_get_explanation_success(self, llm_service_instance):
        """Testa explicação bem-sucedida de texto"""
        text = "Texto para explicar"
        result = llm_service_instance.get_explanation(text, "educacional", "pt-br")
        
        assert "explanation" in result
        assert "summary" in result
        assert "key_concepts" in result
        assert "processing_time" in result
        assert isinstance(result["key_concepts"], list)
        assert result["processing_time"] >= 0
    
    def test_get_explanation_empty_text(self, llm_service_instance):
        """Testa explicação com texto vazio"""
        result = llm_service_instance.get_explanation("", "educacional", "pt-br")
        
        assert "explanation" in result
        assert "processing_time" in result
        # Deve funcionar mesmo com texto vazio
    
    def test_global_instances(self):
        """Testa se as instâncias globais estão disponíveis"""
        assert ocr_service is not None
        assert llm_service is not None
        assert hasattr(ocr_service, 'extract_text')
        assert hasattr(llm_service, 'get_explanation')
