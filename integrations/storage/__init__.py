"""Storage integration adapters."""
try:
    from .s3_adapter import S3Adapter
except Exception:
    S3Adapter = None

try:
    from .cloudinary_adapter import CloudinaryAdapter
except Exception:
    CloudinaryAdapter = None

__all__ = ['S3Adapter', 'CloudinaryAdapter']
