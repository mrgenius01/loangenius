"""Payment business logic service."""
import uuid
from datetime import datetime
from models.transaction import Transaction
from services.paynow_service import PaynowService
from utils.database import db

class PaymentService:
    """Service class for payment business logic."""
    
    def __init__(self, paynow_service):
        """Initialize payment service with Paynow service."""
        self.paynow_service = paynow_service
    
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
            
            db.session.commit()
            
            return {
                "reference": reference,
                "status": str(status.status) if status.status else 'unknown',
                "paid": bool(getattr(status, 'paid', False)),
                "amount": transaction.amount,
                "method": transaction.method,
                "created_at": transaction.created_at.isoformat() if transaction.created_at else None
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
