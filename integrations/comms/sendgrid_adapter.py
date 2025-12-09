"""SendGrid email integration adapter."""
import os
from typing import Dict, Optional, List
from flask import current_app

try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail, Email, Content, Attachment
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False
    SendGridAPIClient = None
    Mail = None


class SendGridAdapter:
    """SendGrid transactional email adapter."""
    
    def __init__(self):
        self.api_key = os.getenv('SENDGRID_API_KEY', '')
        self.from_email = os.getenv('SENDGRID_FROM_EMAIL', 'noreply@sasbestfoods.com')
        self.from_name = os.getenv('SENDGRID_FROM_NAME', 'SAS Best Foods')
        self.mock_mode = os.getenv('INTEGRATIONS_MOCK', 'false').lower() == 'true'
        
        if SENDGRID_AVAILABLE and self.api_key and not self.mock_mode:
            self.client = SendGridAPIClient(self.api_key)
            self.enabled = True
        else:
            self.client = None
            self.enabled = False
            if current_app:
                current_app.logger.warning(
                    "SendGrid adapter disabled. Using mock mode." if self.mock_mode else ""
                )
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, any]:
        """
        Send transactional email via SendGrid.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email body
            text_content: Optional plain text version
            cc: Optional CC recipients
            bcc: Optional BCC recipients
            attachments: Optional list of attachments (dict with 'content', 'filename', 'type')
            
        Returns:
            Dict with 'success', 'message_id', 'error'
        """
        if self.mock_mode or not self.enabled:
            return {
                'success': True,
                'message_id': f'SG{os.urandom(16).hex()}',
                'status': 'queued',
                'mock': True,
                'message': 'Mock email sent (SendGrid not configured)'
            }
        
        try:
            message = Mail(
                from_email=Email(self.from_email, self.from_name),
                to_emails=to_email,
                subject=subject,
                html_content=Content("text/html", html_content)
            )
            
            if text_content:
                message.content = Content("text/plain", text_content)
            
            if cc:
                for email in cc:
                    message.add_cc(Email(email))
            
            if bcc:
                for email in bcc:
                    message.add_bcc(Email(email))
            
            if attachments:
                for att in attachments:
                    attachment = Attachment()
                    attachment.file_content = att.get('content')
                    attachment.file_name = att.get('filename', 'attachment')
                    attachment.file_type = att.get('type', 'application/octet-stream')
                    attachment.disposition = 'attachment'
                    message.add_attachment(attachment)
            
            response = self.client.send(message)
            
            return {
                'success': response.status_code in [200, 201, 202],
                'message_id': response.headers.get('X-Message-Id', ''),
                'status_code': response.status_code,
                'mock': False
            }
        except Exception as e:
            if current_app:
                current_app.logger.exception(f"SendGrid error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_template_email(
        self,
        to_email: str,
        template_id: str,
        template_data: Dict[str, any]
    ) -> Dict[str, any]:
        """
        Send email using SendGrid template.
        
        Args:
            to_email: Recipient email
            template_id: SendGrid template ID
            template_data: Template variable substitutions
            
        Returns:
            Dict with 'success', 'message_id', 'error'
        """
        if self.mock_mode or not self.enabled:
            return {
                'success': True,
                'message_id': f'SG{os.urandom(16).hex()}',
                'status': 'queued',
                'mock': True
            }
        
        try:
            message = Mail(
                from_email=Email(self.from_email, self.from_name),
                to_emails=to_email
            )
            message.template_id = template_id
            message.dynamic_template_data = template_data
            
            response = self.client.send(message)
            
            return {
                'success': response.status_code in [200, 201, 202],
                'message_id': response.headers.get('X-Message-Id', ''),
                'status_code': response.status_code,
                'mock': False
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

