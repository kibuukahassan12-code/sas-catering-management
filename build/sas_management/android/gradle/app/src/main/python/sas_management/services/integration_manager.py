"""Integration manager service - single entry point for all integrations."""
import os
from typing import Dict, Optional, Any, List
from flask import current_app

# Safe imports for Payment adapters
try:
    from integrations.payments.stripe_adapter import StripeAdapter
except Exception:
    StripeAdapter = None

try:
    from integrations.payments.flutterwave_adapter import FlutterwaveAdapter
except Exception:
    FlutterwaveAdapter = None

try:
    from integrations.payments.paystack_adapter import PaystackAdapter
except Exception:
    PaystackAdapter = None

try:
    from integrations.payments.mtmomo_adapter import MTMoMoAdapter
except Exception:
    MTMoMoAdapter = None

# Safe imports for Communication adapters
try:
    from integrations.comms.whatsapp_twilio_adapter import WhatsAppTwilioAdapter
except Exception:
    WhatsAppTwilioAdapter = None

try:
    from integrations.comms.africastalking_adapter import AfricasTalkingAdapter
except Exception:
    AfricasTalkingAdapter = None

try:
    from integrations.comms.sendgrid_adapter import SendGridAdapter
except Exception:
    SendGridAdapter = None

# Safe imports for Accounting adapters
try:
    from integrations.accounting.quickbooks_adapter import QuickBooksAdapter
except Exception:
    QuickBooksAdapter = None

try:
    from integrations.accounting.xero_adapter import XeroAdapter
except Exception:
    XeroAdapter = None

# Safe imports for POS adapters
try:
    from integrations.pos.escpos_adapter import ESCPOSAdapter
except Exception:
    ESCPOSAdapter = None

# Safe imports for Delivery adapters
try:
    from integrations.delivery.google_maps_adapter import GoogleMapsAdapter
except Exception:
    GoogleMapsAdapter = None

try:
    from integrations.delivery.route_optimizer import RouteOptimizer
except Exception:
    RouteOptimizer = None

# Safe imports for Storage adapters
try:
    from integrations.storage.s3_adapter import S3Adapter
except Exception:
    S3Adapter = None

try:
    from integrations.storage.cloudinary_adapter import CloudinaryAdapter
except Exception:
    CloudinaryAdapter = None

# Safe imports for HR adapters
try:
    from integrations.hr_attendance.zkteco_adapter import ZKTecoAdapter
except Exception:
    ZKTecoAdapter = None

# Safe imports for BI adapters
try:
    from integrations.bi.powerbi_adapter import PowerBIAdapter
except Exception:
    PowerBIAdapter = None

try:
    from integrations.bi.tableau_adapter import TableauAdapter
except Exception:
    TableauAdapter = None

# Safe imports for ML services
try:
    from integrations.ml.forecasting_service import ForecastingService
except Exception:
    ForecastingService = None


