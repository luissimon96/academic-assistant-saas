import pytest
from unittest.mock import Mock, patch, AsyncMock
from PIL import Image
import io

from app.services.ocr_service import OCRService
from app.services.llm_service import LLMService
from app.config import Settings

class TestOCRService:
    """Testes para o serviço de OCR"""
    
    @pytest.fixture
    def ocr_service(self):
        """Fixture para instância do OCRService"""
        settings = Settings()
        return OCRService(settings)
    
    def create_test_image(self) -> Image.Image:
        """Cria uma imagem de teste"""
        return Image.new('RGB', (100, 100), color='white')
    
    @patch('pytesseract.image_to_string')
    def test_tesseract_ocr_success(self, mock_tesseract, ocr_service):
        """Testa OCR com Tesseract bem-sucedido"""
        mock_tesseract.return_value = "Extracted text"
        
        image = self.create_test_image()
        result = ocr_service._process_with_tesseract(image)
        
        assert result["text"] == "Extracted text"
        assert result["provider"] == "tesseract"
        assert "confidence" in result
        assert "processing_time" in result
