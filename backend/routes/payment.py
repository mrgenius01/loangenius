"""Payment-related routes."""
from flask import Blueprint, request
from utils.responses import APIResponse
from utils.validators import PaymentValidator, ValidationError, validate_json_data
from services.payment_service import PaymentService

payment_bp = Blueprint('payment', __name__)

# Payment service will be injected when blueprint is registered
payment_service = None

def init_payment_routes(service):
    """Initialize payment routes with service dependency."""
    global payment_service
    payment_service = service

@payment_bp.route('/payment', methods=['POST'])
def create_payment():
    """
    Create a payment request
    ---
    tags:
      - Payment
    parameters:
      - in: body
        name: payload
        schema:
          type: object
          required:
            - phoneNumber
            - amount
            - method
          properties:
            phoneNumber:
              type: string
              example: "0771234567"
            amount:
              type: string
              example: "50.00"
            method:
              type: string
              enum: ["ecocash","innbucks","omari"]
              example: "ecocash"
    responses:
      200:
        description: Payment initiated
        schema:
          type: object
          properties:
            status:
              type: string
              example: "success"
            reference:
              type: string
              example: "LOAN_ABC123"
            poll_url:
              type: string
            instructions:
              type: string
      400:
        description: Bad request
    """
    try:
        # Validate JSON data
        data = validate_json_data(request.get_json())
        
        # Validate payment request
        validated_data = PaymentValidator.validate_payment_request(data)
        
        # Create payment
        result = payment_service.create_payment(
            validated_data['phoneNumber'],
            validated_data['amount'],
            validated_data['method']
        )
        
        if result.get('status') == 'success':
            return APIResponse.payment_success(result)
        else:
            return APIResponse.payment_error(
                result.get('message', 'Payment failed'),
                result.get('errors'),
                result.get('debug_info')
            )
    
    except ValidationError as e:
        return APIResponse.validation_error(str(e))
    except ValueError as e:
        return APIResponse.validation_error(f"Invalid amount format: {str(e)}")
    except Exception as e:
        return APIResponse.internal_error(f"Payment creation failed: {str(e)}")

@payment_bp.route('/payment/test', methods=['POST'])
def create_test_payment():
    """
    Create a test payment (no actual Paynow integration)
    ---
    tags:
      - Testing
    parameters:
      - in: body
        name: payload
        schema:
          type: object
          required:
            - phoneNumber
            - amount
            - method
          properties:
            phoneNumber:
              type: string
              example: "0771234567"
              description: Phone number for payment
            amount:
              type: string
              example: "25.00"
              description: Payment amount in USD
            method:
              type: string
              enum: ["ecocash","innbucks","omari"]
              example: "ecocash"
              description: Payment method
    responses:
      200:
        description: Test payment created successfully
      400:
        description: Bad request
    """
    try:
        # Validate JSON data
        data = validate_json_data(request.get_json())
        
        # Validate payment request
        validated_data = PaymentValidator.validate_payment_request(data)
        
        # Create test payment
        result = payment_service.create_test_payment(
            validated_data['phoneNumber'],
            validated_data['amount'],
            validated_data['method']
        )
        
        if result.get('status') == 'success':
            return APIResponse.success(result, "Test payment created successfully")
        else:
            return APIResponse.error(result.get('message', 'Test payment creation failed'))
    
    except ValidationError as e:
        return APIResponse.validation_error(str(e))
    except ValueError as e:
        return APIResponse.validation_error(f"Invalid amount format: {str(e)}")
    except Exception as e:
        return APIResponse.internal_error(f"Test payment creation failed: {str(e)}")

@payment_bp.route('/payment/otp', methods=['POST'])
def submit_otp():
    """
    Submit OTP for OMari payment
    ---
    tags:
      - Payment
    parameters:
      - in: body
        name: payload
        schema:
          type: object
          required:
            - reference
            - otp
          properties:
            reference:
              type: string
              example: "LOAN_ABC123"
              description: Payment reference ID
            otp:
              type: string
              example: "012345"
              description: 6-digit OTP received via SMS
    responses:
      200:
        description: OTP submitted successfully
      400:
        description: Invalid OTP or request
      404:
        description: Transaction not found
    """
    try:
        # Validate JSON data
        data = validate_json_data(request.get_json())
        
        # Validate OTP request
        validated_data = PaymentValidator.validate_otp_request(data)
        
        # Submit OTP
        result = payment_service.submit_otp(
            validated_data['reference'],
            validated_data['otp']
        )
        
        if result.get('status') == 'success':
            return APIResponse.success(result, "OTP submitted successfully")
        elif 'not found' in result.get('error', '').lower():
            return APIResponse.not_found(result.get('error', 'Transaction not found'))
        else:
            return APIResponse.error(
                result.get('message', 'OTP submission failed'),
                result.get('error')
            )
    
    except ValidationError as e:
        return APIResponse.validation_error(str(e))
    except Exception as e:
        return APIResponse.internal_error(f"OTP submission failed: {str(e)}")

@payment_bp.route('/payment/otp/request', methods=['POST'])
def request_otp():
    """
    Request OTP for OMari payment
    ---
    tags:
      - Payment
    parameters:
      - in: body
        name: payload
        schema:
          type: object
          required:
            - reference
          properties:
            reference:
              type: string
              example: "LOAN_ABC123"
              description: Transaction reference
    responses:
      200:
        description: OTP request initiated
        schema:
          type: object
          properties:
            status:
              type: string
              example: "success"
            message:
              type: string
              example: "OTP sent to your phone"
      400:
        description: Bad request
      404:
        description: Transaction not found
    """
    try:
        # Validate JSON data
        data = validate_json_data(request.get_json())
        
        # Validate required fields
        if not data.get('reference'):
            return APIResponse.validation_error("Transaction reference is required")
        
        reference = data['reference'].strip()
        
        # Find the transaction
        from models.transaction import Transaction
        transaction = Transaction.query.filter_by(reference=reference).first()
        
        if not transaction:
            return APIResponse.not_found("Transaction not found")
        
        # Check if this is an OMari transaction
        if transaction.method != 'omari':
            return APIResponse.error("OTP is only available for OMari payments")
        
        # Check if transaction is in a valid state for OTP
        if transaction.status not in ['pending', 'sent']:
            return APIResponse.error(f"Cannot request OTP for transaction with status: {transaction.status}")
        
        # For now, we'll simulate OTP request success
        # In a real implementation, you would integrate with the actual OMari API
        return APIResponse.success({
            'reference': reference,
            'message': 'OTP has been sent to your phone',
            'otp_sent': True
        }, "OTP request initiated successfully")
        
    except ValidationError as e:
        return APIResponse.validation_error(str(e))
    except Exception as e:
        return APIResponse.internal_error(f"OTP request failed: {str(e)}")
