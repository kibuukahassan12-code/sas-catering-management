"""AWS S3 storage integration adapter."""
import os
from typing import Dict, Optional
from flask import current_app

try:
    import boto3
    from botocore.exceptions import ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    boto3 = None
    ClientError = Exception


class S3Adapter:
    """AWS S3 storage adapter."""
    
    def __init__(self):
        self.access_key = os.getenv('AWS_ACCESS_KEY_ID', '')
        self.secret_key = os.getenv('AWS_SECRET_ACCESS_KEY', '')
        self.bucket_name = os.getenv('AWS_S3_BUCKET', 'sas-best-foods')
        self.region = os.getenv('AWS_REGION', 'us-east-1')
        self.mock_mode = os.getenv('INTEGRATIONS_MOCK', 'false').lower() == 'true'
        
        if BOTO3_AVAILABLE and self.access_key and self.secret_key and not self.mock_mode:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=self.region
            )
            self.enabled = True
        else:
            self.s3_client = None
            self.enabled = False
            if current_app:
                current_app.logger.warning(
                    "S3 adapter disabled. Using mock mode." if self.mock_mode else ""
                )
    
    def upload_file(
        self,
        file_path: str,
        s3_key: str,
        content_type: Optional[str] = None,
        public: bool = False
    ) -> Dict[str, any]:
        """
        Upload file to S3.
        
        Args:
            file_path: Local file path
            s3_key: S3 object key (path)
            content_type: MIME type
            public: Whether to make file publicly accessible
            
        Returns:
            Dict with 'success', 'url', 's3_key', 'error'
        """
        if self.mock_mode or not self.enabled:
            return {
                'success': True,
                'url': f'https://{self.bucket_name}.s3.{self.region}.amazonaws.com/mock/{s3_key}',
                's3_key': s3_key,
                'mock': True
            }
        
        try:
            extra_args = {}
            if content_type:
                extra_args['ContentType'] = content_type
            if public:
                extra_args['ACL'] = 'public-read'
            
            self.s3_client.upload_file(
                file_path,
                self.bucket_name,
                s3_key,
                ExtraArgs=extra_args
            )
            
            url = f'https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{s3_key}'
            
            return {
                'success': True,
                'url': url,
                's3_key': s3_key,
                'mock': False
            }
        except ClientError as e:
            if current_app:
                current_app.logger.error(f"S3 upload error: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            if current_app:
                current_app.logger.exception(f"S3 adapter error: {e}")
            return {'success': False, 'error': str(e)}
    
    def generate_presigned_url(
        self,
        s3_key: str,
        expiration: int = 3600
    ) -> Dict[str, any]:
        """
        Generate presigned URL for temporary access.
        
        Args:
            s3_key: S3 object key
            expiration: URL expiration in seconds (default: 1 hour)
            
        Returns:
            Dict with 'success', 'url', 'error'
        """
        if self.mock_mode or not self.enabled:
            return {
                'success': True,
                'url': f'https://{self.bucket_name}.s3.{self.region}.amazonaws.com/mock/{s3_key}?presigned=mock',
                'expires_in': expiration,
                'mock': True
            }
        
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=expiration
            )
            
            return {
                'success': True,
                'url': url,
                'expires_in': expiration,
                'mock': False
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def delete_file(self, s3_key: str) -> Dict[str, any]:
        """Delete file from S3."""
        if self.mock_mode or not self.enabled:
            return {'success': True, 'mock': True}
        
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            return {'success': True, 'mock': False}
        except Exception as e:
            return {'success': False, 'error': str(e)}

