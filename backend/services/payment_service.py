"""Payment business logic service."""
import uuid
from datetime import datetime
from models.transaction import Transaction
from services.paynow_service import PaynowService
from utils.database import db
import os
class PaymentService:
    """Service class for payment business logic."""
    
    def __init__(self, paynow_service):
        """Initialize payment service with Paynow service."""
        self.paynow_service = paynow_service
        
        # If no paynow_service provided, try to create one
        if not self.paynow_service:
            try:
                # Get configuration from environment variables or use defaults
                integration_id = os.getenv('PAYNOW_INTEGRATION_ID', 'YOUR_INTEGRATION_ID')
                integration_key = os.getenv('PAYNOW_INTEGRATION_KEY', 'YOUR_INTEGRATION_KEY')
                return_url = os.getenv('PAYNOW_RETURN_URL', 'http://localhost:5000/payment/return')
                result_url = os.getenv('PAYNOW_RESULT_URL', 'http://localhost:5000/payment/result')
                
                # Initialize PaynowService with proper parameters
                self.paynow_service = PaynowService(
                    integration_id=integration_id,
                    integration_key=integration_key,
                    return_url=return_url,
                    result_url=result_url
                )
                print("PaynowService initialized successfully")
                
                # Check if we have real credentials
                if integration_id == 'YOUR_INTEGRATION_ID':
                    print("Warning: Using default/test Paynow credentials")
                else:
                    print(f"PaynowService initialized with integration ID: {integration_id}")
                    
            except Exception as e:
                print(f"Failed to initialize PaynowService: {e}")
                self.paynow_service = None
    
    def process_transaction(self, transaction_reference):
        """Process a transaction using its reference.
        
        Args:
            transaction_reference (str): The transaction reference to process
            
        Returns:
            dict: Processing result
        """
        try:
            # Find the transaction
            transaction = Transaction.query.filter_by(reference=transaction_reference).first()
            if not transaction:
                return {
                    'status': 'error',
                    'message': f'Transaction not found: {transaction_reference}'
                }
            
            # Check if already processed
            if transaction.status in ['paid', 'completed']:
                return {
                    'status': 'success',
                    'message': 'Transaction already completed',
                    'transaction_id': transaction.id,
                    'reference': transaction.reference,
                    'amount': float(transaction.amount),
                    'status_code': transaction.status
                }
            
            # Process the payment using existing create_payment logic
            result= self.create_payment(
                transaction.phone_number,
                float(transaction.amount),
                transaction.method
            )
            # debug results
            if result.get('status') == 'success':
                # Update the original transaction with the new processing data
                transaction.poll_url = result.get('poll_url')
                transaction.instructions = result.get('instructions')
                transaction.paynow_reference = result.get('paynow_reference')
                transaction.redirect_url = result.get('redirect_url', '')
                
                # Handle OMari-specific fields
                if transaction.method == 'omari':
                    transaction.remoteotpurl = result.get('remoteotpurl')
                    transaction.otpreference = result.get('otpreference')
                
                transaction.status = 'sent'  # Update status to sent
                db.session.commit()
                
                return {
                    'status': 'success',
                    'message': 'Transaction processed successfully',
                    'transaction_id': transaction.id,
                    'reference': transaction.reference,
                    'amount': float(transaction.amount),
                    'poll_url': result.get('poll_url'),
                    'instructions': result.get('instructions'),
                    'paynow_reference': result.get('paynow_reference'),
                    'redirect_url': result.get('redirect_url'),
                    'has_redirect': result.get('has_redirect', False),
                    'remoteotpurl': result.get('remoteotpurl'),
                    'otpreference': result.get('otpreference')
                }
            else:
                # Processing failed
                transaction.status = 'failed'
                db.session.commit()
                
                return {
                    'status': 'error',
                    'message': result.get('message', 'Transaction processing failed'),
                    'errors': result.get('errors', []),
                    'transaction_id': transaction.id,
                    'reference': transaction.reference
                }
                
        except Exception as e:
            db.session.rollback()
            return {
                'status': 'error',
                'message': f'Transaction processing failed: {str(e)}',
                'reference': transaction_reference
            }

    def create_payment(self, phone_number, amount, method):
        """Create a new payment transaction.
        
        Args:
            phone_number (str): Customer phone number
            amount (float): Payment amount
            method (str): Payment method
        
        Returns:
            dict: Payment response data
        """
        # Generate unique reference
        reference = f"LOAN_{uuid.uuid4().hex[:8].upper()}"
        
        try:
            # Send payment request to Paynow
            paynow_response = self.paynow_service.create_payment(
                reference, amount, phone_number, method
            )
            print(f"payniw response {paynow_response}")
            if paynow_response.success:
                # Get instructions
                instructions = paynow_response.get_instructions()
                
                # Create transaction record
                transaction = Transaction(
                    reference=reference,
                    phone_number=phone_number,
                    amount=amount,
                    method=method,
                    poll_url=paynow_response.get_poll_url(),
                    status='pending',
                    instructions=instructions,
                    paynow_reference=paynow_response.get_paynow_reference(),
                    hash=paynow_response.get_hash(),
                    redirect_url=paynow_response.redirect_url or '',
                    has_redirect=paynow_response.has_redirect(),
                    # OMari-specific fields
                    remoteotpurl=paynow_response.remoteotpurl if method == 'omari' else None,
                    otpreference=paynow_response.otpreference if method == 'omari' else None
                )
                
                # Save to database
                db.session.add(transaction)
                db.session.commit()
                print(f"Transaction {reference} saved to database")
                
                # Return response data
                return {
                    "status": "success",
                    "reference": reference,
                    "poll_url": paynow_response.get_poll_url(),
                    "instructions": instructions,
                    "message": "Payment request sent successfully",
                    "paynow_reference": paynow_response.get_paynow_reference(),
                    "redirect_url": paynow_response.redirect_url or '',
                    "has_redirect": paynow_response.has_redirect(),
                    "hash": paynow_response.get_hash(),
                    "paynow_status": paynow_response.data.get('status', '') if paynow_response.data else '',
                    # OMari-specific fields
                    "remoteotpurl": paynow_response.remoteotpurl if method == 'omari' else None,
                    "otpreference": paynow_response.otpreference if method == 'omari' else None
                }
            else:
                # Payment failed
                errors = getattr(paynow_response.response, 'errors', [])
                if errors:
                    errors = [str(error) for error in errors]
                
                return {
                    "status": "error",
                    "message": "Failed to process payment",
                    "errors": errors,
                    "debug_info": {
                        "reference": reference,
                        "integration_id": self.paynow_service.integration_id,
                        "credentials_configured": self.paynow_service.integration_id != 'YOUR_INTEGRATION_ID'
                    }
                }
        
        except Exception as e:
            db.session.rollback()
            return {
                "status": "error",
                "message": f"Payment creation failed: {str(e)}"
            }
    
    def create_test_payment(self, phone_number, amount, method):
        """Create a test payment transaction.
        
        Args:
            phone_number (str): Customer phone number
            amount (float): Payment amount
            method (str): Payment method
        
        Returns:
            dict: Test payment response data
        """
        # Generate unique reference
        reference = f"TEST_{uuid.uuid4().hex[:8].upper()}"
        
        try:
            # Create mock transaction
            transaction = Transaction(
                reference=reference,
                phone_number=phone_number,
                amount=amount,
                method=method,
                poll_url=f'http://localhost:5000/mock/poll/{reference}',
                status='pending',
                instructions=f'This is a test payment for {method.upper()}. Send ${amount} to {phone_number}',
                is_test=True,
                # Add OMari-specific mock data
                remoteotpurl=f'https://mock-omari-otp.com/pay/{reference}' if method == 'omari' else None,
                otpreference=f'OTP_{reference}' if method == 'omari' else None
            )
            
            # Save to database
            db.session.add(transaction)
            db.session.commit()
            print(f"Test transaction {reference} saved to database")
            
            response_data = {
                "status": "success",
                "reference": reference,
                "poll_url": f'http://localhost:5000/mock/poll/{reference}',
                "instructions": f'TEST: Send ${amount} via {method.upper()} to {phone_number}',
                "message": "Test payment request created successfully",
                "note": "This is a test transaction - no real payment will be processed"
            }
            
            # Add OMari-specific response data
            if method == 'omari':
                response_data['remoteotpurl'] = transaction.remoteotpurl
                response_data['otpreference'] = transaction.otpreference
            
            return response_data
        
        except Exception as e:
            db.session.rollback()
            return {
                "status": "error",
                "message": f"Test payment creation failed: {str(e)}"
            }
    
    def check_payment_status(self, reference):
        """Check payment status for a transaction.
        
        Args:
            reference (str): Transaction reference
        
        Returns:
            dict: Status response data
        """
        try:
            # Find transaction
            transaction = Transaction.query.filter_by(reference=reference).first()
            
            if not transaction:
                return {"error": "Transaction not found"}
            
            # Check status with Paynow
            status = self.paynow_service.check_transaction_status(transaction.poll_url)
            
            # Update transaction status
            transaction.status = str(status.status) if status.status else 'unknown'
            transaction.updated_at = datetime.utcnow()
            
            if hasattr(status, 'paid') and status.paid:
                transaction.paid_at = datetime.utcnow()
                
                # Update loan balance if this is a loan payment
                if transaction.loan_id and transaction.loan:
                    loan = transaction.loan
                    loan.outstanding_balance -= transaction.amount
                    if loan.outstanding_balance <= 0:
                        loan.status = 'completed'
                        loan.outstanding_balance = 0
            
            db.session.commit()
            
            return {
                "reference": reference,
                "status": str(status.status) if status.status else 'unknown',
                "paid": bool(getattr(status, 'paid', False)),
                "amount": transaction.amount,
                "method": transaction.method,
                "created_at": transaction.created_at.isoformat() if transaction.created_at else None,
                "loan_balance_updated": bool(transaction.loan_id and getattr(status, 'paid', False))
            }
        
        except Exception as e:
            db.session.rollback()
            return {"error": f"Status check failed: {str(e)}"}
    
    def submit_otp(self, reference, otp):
        """Submit OTP for OMari payment.
        
        Args:
            reference (str): Transaction reference
            otp (str): OTP code
        
        Returns:
            dict: OTP submission response
        """
        try:
            # Find transaction
            transaction = Transaction.query.filter_by(reference=reference).first()
            
            if not transaction:
                return {"error": "Transaction not found"}
            
            # Validate this is an OMari transaction with OTP capability
            if transaction.method != 'omari':
                return {"error": "OTP submission only available for OMari payments"}
            
            if not transaction.remoteotpurl:
                return {"error": "No OTP URL available for this transaction"}
            
            # Submit OTP to Paynow
            response_data = self.paynow_service.submit_otp(
                transaction.remoteotpurl, 
                self.paynow_service.integration_id, 
                otp,
                self.paynow_service.paynow
            )
            
            # Update transaction with OTP response
            transaction.set_otp_response(response_data)
            
            if response_data.get('status') == 'Error':
                db.session.commit()
                
                return {
                    "status": "error",
                    "message": "OTP submission failed",
                    "error": response_data.get('error', 'Invalid OTP'),
                    "paynow_response": response_data
                }
            else:
                # Success - payment is being processed
                transaction.status = response_data.get('status', 'Processing')
                if response_data.get('paynowreference'):
                    transaction.paynow_reference = response_data.get('paynowreference')
                if response_data.get('pollurl'):
                    transaction.poll_url = response_data.get('pollurl')
                
                db.session.commit()
                print(f"Transaction {reference} updated with OTP response")
                
                return {
                    "status": "success",
                    "message": "OTP submitted successfully",
                    "payment_status": response_data.get('status', 'Processing'),
                    "reference": reference,
                    "paynow_reference": response_data.get('paynowreference', ''),
                    "poll_url": response_data.get('pollurl', ''),
                    "paynow_response": response_data
                }
        
        except Exception as e:
            db.session.rollback()
            return {
                "status": "error",
                "message": f"OTP submission failed: {str(e)}"
            }
    
    def handle_paynow_result(self, result_data):
        """Handle Paynow result callback.
        
        Args:
            result_data (dict): Result data from Paynow
        
        Returns:
            bool: Success status
        """
        try:
            reference = result_data.get('reference')
            if reference:
                transaction = Transaction.query.filter_by(reference=reference).first()
                if transaction:
                    transaction.set_paynow_result(result_data)
                    
                    # Update loan balance if payment is completed
                    if result_data.get('paynowreference') == 'Paid' and transaction.loan_id:
                        loan = transaction.loan
                        loan.outstanding_balance -= transaction.amount
                        if loan.outstanding_balance <= 0:
                            loan.status = 'completed'
                            loan.outstanding_balance = 0
                    
                    db.session.commit()
                    print(f"Transaction {reference} updated with Paynow result")
                    return True
                else:
                    print(f"Transaction not found for reference: {reference}")
            return False
        
        except Exception as e:
            db.session.rollback()
            print(f"Error handling Paynow result: {e}")
            return False
    
    def get_all_transactions(self):
        """Get all transactions.
        
        Returns:
            list: List of transaction dictionaries
        """
        try:
            transactions = Transaction.query.order_by(Transaction.created_at.desc()).all()
            return [transaction.to_dict() for transaction in transactions]
        
        except Exception as e:
            return {"error": f"Failed to retrieve transactions: {str(e)}"}