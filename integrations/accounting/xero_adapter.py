"""Xero accounting integration adapter."""
import os
from typing import Dict, Optional, Any
from flask import current_app

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    requests = None


class XeroAdapter:
    """Xero accounting adapter."""
    
    def __init__(self):
        self.client_id = os.getenv('XERO_CLIENT_ID', '')
        self.client_secret = os.getenv('XERO_CLIENT_SECRET', '')
        self.access_token = os.getenv('XERO_ACCESS_TOKEN', '')
        self.tenant_id = os.getenv('XERO_TENANT_ID', '')
        self.base_url = 'https://api.xero.com/api.xro/2.0'
        self.mock_mode = os.getenv('INTEGRATIONS_MOCK', 'false').lower() == 'true'
        self.enabled = bool(self.access_token and self.tenant_id) and not self.mock_mode
        
        if not self.enabled and current_app:
            current_app.logger.warning(
                "Xero adapter disabled. Using mock mode." if self.mock_mode else ""
            )
    
    def push_invoice(self, invoice_obj: Dict[str, Any]) -> Dict[str, Any]:
        """Push invoice to Xero."""
        if self.mock_mode or not self.enabled:
            return {
                'success': True,
                'invoice_id': f'XERO{os.urandom(12).hex()}',
                'invoice_number': invoice_obj.get('invoice_number', ''),
                'mock': True
            }
        
        try:
            url = f'{self.base_url}/Invoices'
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Xero-tenant-id': self.tenant_id,
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
            
            xero_invoice = self._transform_invoice(invoice_obj)
            response = requests.post(url, json=xero_invoice, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            invoice = data.get('Invoices', [{}])[0]
            return {
                'success': True,
                'invoice_id': invoice.get('InvoiceID', ''),
                'invoice_number': invoice.get('InvoiceNumber', ''),
                'mock': False
            }
        except requests.RequestException as e:
            if current_app:
                current_app.logger.error(f"Xero API error: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            if current_app:
                current_app.logger.exception(f"Xero adapter error: {e}")
            return {'success': False, 'error': str(e)}
    
    def push_payment(self, payment_obj: Dict[str, Any]) -> Dict[str, Any]:
        """Push payment to Xero."""
        if self.mock_mode or not self.enabled:
            return {
                'success': True,
                'payment_id': f'XERO{os.urandom(12).hex()}',
                'mock': True
            }
        
        try:
            url = f'{self.base_url}/Payments'
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Xero-tenant-id': self.tenant_id,
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
            
            xero_payment = self._transform_payment(payment_obj)
            response = requests.post(url, json=xero_payment, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            payment = data.get('Payments', [{}])[0]
            return {
                'success': True,
                'payment_id': payment.get('PaymentID', ''),
                'mock': False
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def push_journal(self, journal_obj: Dict[str, Any]) -> Dict[str, Any]:
        """Push journal entry to Xero."""
        if self.mock_mode or not self.enabled:
            return {
                'success': True,
                'journal_id': f'XERO{os.urandom(12).hex()}',
                'mock': True
            }
        
        try:
            url = f'{self.base_url}/Journals'
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Xero-tenant-id': self.tenant_id,
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
            
            xero_journal = self._transform_journal(journal_obj)
            response = requests.post(url, json=xero_journal, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            journal = data.get('Journals', [{}])[0]
            return {
                'success': True,
                'journal_id': journal.get('JournalID', ''),
                'mock': False
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _transform_invoice(self, invoice: Dict[str, Any]) -> Dict[str, Any]:
        """Transform internal invoice format to Xero format."""
        return {
            'Type': 'ACCREC',
            'Contact': {'ContactID': invoice.get('customer_id', '')},
            'Date': invoice.get('date', ''),
            'DueDate': invoice.get('due_date', ''),
            'LineItems': [
                {
                    'Description': invoice.get('description', ''),
                    'Quantity': invoice.get('quantity', 1),
                    'UnitAmount': invoice.get('unit_amount', 0),
                    'AccountCode': invoice.get('account_code', '200')
                }
            ]
        }
    
    def _transform_payment(self, payment: Dict[str, Any]) -> Dict[str, Any]:
        """Transform internal payment format to Xero format."""
        return {
            'Invoice': {'InvoiceID': payment.get('invoice_id', '')},
            'Account': {'Code': payment.get('account_code', '090')},
            'Date': payment.get('date', ''),
            'Amount': payment.get('amount', 0)
        }
    
    def _transform_journal(self, journal: Dict[str, Any]) -> Dict[str, Any]:
        """Transform internal journal format to Xero format."""
        return {
            'JournalDate': journal.get('date', ''),
            'JournalLines': journal.get('lines', [])
        }

