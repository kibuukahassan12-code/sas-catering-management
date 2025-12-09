"""MTN Mobile Money payment integration adapter."""
import os
import base64
import uuid
from typing import Dict, Optional, Any
from flask import current_app

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    requests = None


class MTMoMoAdapter:
    """MTN Mobile Money payment processor adapter."""
    
    def __init__(self):
        self.api_key = os.getenv('MTNMOMO_KEY', '')
        self.user_id = os.getenv('MTNMOMO_USER_ID', '')
        self.subscription_key = os.getenv('MTNMOMO_SUBSCRIPTION_KEY', '')
        self.environment = os.getenv('MTNMOMO_ENV', 'sandbox')  # sandbox or production
        self.mock_mode = os.getenv('INTEGRATIONS_MOCK', 'false').lower() == 'true'
        
        if self.environment == 'sandbox':
            self.base_url = 'https://sandbox.momodeveloper.mtn.com'
        else:
            self.base_url = 'https://api.momodeveloper.mtn.com'
        
        self.enabled = bool(self.api_key and self.user_id and self.subscription_key) and not self.mock_mode
        
        if not self.enabled and current_app:
            current_app.logger.warning(
                "MTN MoMo adapter disabled. Using mock mode." if self.mock_mode else ""
            )
    
    def request_to_pay(
        self,
        amount: float,
        currency: str = 'EUR',
        external_id: Optional[str] = None,
        payer_message: str = '',
        payee_note: str = ''
    ) -> Dict[str, Any]:
        """Request payment from customer via MTN Mobile Money."""
        if not REQUESTS_AVAILABLE:
            return {'success': False, 'error': 'requests library not installed'}
        
        if self.mock_mode or not self.enabled:
            return {
                'success': True,
                'transaction_id': f'momo_{uuid.uuid4().hex[:16]}',
                'status': 'PENDING',
                'mock': True
            }
        
        try:
            transaction_id = str(uuid.uuid4())
            external_id = external_id or transaction_id
            
            payload = {
                'amount': str(amount),
                'currency': currency,
                'externalId': external_id,
                'payer': {
                    'partyIdType': 'MSISDN',
                    'partyId': ''  # Should be provided by caller
                },
                'payerMessage': payer_message,
                'payeeNote': payee_note
            }
            
            # Create authorization token
            auth_string = f"{self.user_id}:{self.api_key}"
            auth_token = base64.b64encode(auth_string.encode()).decode()
            
            headers = {
                'Authorization': f'Basic {auth_token}',
                'X-Target-Environment': self.environment,
                'X-Reference-Id': transaction_id,
                'Content-Type': 'application/json',
                'Ocp-Apim-Subscription-Key': self.subscription_key
            }
            
            response = requests.post(
                f'{self.base_url}/collection/v1_0/requesttopay',
                json=payload,
                headers=headers,
                timeout=10
            )
            
            if response.status_code in [200, 202]:
                return {
                    'success': True,
                    'transaction_id': transaction_id,
                    'status': 'PENDING',
                    'mock': False
                }
            else:
                return {
                    'success': False,
                    'error': f"API returned {response.status_code}: {response.text}"
                }
        except requests.RequestException as e:
            if current_app:
                current_app.logger.error(f"MTN MoMo API error: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            if current_app:
                current_app.logger.exception(f"MTN MoMo adapter error: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_transaction_status(self, transaction_id: str) -> Dict[str, Any]:
        """Get status of a payment transaction."""
        if self.mock_mode or not self.enabled:
            return {
                'success': True,
                'status': 'SUCCESSFUL',
                'mock': True
            }
        
        try:
            auth_string = f"{self.user_id}:{self.api_key}"
            auth_token = base64.b64encode(auth_string.encode()).decode()
            
            headers = {
                'Authorization': f'Basic {auth_token}',
                'X-Target-Environment': self.environment,
                'Ocp-Apim-Subscription-Key': self.subscription_key
            }
            
            response = requests.get(
                f'{self.base_url}/collection/v1_0/requesttopay/{transaction_id}',
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                'success': True,
                'status': data.get('status', 'UNKNOWN'),
                'amount': float(data.get('amount', 0)),
                'currency': data.get('currency', ''),
                'mock': False
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

