"""Transaction-related routes."""
from flask import Blueprint
from utils.responses import APIResponse
from utils.validators import PaymentValidator, ValidationError
from services.payment_service import PaymentService

transaction_bp = Blueprint('transaction', __name__)

# Payment service will be injected when blueprint is registered
payment_service = None

def init_transaction_routes(service):
    """Initialize transaction routes with service dependency."""
    global payment_service
    payment_service = service

@transaction_bp.route('/payment/status/<reference>', methods=['GET'])
def check_payment_status(reference):
    """
    Check payment status
    ---
    tags:
      - Payment
    parameters:
      - in: path
        name: reference
        type: string
        required: true
        description: Payment reference ID
        example: "LOAN_ABC123"
    responses:
      200:
        description: Payment status retrieved
        schema:
          type: object
          properties:
            reference:
              type: string
              example: "LOAN_ABC123"
            status:
              type: string
              example: "paid"
            paid:
              type: boolean
              example: true
            amount:
              type: number
              example: 50.0
            method:
              type: string
              example: "ecocash"
            created_at:
              type: string
              example: "2025-06-27T10:30:00.123456"
      404:
        description: Transaction not found
    """
    try:
        # Validate reference
        validated_reference = PaymentValidator.validate_reference(reference)
        
        # Check payment status
        result = payment_service.check_payment_status(validated_reference)
        
        if 'error' in result:
            if 'not found' in result['error'].lower():
                return APIResponse.not_found(result['error'])
            else:
                return APIResponse.error(result['error'])
        
        return APIResponse.success(result, "Payment status retrieved")
    
    except ValidationError as e:
        return APIResponse.validation_error(str(e))
    except Exception as e:
        return APIResponse.internal_error(f"Status check failed: {str(e)}")

@transaction_bp.route('/transactions', methods=['GET'])
def get_transactions():
    """
    Get all transactions (for debugging)
    ---
    tags:
      - Debug
    responses:
      200:
        description: List of all transactions
        schema:
          type: object
          properties:
            status:
              type: string
              example: "success"
            data:
              type: array
              items:
                type: object
                properties:
                  reference:
                    type: string
                    example: "LOAN_ABC123"
                  phone_number:
                    type: string
                    example: "0771234567"
                  amount:
                    type: number
                    example: 50.0
                  method:
                    type: string
                    example: "ecocash"
                  status:
                    type: string
                    example: "pending"
                  created_at:
                    type: string
                    example: "2025-06-27T10:30:00.123456"
    """
    try:
        result = payment_service.get_all_transactions()
        
        if isinstance(result, dict) and 'error' in result:
            return APIResponse.error(result['error'])
        
        return APIResponse.success(
            data=result,
            message="Transactions retrieved successfully"
        )
    
    except Exception as e:
        return APIResponse.internal_error(f"Failed to retrieve transactions: {str(e)}")
