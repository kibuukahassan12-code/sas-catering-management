"""Flutterwave payment integration adapter."""
import os
from typing import Dict, Optional, Any
from flask import current_app

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    requests = None


class FlutterwaveAdapter:
    """Flutterwave payment processor adapter."""
    
    def __init__(self):
        self.public_key = os.getenv('FLUTTERWAVE_PUBLIC_KEY', '')
        self.secret_key = os.getenv('FLUTTERWAVE_SECRET_KEY', '')
        self.base_url = 'https://api.flutterwave.com/v3'
        self.mock_mode = os.getenv('INTEGRATIONS_MOCK', 'false').lower() == 'true'
        self.enabled = bool(self.secret_key) and not self.mock_mode
        
        if not self.enabled and current_app:
            current_app.logger.warning(
                "Flutterwave adapter disabled. Using mock mode." if self.mock_mode else ""
            )
    
    def create_payment(
        self,
        amount: float,
        currency: str = 'UGX',
        email: str = '',
        phone: str = '',
        tx_ref: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a Flutterwave payment."""
        if not REQUESTS_AVAILABLE:
            return {'success': False, 'error': 'requests library not installed'}
        
        if self.mock_mode or not self.enabled:
            return {
                'success': True,
                'payment_link': f'https://checkout.flutterwave.com/mock/{os.urandom(8).hex()}',
                'tx_ref': tx_ref or f'tx_{os.urandom(8).hex()}',
                'mock': True
            }
        
        try:
            import secrets
            tx_ref = tx_ref or f'tx_{secrets.token_hex(8)}'
            
            payload = {
                'tx_ref': tx_ref,
                'amount': str(amount),
                'currency': currency,
                'payment_options': 'card,mobilemoney,ussd',
                'redirect_url': os.getenv('FLUTTERWAVE_REDIRECT_URL', ''),
                'customer': {
                    'email': email,
                    'phonenumber': phone
                },
                'meta': metadata or {}
            }
            
            headers = {
                'Authorization': f'Bearer {self.secret_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                f'{self.base_url}/payments',
                json=payload,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') == 'success':
                return {
                    'success': True,
                    'payment_link': data['data']['link'],
                    'tx_ref': tx_ref,
                    'mock': False
                }
            else:
                return {
                    'success': False,
                    'error': data.get('message', 'Payment creation failed')
                }
        except requests.RequestException as e:
            if current_app:
                current_app.logger.error(f"Flutterwave API error: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            if current_app:
                current_app.logger.exception(f"Flutterwave adapter error: {e}")
            return {'success': False, 'error': str(e)}
    
    def verify_transaction(self, tx_ref: str) -> Dict[str, Any]:
        """Verify a Flutterwave transaction."""
        if self.mock_mode or not self.enabled:
            return {
                'success': True,
                'status': 'successful',
                'mock': True
            }
        
        try:
            headers = {'Authorization': f'Bearer {self.secret_key}'}
            response = requests.get(
                f'{self.base_url}/transactions/{tx_ref}/verify',
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') == 'success':
                tx_data = data.get('data', {})
                return {
                    'success': True,
                    'status': tx_data.get('status', 'unknown'),
                    'amount': float(tx_data.get('amount', 0)),
                    'currency': tx_data.get('currency', ''),
                    'mock': False
                }
            else:
                return {'success': False, 'error': data.get('message', 'Verification failed')}
        except Exception as e:
            return {'success': False, 'error': str(e)}

