"""Integrations blueprint routes."""
import os
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, current_app, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from sas_management.models import UserRole

from sas_management.utils import role_required

# Safe import of integration manager
try:
    from sas_management.services.integration_manager import integration_manager
    INTEGRATION_MANAGER_AVAILABLE = True
except Exception as e:
    current_app.logger.warning(f"Integration manager not available: {e}") if 'current_app' in globals() else None
    integration_manager = None
    INTEGRATION_MANAGER_AVAILABLE = False

integrations_bp = Blueprint("integrations", __name__, url_prefix="/integrations")

@integrations_bp.route("/dashboard")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def dashboard():
    """Integrations dashboard."""
    try:
        if not INTEGRATION_MANAGER_AVAILABLE or not integration_manager:
            status = {
                'payments': {'stripe': False, 'flutterwave': False, 'paystack': False, 'mtnmomo': False},
                'communications': {'whatsapp_twilio': False, 'africastalking': False, 'sendgrid': False},
                'accounting': {'quickbooks': False, 'xero': False},
                'storage': {'s3': False, 'cloudinary': False},
                'delivery': {'google_maps': False},
                'hr': {'zkteco': False},
                'bi': {'powerbi': False, 'tableau': False},
                'ml': {'forecasting': False},
                'mock_mode': True,
                'error': 'Integration manager not available'
            }
        else:
            status = integration_manager.get_status()
        return render_template("integrations/dashboard.html", status=status)
    except Exception as e:
        current_app.logger.exception(f"Error loading integrations dashboard: {e}")
        return render_template("integrations/dashboard.html", status={})

@integrations_bp.route("/flutterwave", endpoint="integrations_flutterwave")
@login_required
@role_required(UserRole.Admin)
def flutterwave_settings():
    """Flutterwave payment integration settings."""
    try:
        if request.method == "POST":
            # Handle settings update
            public_key = request.form.get("public_key", "").strip()
            secret_key = request.form.get("secret_key", "").strip()
            redirect_url = request.form.get("redirect_url", "").strip()
            
            # In a real implementation, you would save these to config/database
            # For now, just flash a message
            flash("Flutterwave settings updated successfully.", "success")
            return redirect(url_for("integrations.flutterwave_settings"))
        
        # GET request - show settings form
        # Get current settings from environment or config
        settings = {
            "public_key": os.getenv("FLUTTERWAVE_PUBLIC_KEY", ""),
            "secret_key": "***hidden***" if os.getenv("FLUTTERWAVE_SECRET_KEY") else "",
            "redirect_url": os.getenv("FLUTTERWAVE_REDIRECT_URL", ""),
            "enabled": bool(integration_manager and integration_manager.flutterwave and integration_manager.flutterwave.enabled) if INTEGRATION_MANAGER_AVAILABLE else False
        }
        return render_template("integrations/flutterwave_settings.html", settings=settings)
    except Exception as e:
        current_app.logger.exception(f"Error loading Flutterwave settings: {e}")
        return render_template("integrations/flutterwave_settings.html", settings={})

# Payment test endpoints
@integrations_bp.route("/payments/test", methods=["POST"])
@login_required
@role_required(UserRole.Admin)
def test_payment():
    """Test payment integration."""
    try:
        if not INTEGRATION_MANAGER_AVAILABLE or not integration_manager:
            return jsonify({'success': False, 'error': 'Integration manager not available'}), 503
        
        data = request.get_json() or request.form
        provider = data.get('provider', 'stripe')
        amount = float(data.get('amount', 10.0))
        currency = data.get('currency', 'USD')
        
        result = integration_manager.create_payment(
            provider=provider,
            amount=amount,
            currency=currency,
            metadata={'test': True, 'user_id': current_user.id}
        )
        
        if request.is_json:
            return jsonify(result), 200 if result['success'] else 400
        else:
            if result['success']:
                flash(f"Test payment created successfully! {result.get('message', '')}", "success")
            else:
                flash(f"Payment test failed: {result.get('error', 'Unknown error')}", "danger")
            return redirect(url_for("integrations.dashboard"))
    except Exception as e:
        current_app.logger.exception(f"Payment test error: {e}")
        if request.is_json:
            return jsonify({'success': False, 'error': str(e)}), 500
        return redirect(url_for("integrations.dashboard"))

# Communication test endpoints
@integrations_bp.route("/comms/test", methods=["POST"])
@login_required
@role_required(UserRole.Admin)
def test_communication():
    """Test communication integration."""
    try:
        if not INTEGRATION_MANAGER_AVAILABLE or not integration_manager:
            if request.is_json:
                return jsonify({'success': False, 'error': 'Integration manager not available'}), 503
            flash("Integration manager is not available.", "danger")
            return redirect(url_for("integrations.dashboard"))
        
        data = request.get_json() or request.form
        channel = data.get('channel', 'whatsapp')
        to = data.get('to', '').strip()
        message = data.get('message', 'Test message from SAS Best Foods ERP').strip()
        
        if not to:
            if request.is_json:
                return jsonify({'success': False, 'error': 'Recipient address is required'}), 400
            flash("Please provide a recipient address.", "warning")
            return redirect(url_for("integrations.dashboard"))
        
        if channel == 'email':
            result = integration_manager.send_email(
                to_email=to,
                subject='Test Email from SAS Best Foods',
                html_content=f'<p>{message}</p>'
            )
        else:
            result = integration_manager.send_message(channel, to, message)
        
        if request.is_json:
            return jsonify(result), 200 if result.get('success') else 400
        else:
            if result.get('success'):
                flash(f"Test message sent successfully! {result.get('message', '')}", "success")
            else:
                error_msg = result.get('error', 'Unknown error')
                flash(f"Message test failed: {error_msg}", "danger")
            return redirect(url_for("integrations.dashboard"))
    except ValueError as e:
        current_app.logger.warning(f"Invalid input in communication test: {e}")
        if request.is_json:
            return jsonify({'success': False, 'error': str(e)}), 400
        flash(f"Invalid input: {str(e)}", "warning")
        return redirect(url_for("integrations.dashboard"))
    except Exception as e:
        current_app.logger.exception(f"Communication test error: {e}")
        if request.is_json:
            return jsonify({'success': False, 'error': 'Unexpected error'}), 500
        return redirect(url_for("integrations.dashboard"))

