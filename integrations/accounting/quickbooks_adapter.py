"""QuickBooks accounting integration adapter."""
import os
from typing import Dict, Optional, Any
from flask import current_app

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    requests = None


class QuickBooksAdapter:
    """QuickBooks Online accounting adapter."""
    
    def __init__(self):
        self.client_id = os.getenv('QUICKBOOKS_CLIENT_ID', '')
        self.client_secret = os.getenv('QUICKBOOKS_CLIENT_SECRET', '')
        self.access_token = os.getenv('QUICKBOOKS_ACCESS_TOKEN', '')
        self.realm_id = os.getenv('QUICKBOOKS_REALM_ID', '')
        self.sandbox = os.getenv('QUICKBOOKS_SANDBOX', 'true').lower() == 'true'
        self.mock_mode = os.getenv('INTEGRATIONS_MOCK', 'false').lower() == 'true'
        
        if self.sandbox:
            self.base_url = 'https://sandbox-quickbooks.api.intuit.com'
        else:
            self.base_url = 'https://quickbooks.api.intuit.com'
        
        self.enabled = bool(self.access_token and self.realm_id) and not self.mock_mode
        
        if not self.enabled and current_app:
            current_app.logger.warning(
                "QuickBooks adapter disabled. Using mock mode." if self.mock_mode else ""
            )
    
    def push_invoice(self, invoice_obj: Dict[str, Any]) -> Dict[str, Any]:
        """
        Push invoice to QuickBooks.
        
        Args:
            invoice_obj: Dict with invoice data (customer, items, amount, etc.)
            
        Returns:
            Dict with 'success', 'invoice_id', 'error'
        """
        if self.mock_mode or not self.enabled:
            return {
                'success': True,
                'invoice_id': f'QB{os.urandom(12).hex()}',
                'sync_token': '0',
                'mock': True
            }
        
        try:
            url = f'{self.base_url}/v3/company/{self.realm_id}/invoice'
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
            
            # Transform invoice_obj to QuickBooks format
            qb_invoice = self._transform_invoice(invoice_obj)
            
            response = requests.post(url, json=qb_invoice, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            invoice = data.get('QueryResponse', {}).get('Invoice', [{}])[0]
            if invoice:
                return {
                    'success': True,
                    'invoice_id': invoice.get('Id', ''),
                    'sync_token': invoice.get('SyncToken', ''),
                    'doc_number': invoice.get('DocNumber', ''),
                    'mock': False
                }
            else:
                return {'success': False, 'error': 'No invoice in response'}
        except requests.RequestException as e:
            if current_app:
                current_app.logger.error(f"QuickBooks API error: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            if current_app:
                current_app.logger.exception(f"QuickBooks adapter error: {e}")
            return {'success': False, 'error': str(e)}
    
    def push_payment(self, payment_obj: Dict[str, Any]) -> Dict[str, Any]:
        """Push payment to QuickBooks."""
        if self.mock_mode or not self.enabled:
            return {
                'success': True,
                'payment_id': f'QB{os.urandom(12).hex()}',
                'mock': True
            }
        
        try:
            url = f'{self.base_url}/v3/company/{self.realm_id}/payment'
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
            
            qb_payment = self._transform_payment(payment_obj)
            response = requests.post(url, json=qb_payment, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            payment = data.get('QueryResponse', {}).get('Payment', [{}])[0]
            return {
                'success': True,
                'payment_id': payment.get('Id', ''),
                'mock': False
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def push_journal(self, journal_obj: Dict[str, Any]) -> Dict[str, Any]:
        """Push journal entry to QuickBooks."""
        if self.mock_mode or not self.enabled:
            return {
                'success': True,
                'journal_id': f'QB{os.urandom(12).hex()}',
                'mock': True
            }
        
        try:
            url = f'{self.base_url}/v3/company/{self.realm_id}/journalentry'
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
            
            qb_journal = self._transform_journal(journal_obj)
            response = requests.post(url, json=qb_journal, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            journal = data.get('QueryResponse', {}).get('JournalEntry', [{}])[0]
            return {
                'success': True,
                'journal_id': journal.get('Id', ''),
                'mock': False
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _transform_invoice(self, invoice: Dict[str, Any]) -> Dict[str, Any]:
        """Transform internal invoice format to QuickBooks format."""
        return {
            'Line': [
                {
                    'Amount': invoice.get('amount', 0),
                    'DetailType': 'SalesItemLineDetail',
                    'SalesItemLineDetail': {
                        'ItemRef': {'value': invoice.get('item_id', '')}
                    }
                }
            ],
            'CustomerRef': {'value': invoice.get('customer_id', '')},
            'TxnDate': invoice.get('date', ''),
            'DueDate': invoice.get('due_date', '')
        }
    
    def _transform_payment(self, payment: Dict[str, Any]) -> Dict[str, Any]:
        """Transform internal payment format to QuickBooks format."""
        return {
            'CustomerRef': {'value': payment.get('customer_id', '')},
            'TotalAmt': payment.get('amount', 0),
            'TxnDate': payment.get('date', '')
        }
    
    def _transform_journal(self, journal: Dict[str, Any]) -> Dict[str, Any]:
        """Transform internal journal format to QuickBooks format."""
        return {
            'Line': journal.get('lines', [])
        }

