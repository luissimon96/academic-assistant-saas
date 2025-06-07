import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import io
from PIL import Image

from app.main import app

client = TestClient(app)

class TestHealthEndpoint:
    """Testes para o endpoint de health check"""
    
    def test_health_check(self):
        """Testa se o health check retorna status OK"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

class TestOCREndpoint:
    """Testes para os endpoints de OCR"""
    
    def create_test_image(self) -> bytes:
        """Cria uma imagem de teste"""
        img = Image.new('RGB', (100, 100), color='white')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        return img_bytes.getvalue()
    
    @patch('app.services.ocr_service.OCRService.process_image')
    def test_process_image_success(self, mock_process):
        """Testa processamento bem-sucedido de imagem"""
        # Mock do retorno do serviço OCR
        mock_process.return_value = {
            "text": "Sample extracted text",
            "confidence": 0.95,
            "processing_time": 1.2,
            "provider": "tesseract"
        }
        
        image_data = self.create_test_image()
        files = {"file": ("test.png", image_data, "image/png")}
        
        response = client.post("/api/ocr/process", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "text" in data["data"]
        assert data["data"]["text"] == "Sample extracted text"
        assert data["data"]["confidence"] == 0.95
    
    def test_process_image_no_file(self):
        """Testa erro quando nenhum arquivo é enviado"""
        response = client.post("/api/ocr/process")
        
        assert response.status_code == 422  # Validation error
    
    def test_process_image_invalid_format(self):
        """Testa erro com formato de arquivo inválido"""
        files = {"file": ("test.txt", b"not an image", "text/plain")}
        
        response = client.post("/api/ocr/process", files=files)
        
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "Invalid file format" in data["error"]
    
    @patch('app.services.ocr_service.OCRService.process_image')
    def test_process_image_service_error(self, mock_process):
        """Testa erro interno do serviço OCR"""
        mock_process.side_effect = Exception("OCR service failed")
        
        image_data = self.create_test_image()
        files = {"file": ("test.png", image_data, "image/png")}
        
        response = client.post("/api/ocr/process", files=files)
        
        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False
        assert "Internal server error" in data["error"]

class TestChatEndpoint:
    """Testes para o endpoint de chat/explicação"""
    
    @patch('app.services.llm_service.LLMService.get_explanation')
    def test_explain_text_success(self, mock_explain):
        """Testa explicação bem-sucedida de texto"""
        mock_explain.return_value = {
            "explanation": "Esta é uma explicação detalhada do texto.",
            "summary": "Resumo do conteúdo",
            "key_concepts": ["conceito1", "conceito2"],
            "processing_time": 2.1
        }
        
        payload = {
            "text": "Texto para explicar",
            "context": "educacional",
            "language": "pt-br"
        }
        
        response = client.post("/api/chat/explain", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "explanation" in data["data"]
        assert data["data"]["explanation"] == "Esta é uma explicação detalhada do texto."
    
    def test_explain_text_empty(self):
        """Testa erro com texto vazio"""
        payload = {"text": "", "context": "educacional"}
        
        response = client.post("/api/chat/explain", json=payload)
        
        assert response.status_code == 422  # Validation error
    
    def test_explain_text_missing_fields(self):
        """Testa erro com campos obrigatórios faltando"""
        payload = {"context": "educacional"}  # text missing
        
        response = client.post("/api/chat/explain", json=payload)
        
        assert response.status_code == 422  # Validation error

class TestRateLimiting:
    """Testes para rate limiting"""
    
    @patch('app.middleware.rate_limiter.check_rate_limit')
    def test_rate_limit_exceeded(self, mock_rate_limit):
        """Testa erro quando rate limit é excedido"""
        mock_rate_limit.return_value = False
        
        response = client.get("/health", headers={"X-User-ID": "test-user"})
        
        assert response.status_code == 429
        data = response.json()
        assert "Rate limit exceeded" in data["detail"]

class TestUserProfile:
    """Testes para endpoints de perfil de usuário"""
    
    @patch('app.services.auth_service.verify_token')
    def test_get_profile_success(self, mock_verify):
        """Testa obtenção bem-sucedida do perfil"""
        mock_verify.return_value = {"user_id": "test-user", "plan": "pro"}
        
        headers = {"Authorization": "Bearer fake-token"}
        response = client.get("/api/user/profile", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "user_id" in data["data"]
    
    def test_get_profile_no_token(self):
        """Testa erro sem token de autenticação"""
        response = client.get("/api/user/profile")
        
        assert response.status_code == 401
        data = response.json()
        assert "Authentication required" in data["detail"] 