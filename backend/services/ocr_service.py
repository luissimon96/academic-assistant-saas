"""
OCR Service with multiple providers
Tesseract (Free) → Google Vision → Azure CV
"""

import io
import base64
import time
from typing import Optional, List, Tuple
from PIL import Image
import pytesseract
import cv2
import numpy as np

try:
    from google.cloud import vision
    GOOGLE_VISION_AVAILABLE = True
except ImportError:
    GOOGLE_VISION_AVAILABLE = False

try:
    from azure.cognitiveservices.vision.computervision import ComputerVisionClient
    from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
    from msrest.authentication import CognitiveServicesCredentials
    AZURE_CV_AVAILABLE = True
except ImportError:
    AZURE_CV_AVAILABLE = False

from ..models import OCRResult, OCRProvider
from ..config import settings

class OCRService:
    """
    Multi-provider OCR service with intelligent fallback
    """
    
    def __init__(self):
        self.tesseract_config = '--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ+-*/=()[]{}.,;:!?ÀÁÂÃÄÅÇÈÉÊËÌÍÎÏÑÒÓÔÕÖÙÚÛÜÝàáâãäåçèéêëìíîïñòóôõöùúûüý'
        self._google_client = None
        self._azure_client = None
        
    def _get_google_client(self):
        """Initialize Google Vision client lazily"""
        if not GOOGLE_VISION_AVAILABLE or not settings.google_vision_api_key:
            return None
            
        if not self._google_client:
            # Set the API key as environment variable for Google client
            import os
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = settings.google_vision_api_key
            self._google_client = vision.ImageAnnotatorClient()
        return self._google_client
    
    def _get_azure_client(self):
        """Initialize Azure CV client lazily"""
        if not AZURE_CV_AVAILABLE or not settings.azure_cv_endpoint or not settings.azure_cv_key:
            return None
            
        if not self._azure_client:
            self._azure_client = ComputerVisionClient(
                settings.azure_cv_endpoint,
                CognitiveServicesCredentials(settings.azure_cv_key)
            )
        return self._azure_client
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocess image for better OCR results
        """
        # Convert to OpenCV format
        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Convert to grayscale
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
        
        # Apply denoising
        denoised = cv2.fastNlMeansDenoising(gray)
        
        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        # Convert back to PIL Image
        return Image.fromarray(thresh)
    
    def _extract_with_tesseract(self, image: Image.Image) -> OCRResult:
        """
        Extract text using Tesseract OCR
        """
        start_time = time.time()
        
        try:
            # Preprocess image
            processed_image = self._preprocess_image(image)
            
            # Extract text
            text = pytesseract.image_to_string(processed_image, config=self.tesseract_config)
            
            # Get confidence scores
            data = pytesseract.image_to_data(processed_image, output_type=pytesseract.Output.DICT)
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            processing_time = time.time() - start_time
            
            return OCRResult(
                provider=OCRProvider.TESSERACT,
                text=text.strip(),
                confidence=avg_confidence / 100.0,  # Convert to 0-1 scale
                processing_time=processing_time,
                success=True
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            return OCRResult(
                provider=OCRProvider.TESSERACT,
                text="",
                confidence=0.0,
                processing_time=processing_time,
                success=False,
                error=str(e)
            )
    
    def _extract_with_google_vision(self, image: Image.Image) -> Optional[OCRResult]:
        """
        Extract text using Google Vision API
        """
        client = self._get_google_client()
        if not client:
            return None
            
        start_time = time.time()
        
        try:
            # Convert PIL image to bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            image_bytes = img_byte_arr.getvalue()
            
            # Prepare the image for Google Vision
            vision_image = vision.Image(content=image_bytes)
            
            # Perform OCR
            response = client.text_detection(image=vision_image)
            
            if response.error.message:
                raise Exception(response.error.message)
            
            # Extract text and confidence
            texts = response.text_annotations
            if texts:
                full_text = texts[0].description
                # Google Vision doesn't provide per-word confidence, so we estimate
                confidence = 0.95  # Google Vision is typically very accurate
            else:
                full_text = ""
                confidence = 0.0
            
            processing_time = time.time() - start_time
            
            return OCRResult(
                provider=OCRProvider.GOOGLE_VISION,
                text=full_text.strip(),
                confidence=confidence,
                processing_time=processing_time,
                success=True
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            return OCRResult(
                provider=OCRProvider.GOOGLE_VISION,
                text="",
                confidence=0.0,
                processing_time=processing_time,
                success=False,
                error=str(e)
            )
    
    def _extract_with_azure_cv(self, image: Image.Image) -> Optional[OCRResult]:
        """
        Extract text using Azure Computer Vision
        """
        client = self._get_azure_client()
        if not client:
            return None
            
        start_time = time.time()
        
        try:
            # Convert PIL image to bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            image_bytes = img_byte_arr.getvalue()
            
            # Start OCR operation
            read_response = client.read_in_stream(
                io.BytesIO(image_bytes), 
                raw=True
            )
            
            # Get operation location
            operation_location = read_response.headers["Operation-Location"]
            operation_id = operation_location.split("/")[-1]
            
            # Wait for completion
            while True:
                read_result = client.get_read_result(operation_id)
                if read_result.status not in ['notStarted', 'running']:
                    break
                time.sleep(0.1)
            
            # Extract text
            text_lines = []
            if read_result.status == OperationStatusCodes.succeeded:
                for text_result in read_result.analyze_result.read_results:
                    for line in text_result.lines:
                        text_lines.append(line.text)
            
            full_text = "\n".join(text_lines)
            confidence = 0.93  # Azure CV is also typically very accurate
            
            processing_time = time.time() - start_time
            
            return OCRResult(
                provider=OCRProvider.AZURE_CV,
                text=full_text.strip(),
                confidence=confidence,
                processing_time=processing_time,
                success=True
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            return OCRResult(
                provider=OCRProvider.AZURE_CV,
                text="",
                confidence=0.0,
                processing_time=processing_time,
                success=False,
                error=str(e)
            )
    
    def extract_text(self, image_data: str, plan: str = "free") -> OCRResult:
        """
        Extract text from image using the best available provider for the user's plan
        
        Args:
            image_data: Base64 encoded image
            plan: User's subscription plan (free, pro, max)
            
        Returns:
            OCRResult with extracted text and metadata
        """
        try:
            # Decode base64 image
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Get available providers based on plan
            from ..config import OCR_ROUTING
            available_providers = OCR_ROUTING.get(plan, ['tesseract'])
            
            # Try providers in order of preference
            best_result = None
            
            for provider in available_providers:
                if provider == 'google_vision' and GOOGLE_VISION_AVAILABLE:
                    result = self._extract_with_google_vision(image)
                    if result and result.success and result.confidence > 0.8:
                        return result
                    if result and result.success:
                        best_result = result
                        
                elif provider == 'azure_cv' and AZURE_CV_AVAILABLE:
                    result = self._extract_with_azure_cv(image)
                    if result and result.success and result.confidence > 0.8:
                        return result
                    if result and result.success:
                        best_result = result
                        
                elif provider == 'tesseract':
                    result = self._extract_with_tesseract(image)
                    if not best_result or (result.success and result.confidence > best_result.confidence):
                        best_result = result
            
            return best_result or OCRResult(
                provider=OCRProvider.TESSERACT,
                text="",
                confidence=0.0,
                processing_time=0.0,
                success=False,
                error="No OCR providers available"
            )
            
        except Exception as e:
            return OCRResult(
                provider=OCRProvider.TESSERACT,
                text="",
                confidence=0.0,
                processing_time=0.0,
                success=False,
                error=f"Image processing error: {str(e)}"
            )

# Global instance
ocr_service = OCRService() 