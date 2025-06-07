import requests
import json
import base64
import time
from typing import Optional, Dict, Any
from config import config

class OpenRouterClient:
    """Cliente otimizado para OpenRouter API com foco em Claude-3.5-Sonnet"""
    
    def __init__(self):
        self.base_url = config.OPENROUTER_BASE_URL
        self.api_key = config.OPENROUTER_API_KEY
        self.model = config.MODEL_NAME
        self.session = requests.Session()
        
        # Headers padrão
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:3000",  # Seu domínio
            "X-Title": "Academic Assistant Stealth"  # Nome da aplicação
        })
        
    def analyze_image(self, image_path: str, custom_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Analisa uma imagem usando Claude-3.5-Sonnet
        
        Args:
            image_path: Caminho para a imagem
            custom_prompt: Prompt personalizado (opcional)
            
        Returns:
            Dicionário com a resposta da API
        """
        try:
            # Carrega e codifica a imagem
            image_base64 = self._encode_image(image_path)
            if not image_base64:
                return {"error": "Falha ao carregar imagem"}
            
            # Usa prompt personalizado ou padrão
            prompt = custom_prompt or config.SYSTEM_PROMPT
            
            # Monta a requisição
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 2000,
                "temperature": 0.1,  # Baixa temperatura para respostas mais consistentes
                "top_p": 0.9,
                "stream": False
            }
            
            # Faz a requisição
            start_time = time.time()
            response = self.session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                timeout=30
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                
                # Extrai a resposta
                if 'choices' in result and len(result['choices']) > 0:
                    content = result['choices'][0]['message']['content']
                    
                    return {
                        "success": True,
                        "content": content,
                        "response_time": response_time,
                        "tokens_used": result.get('usage', {}).get('total_tokens', 0),
                        "model": self.model
                    }
                else:
                    return {"error": "Resposta inválida da API"}
            
            else:
                error_msg = f"Erro HTTP {response.status_code}: {response.text}"
                return {"error": error_msg}
                
        except requests.exceptions.Timeout:
            return {"error": "Timeout na requisição - verifique sua conexão"}
        except requests.exceptions.ConnectionError:
            return {"error": "Erro de conexão - verifique sua internet"}
        except Exception as e:
            return {"error": f"Erro inesperado: {str(e)}"}
    
    def _encode_image(self, image_path: str) -> Optional[str]:
        """
        Codifica imagem para base64
        
        Args:
            image_path: Caminho para a imagem
            
        Returns:
            String base64 ou None se erro
        """
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            print(f"Erro ao codificar imagem: {e}")
            return None
    
    def analyze_text_only(self, text: str, context: str = "questão acadêmica") -> Dict[str, Any]:
        """
        Analisa apenas texto (para casos onde OCR já foi feito)
        
        Args:
            text: Texto a ser analisado
            context: Contexto da análise
            
        Returns:
            Dicionário com a resposta da API
        """
        try:
            prompt = f"""Como assistente acadêmico, analise o seguinte {context}:

{text}

Forneça uma análise completa e resolução passo a passo."""

            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 1500,
                "temperature": 0.1,
                "stream": False
            }
            
            response = self.session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                timeout=25
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                return {
                    "success": True,
                    "content": content,
                    "tokens_used": result.get('usage', {}).get('total_tokens', 0)
                }
            else:
                return {"error": f"Erro HTTP {response.status_code}"}
                
        except Exception as e:
            return {"error": f"Erro na análise de texto: {str(e)}"}
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Testa a conexão com a API
        
        Returns:
            Dicionário com resultado do teste
        """
        try:
            # Teste simples
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": "Responda apenas 'OK' se você está funcionando."
                    }
                ],
                "max_tokens": 10,
                "temperature": 0
            }
            
            response = self.session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'choices' in result:
                    return {
                        "success": True,
                        "message": "Conexão com API estabelecida",
                        "model": self.model
                    }
            
            return {
                "success": False,
                "error": f"Teste falhou: HTTP {response.status_code}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Erro no teste de conexão: {str(e)}"
            }
    
    def get_available_models(self) -> Dict[str, Any]:
        """
        Obtém lista de modelos disponíveis
        
        Returns:
            Dicionário com modelos disponíveis
        """
        try:
            response = self.session.get(f"{self.base_url}/models", timeout=10)
            
            if response.status_code == 200:
                models = response.json()
                return {
                    "success": True,
                    "models": models.get('data', [])
                }
            else:
                return {"error": f"Erro ao obter modelos: HTTP {response.status_code}"}
                
        except Exception as e:
            return {"error": f"Erro ao listar modelos: {str(e)}"}
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estima o número de tokens em um texto
        
        Args:
            text: Texto para estimar
            
        Returns:
            Número estimado de tokens
        """
        # Estimativa simples: ~4 caracteres por token para português
        return len(text) // 4
    
    def format_response_for_display(self, response_content: str) -> str:
        """
        Formata a resposta da API para exibição otimizada
        
        Args:
            response_content: Conteúdo da resposta da API
            
        Returns:
            Texto formatado para exibição
        """
        # Remove quebras de linha excessivas
        formatted = response_content.strip()
        
        # Adiciona marcadores para melhor legibilidade
        if "Resposta:" in formatted:
            formatted = formatted.replace("Resposta:", "🎯 RESPOSTA:")
        
        if "Alternativa" in formatted or "alternativa" in formatted:
            formatted = formatted.replace("Alternativa", "✅ Alternativa")
        
        # Limita o tamanho se muito longo
        if len(formatted) > config.MAX_TEXT_LENGTH:
            formatted = formatted[:config.MAX_TEXT_LENGTH] + "...\n\n[Resposta truncada]"
        
        return formatted 