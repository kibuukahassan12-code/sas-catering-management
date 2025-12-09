"""Paystack payment integration adapter."""
import os
from typing import Dict, Optional, Any
from flask import current_app

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    requests = None


class PaystackAdapter:
    """Paystack payment processor adapter."""
    
    def __init__(self):
        self.secret_key = os.getenv('PAYSTACK_SECRET_KEY', '')
        self.public_key = os.getenv('PAYSTACK_PUBLIC_KEY', '')
        self.base_url = 'https://api.paystack.co'
        self.mock_mode = os.getenv('INTEGRATIONS_MOCK', 'false').lower() == 'true'
        self.enabled = bool(self.secret_key) and not self.mock_mode
        
        if not self.enabled and current_app:
            current_app.logger.warning(
                "Paystack adapter disabled. Using mock mode." if self.mock_mode else ""
            )
    
    def initialize_transaction(
        self,
        amount: float,
        email: str,
        currency: str = 'NGN',
        reference: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Initialize a Paystack transaction."""
        if not REQUESTS_AVAILABLE:
            return {'success': False, 'error': 'requests library not installed'}
        
        if self.mock_mode or not self.enabled:
            import secrets
            ref = reference or f'ref_{secrets.token_hex(8)}'
            return {
                'success': True,
                'authorization_url': f'https://checkout.paystack.com/mock/{ref}',
                'access_code': f'acc_{os.urandom(8).hex()}',
                'reference': ref,
                'mock': True
            }
        
        try:
            import secrets
            ref = reference or f'ref_{secrets.token_hex(8)}'
            
            payload = {
                'email': email,
                'amount': int(amount * 100),  # Convert to kobo
                'currency': currency,
                'reference': ref,
                'metadata': metadata or {}
            }
            
            headers = {
                'Authorization': f'Bearer {self.secret_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                f'{self.base_url}/transaction/initialize',
                json=payload,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get('status'):
                return {
                    'success': True,
                    'authorization_url': data['data']['authorization_url'],
                    'access_code': data['data']['access_code'],
                    'reference': ref,
                    'mock': False
                }
            else:
                return {'success': False, 'error': data.get('message', 'Transaction initialization failed')}
        except requests.RequestException as e:
            if current_app:
                current_app.logger.error(f"Paystack API error: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            if current_app:
                current_app.logger.exception(f"Paystack adapter error: {e}")
            return {'success': False, 'error': str(e)}
    
    def verify_transaction(self, reference: str) -> Dict[str, Any]:
        """Verify a Paystack transaction."""
        if self.mock_mode or not self.enabled:
            return {
                'success': True,
                'status': 'success',
                'mock': True
            }
        
        try:
            headers = {'Authorization': f'Bearer {self.secret_key}'}
            response = requests.get(
                f'{self.base_url}/transaction/verify/{reference}',
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') and data.get('data', {}).get('status') == 'success':
                tx_data = data['data']
                return {
                    'success': True,
                    'status': 'success',
                    'amount': tx_data.get('amount', 0) / 100,
                    'currency': tx_data.get('currency', ''),
                    'mock': False
                }
            else:
                return {'success': False, 'error': 'Transaction verification failed'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

