"""Stripe payment integration adapter."""
import os
from typing import Dict, Optional, Any
from flask import current_app

try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False
    stripe = None


class StripeAdapter:
    """Stripe payment processor adapter."""
    
    def __init__(self):
        self.api_key = os.getenv('STRIPE_SECRET', '')
        self.webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET', '')
        self.mock_mode = os.getenv('INTEGRATIONS_MOCK', 'false').lower() == 'true'
        
        if STRIPE_AVAILABLE and self.api_key and not self.mock_mode:
            stripe.api_key = self.api_key
            self.enabled = True
        else:
            self.enabled = False
            if current_app:
                current_app.logger.warning(
                    "Stripe adapter disabled: SDK not installed or no API key. "
                    "Using mock mode." if self.mock_mode else ""
                )
    
    def create_payment_intent(
        self,
        amount: float,
        currency: str = 'usd',
        metadata: Optional[Dict[str, Any]] = None,
        customer_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a Stripe payment intent.
        
        Args:
            amount: Amount in smallest currency unit (e.g., cents for USD)
            currency: Currency code (default: 'usd')
            metadata: Additional metadata dict
            customer_id: Optional Stripe customer ID
            
        Returns:
            Dict with 'success', 'payment_intent_id', 'client_secret', 'error'
        """
        if self.mock_mode or not self.enabled:
            return {
                'success': True,
                'payment_intent_id': f'pi_mock_{os.urandom(8).hex()}',
                'client_secret': f'pi_mock_{os.urandom(8).hex()}_secret',
                'mock': True,
                'message': 'Mock payment intent created (Stripe not configured)'
            }
        
        try:
            intent_data = {
                'amount': int(amount * 100),  # Convert to cents
                'currency': currency.lower(),
                'metadata': metadata or {}
            }
            if customer_id:
                intent_data['customer'] = customer_id
            
            intent = stripe.PaymentIntent.create(**intent_data)
            
            return {
                'success': True,
                'payment_intent_id': intent.id,
                'client_secret': intent.client_secret,
                'status': intent.status,
                'mock': False
            }
        except stripe.error.StripeError as e:
            if current_app:
                current_app.logger.error(f"Stripe error: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }
        except Exception as e:
            if current_app:
                current_app.logger.exception(f"Unexpected error in Stripe adapter: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def verify_webhook(self, payload: bytes, signature: str) -> Dict[str, Any]:
        """
        Verify Stripe webhook signature.
        
        Args:
            payload: Raw request body bytes
            signature: Stripe signature header
            
        Returns:
            Dict with 'success', 'event' (if valid), 'error'
        """
        if self.mock_mode or not self.enabled or not self.webhook_secret:
            return {
                'success': True,
                'event': {'id': 'evt_mock', 'type': 'payment_intent.succeeded'},
                'mock': True
            }
        
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, self.webhook_secret
            )
            return {
                'success': True,
                'event': event,
                'mock': False
            }
        except ValueError as e:
            return {'success': False, 'error': f'Invalid payload: {e}'}
        except stripe.error.SignatureVerificationError as e:
            return {'success': False, 'error': f'Invalid signature: {e}'}
        except Exception as e:
            if current_app:
                current_app.logger.exception(f"Webhook verification error: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_payment_status(self, payment_intent_id: str) -> Dict[str, Any]:
        """Retrieve payment intent status."""
        if self.mock_mode or not self.enabled:
            return {
                'success': True,
                'status': 'succeeded',
                'mock': True
            }
        
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            return {
                'success': True,
                'status': intent.status,
                'amount': intent.amount / 100,
                'currency': intent.currency,
                'mock': False
            }
        except stripe.error.StripeError as e:
            return {'success': False, 'error': str(e)}
        except Exception as e:
            return {'success': False, 'error': str(e)}

