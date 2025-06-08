import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import io
import base64
from PIL import Image

from main import app

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

class TestProcessEndpoint:
    """Testes para o endpoint de processamento"""
    
    def create_test_image_base64(self) -> str:
        """Cria uma imagem de teste em base64"""
        img = Image.new('RGB', (100, 100), color='white')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        return base64.b64encode(img_bytes.getvalue()).decode('utf-8')
    
    @patch('services.ocr_service.ocr_service.extract_text')
    def test_process_image_success(self, mock_ocr):
        """Testa processamento bem-sucedido de imagem"""
        # Mock do retorno do serviço OCR
        from models import OCRResult, OCRProvider
        mock_ocr.return_value = OCRResult(
            provider=OCRProvider.TESSERACT,
            text="Sample extracted text",
            confidence=0.95,
            processing_time=1.2,
            success=True
        )
        
        image_data = self.create_test_image_base64()
        payload = {"image_data": image_data}
        
        # Mock authentication
        headers = {"Authorization": "Bearer test-token"}
        response = client.post("/process", json=payload, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["request_id"] is not None
    
    def test_process_image_no_auth(self):
        """Testa erro quando não há autenticação"""
        image_data = self.create_test_image_base64()
        payload = {"image_data": image_data}
        
        response = client.post("/process", json=payload)
        
        assert response.status_code == 403  # Forbidden without auth
    
    def test_process_image_invalid_data(self):
        """Testa erro com dados inválidos"""
        payload = {"image_data": "invalid_base64"}
        headers = {"Authorization": "Bearer test-token"}
        
        response = client.post("/process", json=payload, headers=headers)
        
        # O endpoint pode retornar 200 com erro no resultado ou um código de erro
        # Vamos verificar se há erro no resultado quando status é 200
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is False or "error" in data
        else:
            assert response.status_code in [400, 422, 500]

class TestUserEndpoints:
    """Testes para endpoints de usuário"""
    
    def test_get_profile_success(self):
        """Testa obtenção bem-sucedida do perfil"""
        headers = {"Authorization": "Bearer test-token"}
        response = client.get("/user/profile", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "email" in data
        assert "plan" in data
    
    def test_get_profile_no_token(self):
        """Testa erro sem token de autenticação"""
        response = client.get("/user/profile")
        
        assert response.status_code == 403  # Forbidden without auth
    
    def test_get_usage_success(self):
        """Testa obtenção bem-sucedida do uso"""
        headers = {"Authorization": "Bearer test-token"}
        response = client.get("/user/usage", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "current_month_usage" in data
        assert "plan_limit" in data

class TestRootEndpoint:
    """Testes para o endpoint raiz"""
    
    def test_root_endpoint(self):
        """Testa o endpoint raiz"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data

class TestPlansEndpoint:
    """Testes para o endpoint de planos"""
    
    def test_get_plans(self):
        """Testa obtenção dos planos disponíveis"""
        response = client.get("/plans")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        
        # Os planos podem estar diretamente no data ou dentro de data["plans"]
        plans_data = data.get("plans", data)
        assert "free" in plans_data
        assert "pro" in plans_data
        assert "max" in plans_data 