class IntegrationManager:
    """Central manager for all integrations."""
    
    def __init__(self):
        # Initialize all adapters with safe fallbacks
        self.stripe = StripeAdapter() if StripeAdapter else None
        self.flutterwave = FlutterwaveAdapter() if FlutterwaveAdapter else None
        self.paystack = PaystackAdapter() if PaystackAdapter else None
        self.mtmomo = MTMoMoAdapter() if MTMoMoAdapter else None
        
        self.whatsapp = WhatsAppTwilioAdapter() if WhatsAppTwilioAdapter else None
        self.africastalking = AfricasTalkingAdapter() if AfricasTalkingAdapter else None
        self.sendgrid = SendGridAdapter() if SendGridAdapter else None
        
        self.quickbooks = QuickBooksAdapter() if QuickBooksAdapter else None
        self.xero = XeroAdapter() if XeroAdapter else None
        
        self.escpos = ESCPOSAdapter() if ESCPOSAdapter else None
        
        self.google_maps = GoogleMapsAdapter() if GoogleMapsAdapter else None
        self.route_optimizer = RouteOptimizer() if RouteOptimizer else None
        
        self.s3 = S3Adapter() if S3Adapter else None
        self.cloudinary = CloudinaryAdapter() if CloudinaryAdapter else None
        
        self.zkteco = ZKTecoAdapter() if ZKTecoAdapter else None
        
        self.powerbi = PowerBIAdapter() if PowerBIAdapter else None
        self.tableau = TableauAdapter() if TableauAdapter else None
        
        self.forecasting = ForecastingService() if ForecastingService else None
    
    # Payment methods
    def create_payment(
        self,
        provider: str,
        amount: float,
        currency: str = 'USD',
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create payment via specified provider."""
        provider = provider.lower()
        
        if provider == 'stripe':
            if not self.stripe:
                return {'success': False, 'error': 'Stripe adapter not available'}
            return self.stripe.create_payment_intent(amount, currency, metadata, **kwargs)
        elif provider == 'flutterwave':
            if not self.flutterwave:
                return {'success': False, 'error': 'Flutterwave adapter not available'}
            return self.flutterwave.create_payment(amount, currency, **kwargs)
        elif provider == 'paystack':
            if not self.paystack:
                return {'success': False, 'error': 'Paystack adapter not available'}
            return self.paystack.initialize_transaction(amount, **kwargs)
        elif provider == 'mtnmomo':
            if not self.mtmomo:
                return {'success': False, 'error': 'MTN MoMo adapter not available'}
            return self.mtmomo.request_to_pay(amount, currency, **kwargs)
        else:
            return {'success': False, 'error': f'Unknown payment provider: {provider}'}
    
    # Communication methods
    def send_message(
        self,
        channel: str,
        to: str,
        message: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Send message via specified channel."""
        channel = channel.lower()
        
        if channel == 'whatsapp':
            if not self.whatsapp:
                return {'success': False, 'error': 'WhatsApp adapter not available'}
            return self.whatsapp.send_whatsapp_message(to, message, **kwargs)
        elif channel == 'sms_africastalking':
            if not self.africastalking:
                return {'success': False, 'error': 'Africa\'s Talking adapter not available'}
            return self.africastalking.send_sms(to, message, **kwargs)
        elif channel == 'whatsapp_africastalking':
            if not self.africastalking:
                return {'success': False, 'error': 'Africa\'s Talking adapter not available'}
            return self.africastalking.send_whatsapp(to, message, **kwargs)
        else:
            return {'success': False, 'error': f'Unknown communication channel: {channel}'}
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Send email via SendGrid."""
        if not self.sendgrid:
            return {'success': False, 'error': 'SendGrid adapter not available'}
        return self.sendgrid.send_email(to_email, subject, html_content, **kwargs)
    
    # Accounting sync methods
    def sync_invoice(
        self,
        provider: str,
        invoice_obj: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Sync invoice to accounting provider."""
        provider = provider.lower()
        
        if provider == 'quickbooks':
            if not self.quickbooks:
                return {'success': False, 'error': 'QuickBooks adapter not available'}
            return self.quickbooks.push_invoice(invoice_obj)
        elif provider == 'xero':
            if not self.xero:
                return {'success': False, 'error': 'Xero adapter not available'}
            return self.xero.push_invoice(invoice_obj)
        else:
            return {'success': False, 'error': f'Unknown accounting provider: {provider}'}
    
    def sync_payment(
        self,
        provider: str,
        payment_obj: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Sync payment to accounting provider."""
        provider = provider.lower()
        
        if provider == 'quickbooks':
            if not self.quickbooks:
                return {'success': False, 'error': 'QuickBooks adapter not available'}
            return self.quickbooks.push_payment(payment_obj)
        elif provider == 'xero':
            if not self.xero:
                return {'success': False, 'error': 'Xero adapter not available'}
            return self.xero.push_payment(payment_obj)
        else:
            return {'success': False, 'error': f'Unknown accounting provider: {provider}'}
    
    # Storage methods
    def upload_file(
        self,
        provider: str,
        file_path: str,
        remote_path: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Upload file to storage provider."""
        provider = provider.lower()
        
        if provider == 's3':
            if not self.s3:
                return {'success': False, 'error': 'S3 adapter not available'}
            return self.s3.upload_file(file_path, remote_path, **kwargs)
        elif provider == 'cloudinary':
            if not self.cloudinary:
                return {'success': False, 'error': 'Cloudinary adapter not available'}
            return self.cloudinary.upload_file(file_path, public_id=remote_path, **kwargs)
        else:
            return {'success': False, 'error': f'Unknown storage provider: {provider}'}
    
    # Delivery methods
    def geocode_address(self, address: str) -> Dict[str, Any]:
        """Geocode address using Google Maps."""
        if not self.google_maps:
            return {'success': False, 'error': 'Google Maps adapter not available'}
        return self.google_maps.geocode(address)
    
    def optimize_delivery_route(
        self,
        start_location: tuple,
        delivery_locations: List[Dict[str, Any]],
        return_to_start: bool = True
    ) -> Dict[str, Any]:
        """Optimize delivery route."""
        if not self.route_optimizer:
            return {'success': False, 'error': 'Route optimizer not available'}
        return self.route_optimizer.optimize_route(
            start_location,
            delivery_locations,
            return_to_start
        )
    
    # ML/Forecasting methods
    def forecast_sales(
        self,
        historical_data: List[tuple],
        horizon: int = 30,
        model: str = 'simple'
    ) -> Dict[str, Any]:
        """Forecast sales using ML."""
        if not self.forecasting:
            return {'success': False, 'error': 'Forecasting service not available'}
        return self.forecasting.predict_sales(historical_data, horizon, model)
    
    # Get integration status
    def get_status(self) -> Dict[str, Any]:
        """Get status of all integrations."""
        return {
            'payments': {
                'stripe': bool(self.stripe and self.stripe.enabled) if self.stripe else False,
                'flutterwave': bool(self.flutterwave and self.flutterwave.enabled) if self.flutterwave else False,
                'paystack': bool(self.paystack and self.paystack.enabled) if self.paystack else False,
                'mtnmomo': bool(self.mtmomo and self.mtmomo.enabled) if self.mtmomo else False
            },
            'communications': {
                'whatsapp_twilio': bool(self.whatsapp and self.whatsapp.enabled) if self.whatsapp else False,
                'africastalking': bool(self.africastalking and self.africastalking.enabled) if self.africastalking else False,
                'sendgrid': bool(self.sendgrid and self.sendgrid.enabled) if self.sendgrid else False
            },
            'accounting': {
                'quickbooks': bool(self.quickbooks and self.quickbooks.enabled) if self.quickbooks else False,
                'xero': bool(self.xero and self.xero.enabled) if self.xero else False
            },
            'storage': {
                's3': bool(self.s3 and self.s3.enabled) if self.s3 else False,
                'cloudinary': bool(self.cloudinary and self.cloudinary.enabled) if self.cloudinary else False
            },
            'delivery': {
                'google_maps': bool(self.google_maps and self.google_maps.enabled) if self.google_maps else False
            },
            'hr': {
                'zkteco': bool(self.zkteco and self.zkteco.enabled) if self.zkteco else False
            },
            'bi': {
                'powerbi': bool(self.powerbi and self.powerbi.enabled) if self.powerbi else False,
                'tableau': bool(self.tableau and self.tableau.enabled) if self.tableau else False
            },
            'ml': {
                'forecasting': bool(self.forecasting and self.forecasting.enabled) if self.forecasting else False
            },
            'mock_mode': os.getenv('INTEGRATIONS_MOCK', 'false').lower() == 'true',
            'adapters_loaded': {
                'stripe': bool(self.stripe),
                'flutterwave': bool(self.flutterwave),
                'paystack': bool(self.paystack),
                'mtnmomo': bool(self.mtmomo),
                'whatsapp': bool(self.whatsapp),
                'africastalking': bool(self.africastalking),
                'sendgrid': bool(self.sendgrid),
                'quickbooks': bool(self.quickbooks),
                'xero': bool(self.xero),
                'escpos': bool(self.escpos),
                'google_maps': bool(self.google_maps),
                'route_optimizer': bool(self.route_optimizer),
                's3': bool(self.s3),
                'cloudinary': bool(self.cloudinary),
                'zkteco': bool(self.zkteco),
                'powerbi': bool(self.powerbi),
                'tableau': bool(self.tableau),
                'forecasting': bool(self.forecasting)
            }
        }


# Global instance with safe initialization
try:
    integration_manager = IntegrationManager()
except Exception as e:
    # Create a minimal stub if initialization fails
    print(f"Warning: Integration manager initialization failed: {e}")
    integration_manager = None
