"""Webhook routes for Paynow callbacks."""
from flask import Blueprint, request
from utils.responses import APIResponse
from services.payment_service import PaymentService

webhook_bp = Blueprint('webhook', __name__)

# Payment service will be injected when blueprint is registered
payment_service = None

def init_webhook_routes(service):
    """Initialize webhook routes with service dependency."""
    global payment_service
    payment_service = service

@webhook_bp.route('/paynow/result', methods=['POST'])
def paynow_result():
    """
    Handle Paynow result callback
    ---
    tags:
      - Webhooks
    parameters:
      - in: formData
        name: reference
        type: string
        description: Payment reference
      - in: formData
        name: paynowreference
        type: string
        description: Paynow internal reference
      - in: formData
        name: amount
        type: string
        description: Payment amount
      - in: formData
        name: status
        type: string
        description: Payment status
    responses:
      200:
        description: Callback processed successfully
        schema:
          type: string
          example: "OK"
      500:
        description: Error processing callback
        schema:
          type: string
          example: "ERROR"
    """
    try:
        # Get form data from Paynow
        data = request.form.to_dict()
        
        # Log the result (in production, you'd want proper logging)
        print(f"Paynow result: {data}")
        
        # Handle the result
        success = payment_service.handle_paynow_result(data)
        
        if success:
            return "OK", 200
        else:
            return "ERROR", 500
    
    except Exception as e:
        print(f"Error handling Paynow result: {e}")
        return "ERROR", 500
