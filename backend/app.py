from flask import Flask, request, jsonify
from flask_cors import CORS
from paynow import Paynow
import os
from datetime import datetime
import uuid
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for React Native app

# Paynow configuration
PAYNOW_INTEGRATION_ID = os.getenv('PAYNOW_INTEGRATION_ID', 'YOUR_INTEGRATION_ID')
PAYNOW_INTEGRATION_KEY = os.getenv('PAYNOW_INTEGRATION_KEY', 'YOUR_INTEGRATION_KEY')
RETURN_URL = os.getenv('RETURN_URL', 'http://localhost:3000/payment/return')
RESULT_URL = os.getenv('RESULT_URL', 'http://localhost:5000/paynow/result')

# Initialize Paynow
paynow = Paynow(
    PAYNOW_INTEGRATION_ID,
    PAYNOW_INTEGRATION_KEY,
    RETURN_URL,
    RESULT_URL
)

# In-memory storage for demo (use database in production)
transactions = {}

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

@app.route('/payment', methods=['POST'])
def create_payment():
    """Create a payment request"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['phoneNumber', 'amount', 'method']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        phone_number = data['phoneNumber']
        amount = float(data['amount'])
        method = data['method'].lower()
        
        # Generate unique reference
        reference = f"LOAN_{uuid.uuid4().hex[:8].upper()}"
        
        # Create payment
        payment = paynow.create_payment(reference, f"loan-user@{phone_number}")
        payment.add('Loan Repayment', amount)
        
        # Send mobile payment based on method
        if method == 'ecocash':
            response = paynow.send_mobile(payment, phone_number, 'ecocash')
        elif method == 'innbucks':
            # Note: Check if Paynow supports innbucks or use 'onemoney'
            response = paynow.send_mobile(payment, phone_number, 'onemoney')
        else:
            return jsonify({"error": "Unsupported payment method"}), 400            
        if response.success:
            # Debug: Print response attributes to understand structure
            print(f"Paynow response attributes: {dir(response)}")
            print(f"Response.instructions type: {type(response.instructions)}")
            print(f"Response.instructions value: {repr(response.instructions)}")
            
            # Since instructions is returning <class 'str'> instead of actual content,
            # let's check other possible sources of instructions
            instructions = ''
            
            # Check if there's actual instruction data in other attributes
            if hasattr(response, 'data') and response.data:
                print(f"Response.data: {response.data}")
                # Check if data contains instructions
                if isinstance(response.data, dict):
                    instructions = response.data.get('instructions', '')
                    if not instructions:
                        instructions = response.data.get('message', '')
              # If still no instructions, check if there's redirect info that can help
            if not instructions and hasattr(response, 'has_redirect') and response.has_redirect:
                if hasattr(response, 'redirect_url') and response.redirect_url:
                    instructions = f"Please complete payment by visiting: {response.redirect_url}"
            
            # If still no instructions, provide method-specific default messages
            if not instructions:
                if method.lower() == 'ecocash':
                    instructions = "Dial *151# on your EcoCash registered line and follow the prompts to complete payment."
                elif method.lower() == 'innbucks':
                    instructions = "To be redirected to Innbucks, check return URL or follow the app instructions."
                else:
                    instructions = f"Payment initiated via {method.upper()}. Please check your phone for payment instructions."
            
            # If there's a redirect URL, append it to instructions
            if hasattr(response, 'redirect_url') and response.redirect_url:
                instructions += f"\n\nAlternatively, complete payment at: {response.redirect_url}"
            
            print(f"Final instructions: {instructions}")
              # Store transaction details
            transactions[reference] = {
                'reference': reference,
                'phone_number': phone_number,
                'amount': amount,
                'method': method,
                'poll_url': str(response.poll_url) if response.poll_url else '',
                'status': 'pending',
                'created_at': datetime.now().isoformat(),
                'instructions': instructions,
                'paynow_reference': response.data.get('paynowreference', '') if response.data else '',
                'hash': response.data.get('hash', '') if response.data else '',
                'redirect_url': response.redirect_url if hasattr(response, 'redirect_url') and response.redirect_url else '',
                'has_redirect': getattr(response, 'has_redirect', False)
            }
            
            return jsonify({
                "status": "success",
                "reference": reference,
                "poll_url": str(response.poll_url) if response.poll_url else '',
                "instructions": instructions,
                "message": "Payment request sent successfully",
                # Additional essential Paynow data
                "paynow_reference": response.data.get('paynowreference', '') if response.data else '',
                "redirect_url": str(response.redirect_url) if hasattr(response, 'redirect_url') and response.redirect_url else '',
                "has_redirect": getattr(response, 'has_redirect', False),
                "hash": response.data.get('hash', '') if response.data else '',
                "paynow_status": response.data.get('status', '') if response.data else ''
            }), 200
        else:
            # Log detailed error information for debugging
            print(f"Paynow payment failed for reference {reference}")
            print(f"Response errors: {getattr(response, 'errors', [])}")
            print(f"Response data: {getattr(response, 'data', {})}")
            
            # Convert errors to strings to ensure JSON serialization
            errors = getattr(response, 'errors', [])
            if errors:
                errors = [str(error) for error in errors]
            
            return jsonify({
                "status": "error",
                "message": "Failed to process payment",
                "errors": errors,
                "debug_info": {
                    "reference": reference,
                    "integration_id": PAYNOW_INTEGRATION_ID,
                    "credentials_configured": PAYNOW_INTEGRATION_ID != 'YOUR_INTEGRATION_ID'
                }
            }), 400
            
    except ValueError as e:
        return jsonify({"error": "Invalid amount format"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/payment/status/<reference>', methods=['GET'])
def check_payment_status(reference):
    """Check payment status"""
    try:
        if reference not in transactions:
            return jsonify({"error": "Transaction not found"}), 404
        
        transaction = transactions[reference]
        poll_url = transaction['poll_url']
        
        # Check status with Paynow
        status = paynow.check_transaction_status(poll_url)
        
        # Update transaction status
        transaction['status'] = str(status.status) if status.status else 'unknown'
        transaction['updated_at'] = datetime.now().isoformat()
        
        if hasattr(status, 'paid') and status.paid:
            transaction['paid'] = True
            transaction['paid_at'] = datetime.now().isoformat()
        
        return jsonify({
            "reference": reference,
            "status": str(status.status) if status.status else 'unknown',
            "paid": bool(getattr(status, 'paid', False)),
            "amount": transaction['amount'],
            "method": transaction['method'],
            "created_at": transaction['created_at']
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/paynow/result', methods=['POST'])
def paynow_result():
    """Handle Paynow result callback"""
    try:
        # This endpoint receives payment result from Paynow
        data = request.form.to_dict()
        
        # Log the result (in production, you'd want proper logging)
        print(f"Paynow result: {data}")
        
        # Update transaction status based on result
        reference = data.get('reference')
        if reference and reference in transactions:
            transactions[reference]['paynow_result'] = data
            transactions[reference]['updated_at'] = datetime.now().isoformat()
        
        return "OK", 200
        
    except Exception as e:
        print(f"Error handling Paynow result: {e}")
        return "ERROR", 500

@app.route('/transactions', methods=['GET'])
def get_transactions():
    """Get all transactions (for debugging)"""
    return jsonify(list(transactions.values())), 200

@app.route('/payment/test', methods=['POST'])
def create_test_payment():
    """Create a test payment (no actual Paynow integration)"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['phoneNumber', 'amount', 'method']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        phone_number = data['phoneNumber']
        amount = float(data['amount'])
        method = data['method'].lower()
        
        # Generate unique reference
        reference = f"TEST_{uuid.uuid4().hex[:8].upper()}"
        
        # Create mock transaction
        transactions[reference] = {
            'reference': reference,
            'phone_number': phone_number,
            'amount': amount,
            'method': method,
            'poll_url': f'http://localhost:5000/mock/poll/{reference}',
            'status': 'pending',
            'created_at': datetime.now().isoformat(),
            'instructions': f'This is a test payment for {method.upper()}. Send ${amount} to {phone_number}',
            'is_test': True
        }
        
        return jsonify({
            "status": "success",
            "reference": reference,
            "poll_url": f'http://localhost:5000/mock/poll/{reference}',
            "instructions": f'TEST: Send ${amount} via {method.upper()} to {phone_number}',
            "message": "Test payment request created successfully",
            "note": "This is a test transaction - no real payment will be processed"
        }), 200
            
    except ValueError as e:
        return jsonify({"error": "Invalid amount format"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("Starting Loan Repayment Backend...")
    print(f"Paynow Integration ID: {PAYNOW_INTEGRATION_ID}")
    print("Make sure to set your Paynow credentials in environment variables:")
    print("- PAYNOW_INTEGRATION_ID")
    print("- PAYNOW_INTEGRATION_KEY")
    app.run(debug=True, host='0.0.0.0', port=5000)
