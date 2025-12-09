"""Communication integration adapters."""
try:
    from .whatsapp_twilio_adapter import WhatsAppTwilioAdapter
except Exception:
    WhatsAppTwilioAdapter = None

try:
    from .africastalking_adapter import AfricasTalkingAdapter
except Exception:
    AfricasTalkingAdapter = None

try:
    from .sendgrid_adapter import SendGridAdapter
except Exception:
    SendGridAdapter = None

__all__ = ['WhatsAppTwilioAdapter', 'AfricasTalkingAdapter', 'SendGridAdapter']