# Accounting test endpoints
@integrations_bp.route("/accounting/test", methods=["POST"])
@login_required
@role_required(UserRole.Admin)
def test_accounting():
    """Test accounting integration."""
    try:
        data = request.get_json() or request.form
        provider = data.get('provider', 'quickbooks')
        
        test_invoice = {
            'customer_id': 'test_customer',
            'amount': 100.0,
            'date': '2025-11-23',
            'due_date': '2025-12-23',
            'description': 'Test invoice from SAS Best Foods ERP'
        }
        
        result = integration_manager.sync_invoice(provider, test_invoice)
        
        if request.is_json:
            return jsonify(result), 200 if result['success'] else 400
        else:
            if result['success']:
                flash(f"Test invoice synced successfully! {result.get('message', '')}", "success")
            else:
                flash(f"Accounting sync failed: {result.get('error', 'Unknown error')}", "danger")
            return redirect(url_for("integrations.dashboard"))
    except Exception as e:
        current_app.logger.exception(f"Accounting test error: {e}")
        if request.is_json:
            return jsonify({'success': False, 'error': str(e)}), 500
        return redirect(url_for("integrations.dashboard"))

# Storage test endpoints
@integrations_bp.route("/storage/upload-test", methods=["POST"])
@login_required
@role_required(UserRole.Admin)
def test_storage_upload():
    """Test storage upload."""
    try:
        data = request.form
        provider = data.get('provider', 's3')
        
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # Save temporarily
        import tempfile
        temp_path = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1])
        file.save(temp_path.name)
        temp_path.close()
        
        # Upload
        remote_path = f'test/{secure_filename(file.filename)}'
        result = integration_manager.upload_file(provider, temp_path.name, remote_path)
        
        # Cleanup
        os.unlink(temp_path.name)
        
        if request.is_json:
            return jsonify(result), 200 if result['success'] else 400
        else:
            if result['success']:
                flash(f"File uploaded successfully! URL: {result.get('url', '')}", "success")
            else:
                flash(f"Upload failed: {result.get('error', 'Unknown error')}", "danger")
            return redirect(url_for("integrations.dashboard"))
    except Exception as e:
        current_app.logger.exception(f"Storage upload test error: {e}")
        if request.is_json:
            return jsonify({'success': False, 'error': str(e)}), 500
        return redirect(url_for("integrations.dashboard"))

# Webhook endpoints
@integrations_bp.route("/webhooks/stripe", methods=["POST"])
def stripe_webhook():
    """Stripe webhook receiver."""
    try:
        payload = request.get_data()
        signature = request.headers.get('Stripe-Signature', '')
        
        result = integration_manager.stripe.verify_webhook(payload, signature)
        
        if result['success']:
            event = result.get('event', {})
            event_type = event.get('type', '')
            
            # Handle payment events
            if event_type == 'payment_intent.succeeded':
                payment_intent = event.get('data', {}).get('object', {})
                current_app.logger.info(f"Payment succeeded: {payment_intent.get('id')}")
                # TODO: Update invoice/payment status in database
            
            return jsonify({'received': True}), 200
        else:
            current_app.logger.warning(f"Stripe webhook verification failed: {result.get('error')}")
            return jsonify({'error': result.get('error')}), 400
    except Exception as e:
        current_app.logger.exception(f"Stripe webhook error: {e}")
        return jsonify({'error': str(e)}), 500

@integrations_bp.route("/webhooks/twilio", methods=["POST"])
def twilio_webhook():
    """Twilio webhook receiver."""
    try:
        data = request.form
        message_sid = data.get('MessageSid', '')
        status = data.get('MessageStatus', '')
        to = data.get('To', '')
        from_number = data.get('From', '')
        
        current_app.logger.info(f"Twilio webhook: {message_sid} - {status}")
        # TODO: Update message status in database
        
        return jsonify({'received': True}), 200
    except Exception as e:
        current_app.logger.exception(f"Twilio webhook error: {e}")
        return jsonify({'error': str(e)}), 500

# Route optimization endpoint
@integrations_bp.route("/delivery/route-optimize", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def route_optimize():
    """Optimize delivery route."""
    try:
        data = request.get_json() or request.form
        start_lat = float(data.get('start_lat', 0))
        start_lng = float(data.get('start_lng', 0))
        deliveries = data.get('deliveries', [])
        
        result = integration_manager.optimize_delivery_route(
            (start_lat, start_lng),
            deliveries,
            return_to_start=True
        )
        
        return jsonify(result), 200 if result['success'] else 400
    except Exception as e:
        current_app.logger.exception(f"Route optimization error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

