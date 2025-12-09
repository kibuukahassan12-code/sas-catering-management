"""Cloudinary storage integration adapter."""
import os
from typing import Dict, Optional
from flask import current_app

try:
    import cloudinary
    import cloudinary.uploader
    CLOUDINARY_AVAILABLE = True
except ImportError:
    CLOUDINARY_AVAILABLE = False
    cloudinary = None


class CloudinaryAdapter:
    """Cloudinary storage adapter."""
    
    def __init__(self):
        self.cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME', '')
        self.api_key = os.getenv('CLOUDINARY_API_KEY', '')
        self.api_secret = os.getenv('CLOUDINARY_API_SECRET', '')
        self.mock_mode = os.getenv('INTEGRATIONS_MOCK', 'false').lower() == 'true'
        
        if CLOUDINARY_AVAILABLE and self.cloud_name and self.api_key and self.api_secret and not self.mock_mode:
            cloudinary.config(
                cloud_name=self.cloud_name,
                api_key=self.api_key,
                api_secret=self.api_secret
            )
            self.enabled = True
        else:
            self.enabled = False
            if current_app:
                current_app.logger.warning(
                    "Cloudinary adapter disabled. Using mock mode." if self.mock_mode else ""
                )
    
    def upload_file(
        self,
        file_path: str,
        folder: str = 'sas-best-foods',
        public_id: Optional[str] = None,
        resource_type: str = 'auto'
    ) -> Dict[str, any]:
        """
        Upload file to Cloudinary.
        
        Args:
            file_path: Local file path
            folder: Cloudinary folder
            public_id: Optional public ID
            resource_type: auto, image, video, raw
            
        Returns:
            Dict with 'success', 'url', 'public_id', 'error'
        """
        if self.mock_mode or not self.enabled:
            return {
                'success': True,
                'url': f'https://res.cloudinary.com/{self.cloud_name}/mock/{folder}/{public_id or "file"}',
                'public_id': public_id or 'mock_file',
                'secure_url': f'https://res.cloudinary.com/{self.cloud_name}/mock/{folder}/{public_id or "file"}',
                'mock': True
            }
        
        try:
            result = cloudinary.uploader.upload(
                file_path,
                folder=folder,
                public_id=public_id,
                resource_type=resource_type
            )
            
            return {
                'success': True,
                'url': result.get('url', ''),
                'secure_url': result.get('secure_url', ''),
                'public_id': result.get('public_id', ''),
                'format': result.get('format', ''),
                'bytes': result.get('bytes', 0),
                'mock': False
            }
        except Exception as e:
            if current_app:
                current_app.logger.exception(f"Cloudinary upload error: {e}")
            return {'success': False, 'error': str(e)}
    
    def delete_file(self, public_id: str) -> Dict[str, any]:
        """Delete file from Cloudinary."""
        if self.mock_mode or not self.enabled:
            return {'success': True, 'mock': True}
        
        try:
            result = cloudinary.uploader.destroy(public_id)
            return {
                'success': result.get('result') == 'ok',
                'mock': False
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

