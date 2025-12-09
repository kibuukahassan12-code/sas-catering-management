"""Africa's Talking SMS/WhatsApp adapter."""
import os
from typing import Dict, Optional
from flask import current_app

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    requests = None


class AfricasTalkingAdapter:
    """Africa's Talking communication adapter."""
    
    def __init__(self):
        self.api_key = os.getenv('AFRICASTALKING_API_KEY', '')
        self.username = os.getenv('AFRICASTALKING_USERNAME', '')
        self.sender_id = os.getenv('AFRICASTALKING_SENDER_ID', 'SASFOODS')
        self.base_url = 'https://api.africastalking.com/version1'
        self.mock_mode = os.getenv('INTEGRATIONS_MOCK', 'false').lower() == 'true'
        self.enabled = bool(self.api_key and self.username) and not self.mock_mode
        
        if not self.enabled and current_app:
            current_app.logger.warning(
                "Africa's Talking adapter disabled. Using mock mode." if self.mock_mode else ""
            )
    
    def send_sms(
        self,
        to: str,
        message: str,
        bulk_sms_mode: int = 0
    ) -> Dict[str, any]:
        """
        Send SMS via Africa's Talking.
        
        Args:
            to: Recipient phone number (international format)
            message: Message text
            bulk_sms_mode: 0 for single, 1 for bulk
            
        Returns:
            Dict with 'success', 'message_id', 'error'
        """
        if not REQUESTS_AVAILABLE:
            return {'success': False, 'error': 'requests library not installed'}
        
        if self.mock_mode or not self.enabled:
            return {
                'success': True,
                'message_id': f'AT{os.urandom(12).hex()}',
                'status': 'sent',
                'mock': True
            }
        
        try:
            url = f'{self.base_url}/messaging'
            headers = {
                'ApiKey': self.api_key,
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json'
            }
            
            data = {
                'username': self.username,
                'to': to,
                'message': message,
                'from': self.sender_id,
                'bulkSMSMode': bulk_sms_mode
            }
            
            response = requests.post(url, data=data, headers=headers, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            if result.get('SMSMessageData', {}).get('Recipients'):
                recipient = result['SMSMessageData']['Recipients'][0]
                return {
                    'success': recipient.get('statusCode') == 101,
                    'message_id': recipient.get('messageId', ''),
                    'status': recipient.get('status', ''),
                    'cost': recipient.get('cost', ''),
                    'mock': False
                }
            else:
                return {'success': False, 'error': 'No recipients in response'}
        except requests.RequestException as e:
            if current_app:
                current_app.logger.error(f"Africa's Talking API error: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            if current_app:
                current_app.logger.exception(f"Africa's Talking adapter error: {e}")
            return {'success': False, 'error': str(e)}
    
    def send_whatsapp(
        self,
        to: str,
        message: str,
        media_url: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Send WhatsApp message via Africa's Talking.
        
        Args:
            to: Recipient phone number
            message: Message text
            media_url: Optional media URL
            
        Returns:
            Dict with 'success', 'message_id', 'error'
        """
        if self.mock_mode or not self.enabled:
            return {
                'success': True,
                'message_id': f'WA{os.urandom(12).hex()}',
                'status': 'sent',
                'mock': True
            }
        
        try:
            # Africa's Talking WhatsApp API endpoint
            url = f'{self.base_url}/whatsapp/message'
            headers = {
                'ApiKey': self.api_key,
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            payload = {
                'username': self.username,
                'to': to,
                'message': message
            }
            
            if media_url:
                payload['mediaUrl'] = media_url
            
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            return {
                'success': result.get('status') == 'Success',
                'message_id': result.get('messageId', ''),
                'status': result.get('status', ''),
                'mock': False
            }
        except Exception as e:
            if current_app:
                current_app.logger.exception(f"Africa's Talking WhatsApp error: {e}")
            return {'success': False, 'error': str(e)}

