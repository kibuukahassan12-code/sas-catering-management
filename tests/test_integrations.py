"""Integration tests for enterprise integrations."""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Set mock mode for tests
os.environ['INTEGRATIONS_MOCK'] = 'true'


class TestIntegrations(unittest.TestCase):
    """Test integration adapters."""
    
    def setUp(self):
        """Set up test environment."""
        from services.integration_manager import integration_manager
        self.manager = integration_manager
    
    def test_payment_stripe(self):
        """Test Stripe payment adapter."""
        result = self.manager.create_payment(
            provider='stripe',
            amount=10.0,
            currency='USD'
        )
        self.assertTrue(result['success'])
        self.assertIn('payment_intent_id', result)
        self.assertTrue(result.get('mock', False))
    
    def test_payment_flutterwave(self):
        """Test Flutterwave payment adapter."""
        result = self.manager.create_payment(
            provider='flutterwave',
            amount=10000.0,
            currency='UGX'
        )
        self.assertTrue(result['success'])
        self.assertIn('payment_link', result)
    
    def test_communication_whatsapp(self):
        """Test WhatsApp communication."""
        result = self.manager.send_message(
            channel='whatsapp',
            to='+256771234567',
            message='Test message'
        )
        self.assertTrue(result['success'])
        self.assertIn('message_sid', result)
    
    def test_communication_email(self):
        """Test email communication."""
        result = self.manager.send_email(
            to_email='test@example.com',
            subject='Test',
            html_content='<p>Test</p>'
        )
        self.assertTrue(result['success'])
        self.assertIn('message_id', result)
    
    def test_storage_s3(self):
        """Test S3 storage upload."""
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as f:
            f.write(b'test content')
            temp_path = f.name
        
        try:
            result = self.manager.upload_file(
                provider='s3',
                file_path=temp_path,
                remote_path='test/file.txt'
            )
            self.assertTrue(result['success'])
            self.assertIn('url', result)
        finally:
            os.unlink(temp_path)
    
    def test_geocoding(self):
        """Test address geocoding."""
        result = self.manager.geocode_address('Kampala, Uganda')
        self.assertTrue(result['success'])
        self.assertIn('lat', result)
        self.assertIn('lng', result)
    
    def test_route_optimization(self):
        """Test route optimization."""
        start = (0.3476, 32.5825)  # Kampala
        deliveries = [
            {'lat': 0.3500, 'lng': 32.5800, 'address': 'Location 1', 'order_id': '1'},
            {'lat': 0.3450, 'lng': 32.5850, 'address': 'Location 2', 'order_id': '2'}
        ]
        
        result = self.manager.optimize_delivery_route(start, deliveries)
        self.assertTrue(result['success'])
        self.assertIn('route', result)
        self.assertIn('total_distance', result)
    
    def test_forecasting(self):
        """Test sales forecasting."""
        historical = [
            ('2025-11-01', 1000.0),
            ('2025-11-02', 1200.0),
            ('2025-11-03', 1100.0),
            ('2025-11-04', 1300.0),
            ('2025-11-05', 1250.0)
        ]
        
        result = self.manager.forecast_sales(historical, horizon=7)
        self.assertTrue(result['success'])
        self.assertIn('forecast', result)
        self.assertEqual(len(result['forecast']), 7)
    
    def test_integration_status(self):
        """Test integration status retrieval."""
        status = self.manager.get_status()
        self.assertIn('payments', status)
        self.assertIn('communications', status)
        self.assertIn('accounting', status)
        self.assertIn('storage', status)
        self.assertTrue(status['mock_mode'])


if __name__ == '__main__':
    unittest.main()

