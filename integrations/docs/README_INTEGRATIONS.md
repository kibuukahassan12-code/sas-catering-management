# Enterprise Integrations Documentation

## Overview

The SAS Best Foods ERP system includes comprehensive enterprise integrations for payments, communications, accounting, storage, delivery, HR, BI, and ML services.

## Setup

### 1. Install Dependencies

```bash
pip install Flask Flask-SQLAlchemy Flask-Migrate python-dotenv requests boto3 stripe stripe-python twilio sendgrid reportlab qrcode Pillow psycopg2-binary sqlalchemy-utils gunicorn pandas scikit-learn prophet
```

### 2. Configure API Keys

Copy `config/integrations.example.env` to `.env` and fill in your API keys:

```bash
cp config/integrations.example.env .env
```

Edit `.env` with your actual credentials.

### 3. Enable/Disable Integrations

Set `INTEGRATIONS_MOCK=true` in `.env` to run in mock mode (for testing without API keys).

## Available Integrations

### Payment Processors

- **Stripe**: Credit card payments
- **Flutterwave**: African payment gateway
- **Paystack**: Nigerian payment gateway
- **MTN MoMo**: Mobile money (Uganda, etc.)

### Communications

- **WhatsApp (Twilio)**: WhatsApp Business API
- **Africa's Talking**: SMS and WhatsApp for Africa
- **SendGrid**: Transactional email

### Accounting

- **QuickBooks**: Accounting sync
- **Xero**: Accounting sync

### Storage

- **AWS S3**: File storage
- **Cloudinary**: Media storage and CDN

### Delivery

- **Google Maps**: Geocoding, directions, distance matrix
- **Route Optimizer**: Delivery route optimization

### HR & Attendance

- **ZKTeco**: Biometric attendance devices

### BI & Analytics

- **Power BI**: Data export
- **Tableau**: Data export

### ML & Forecasting

- **Sales Forecasting**: Linear regression and Prophet models
- **Demand Prediction**: Item-level demand forecasting

## Usage

### Integration Manager

All integrations are accessed through the `IntegrationManager`:

```python
from services.integration_manager import integration_manager

# Create payment
result = integration_manager.create_payment(
    provider='stripe',
    amount=100.0,
    currency='USD'
)

# Send WhatsApp
result = integration_manager.send_message(
    channel='whatsapp',
    to='+256771234567',
    message='Your order is ready!'
)

# Upload file
result = integration_manager.upload_file(
    provider='s3',
    file_path='/path/to/file.jpg',
    remote_path='uploads/file.jpg'
)
```

### Webhooks

Webhook endpoints are available at:

- `/integrations/webhooks/stripe` - Stripe payment events
- `/integrations/webhooks/twilio` - Twilio message status

### Admin Dashboard

Access the integrations dashboard at `/integrations/dashboard` (Admin/Sales Manager only).

## Testing

Run integration tests:

```bash
python -m pytest tests/test_integrations.py -v
```

## Example API Calls

### Test Stripe Payment

```bash
curl -X POST http://localhost:5000/integrations/payments/test \
  -H "Content-Type: application/json" \
  -d '{"provider": "stripe", "amount": 10.0, "currency": "USD"}'
```

### Test WhatsApp Message

```bash
curl -X POST http://localhost:5000/integrations/comms/test \
  -H "Content-Type: application/json" \
  -d '{"channel": "whatsapp", "to": "+256771234567", "message": "Test"}'
```

### Upload File to Storage

```bash
curl -X POST http://localhost:5000/integrations/storage/upload-test \
  -F "file=@instance/integrations_assets/sample_asset.jpg" \
  -F "provider=s3"
```

## Security Notes

1. **Never commit `.env` files** to version control
2. Use **sandbox/test keys** during development
3. **Restrict API keys** to specific IPs/domains when possible
4. **Rotate keys** regularly
5. Use **webhook signatures** to verify requests

## Troubleshooting

### Mock Mode

If integrations are in mock mode, check:
- `INTEGRATIONS_MOCK` is not set to `true` in `.env`
- API keys are correctly configured
- Required SDKs are installed

### Common Errors

- **ImportError**: Install missing SDK (`pip install <package>`)
- **Authentication Error**: Check API keys in `.env`
- **Webhook Verification Failed**: Check webhook secret configuration

## Support

For integration-specific issues, refer to:
- Provider documentation
- Integration adapter source code in `integrations/`
- Integration manager in `services/integration_manager.py`

