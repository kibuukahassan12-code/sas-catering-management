"""WhatsApp integration via Twilio adapter."""
import os
from typing import Dict, Optional, List
from flask import current_app

try:
    from twilio.rest import Client as TwilioClient
    from twilio.base.exceptions import TwilioRestException
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    TwilioClient = None
    TwilioRestException = Exception


class WhatsAppTwilioAdapter:
    """WhatsApp messaging via Twilio adapter."""
    
    def __init__(self):
        self.account_sid = os.getenv('TWILIO_SID', '')
        self.auth_token = os.getenv('TWILIO_TOKEN', '')
        self.whatsapp_from = os.getenv('TWILIO_WHATSAPP_FROM', 'whatsapp:+14155238886')  # Twilio sandbox
        self.mock_mode = os.getenv('INTEGRATIONS_MOCK', 'false').lower() == 'true'
        
        if TWILIO_AVAILABLE and self.account_sid and self.auth_token and not self.mock_mode:
            self.client = TwilioClient(self.account_sid, self.auth_token)
            self.enabled = True
        else:
            self.client = None
            self.enabled = False
            if current_app:
                current_app.logger.warning(
                    "Twilio WhatsApp adapter disabled. Using mock mode." if self.mock_mode else ""
                )
    
    def send_whatsapp_message(
        self,
        to: str,
        message: str,
        media_url: Optional[str] = None,
        template: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Send WhatsApp message via Twilio.
        
        Args:
            to: Recipient phone number (E.164 format, e.g., +256771234567)
            message: Message text
            media_url: Optional media URL
            template: Optional template name (for approved templates)
            
        Returns:
            Dict with 'success', 'message_sid', 'error'
        """
        if self.mock_mode or not self.enabled:
            return {
                'success': True,
                'message_sid': f'SM{os.urandom(16).hex()}',
                'status': 'queued',
                'mock': True,
                'message': 'Mock WhatsApp message sent (Twilio not configured)'
            }
        
        try:
            # Ensure 'whatsapp:' prefix
            to_number = to if to.startswith('whatsapp:') else f'whatsapp:{to}'
            
            message_params = {
                'from': self.whatsapp_from,
                'to': to_number,
                'body': message
            }
            
            if media_url:
                message_params['media_url'] = [media_url]
            
            twilio_message = self.client.messages.create(**message_params)
            
            return {
                'success': True,
                'message_sid': twilio_message.sid,
                'status': twilio_message.status,
                'mock': False
            }
        except TwilioRestException as e:
            if current_app:
                current_app.logger.error(f"Twilio error: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': e.code if hasattr(e, 'code') else None
            }
        except Exception as e:
            if current_app:
                current_app.logger.exception(f"Unexpected error in Twilio adapter: {e}")
            return {'success': False, 'error': str(e)}
    
    def send_template_message(
        self,
        to: str,
        template_name: str,
        parameters: Optional[List[str]] = None
    ) -> Dict[str, any]:
        """
        Send WhatsApp template message (requires approved template).
        
        Args:
            to: Recipient phone number
            template_name: Approved template name
            parameters: List of template parameter values
            
        Returns:
            Dict with 'success', 'message_sid', 'error'
        """
        if self.mock_mode or not self.enabled:
            return {
                'success': True,
                'message_sid': f'SM{os.urandom(16).hex()}',
                'status': 'queued',
                'mock': True
            }
        
        try:
            to_number = to if to.startswith('whatsapp:') else f'whatsapp:{to}'
            
            # Twilio Content API for templates (requires Content SID)
            # For now, fallback to regular message
            message = f"Template: {template_name}"
            if parameters:
                message += f" | Params: {', '.join(parameters)}"
            
            return self.send_whatsapp_message(to_number, message)
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_message_status(self, message_sid: str) -> Dict[str, any]:
        """Get status of a sent message."""
        if self.mock_mode or not self.enabled:
            return {
                'success': True,
                'status': 'delivered',
                'mock': True
            }
        
        try:
            message = self.client.messages(message_sid).fetch()
            return {
                'success': True,
                'status': message.status,
                'date_sent': str(message.date_sent) if message.date_sent else None,
                'mock': False
            }
        except TwilioRestException as e:
            return {'success': False, 'error': str(e)}
        except Exception as e:
            return {'success': False, 'error': str(e)}

