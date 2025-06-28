"""Enhanced transaction routes with loan integration."""
from flask import Blueprint, request
from utils.responses import APIResponse
from utils.validators import PaymentValidator, ValidationError
from services.payment_service import PaymentService
from models.transaction import Transaction
from models.loan import Loan
from models.user import User
from utils.database import db

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
    Check payment status with loan updates
    ---
    tags:
      - Payment
    parameters:
      - in: path
        name: reference
        type: string
        required: true
        description: Payment reference ID
        example: "abcsl00a.20250628143022.L001"
    responses:
      200:
        description: Payment status retrieved
        schema:
          type: object
          properties:
            reference:
              type: string
              example: "abcsl00a.20250628143022.L001"
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
            loan_id:
              type: string
              example: "L001"
            loan_balance_updated:
              type: boolean
              example: true
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
        
        # Find transaction to update loan if paid
        transaction = Transaction.query.filter_by(reference=validated_reference).first()
        if transaction and result.get('paid') and not transaction.paid:
            # Mark transaction as completed and update loan
            transaction.mark_as_completed()
            result['loan_balance_updated'] = True
            
            # Add loan information to response
            if transaction.loan:
                result['loan_info'] = {
                    'loan_id': transaction.loan.loan_id,
                    'outstanding_balance': float(transaction.loan.outstanding_balance),
                    'status': transaction.loan.status
                }
        
        return APIResponse.success(result, "Payment status retrieved")
    
    except ValidationError as e:
        return APIResponse.validation_error(str(e))
    except Exception as e:
        return APIResponse.internal_error(f"Status check failed: {str(e)}")

@transaction_bp.route('/transactions', methods=['GET'])
def get_transactions():
    """
    Get all transactions with loan information (for debugging)
    ---
    tags:
      - Debug
    parameters:
      - in: query
        name: loan_id
        type: string
        description: Filter by loan ID
      - in: query
        name: status
        type: string
        description: Filter by status
      - in: query
        name: limit
        type: integer
        description: Limit number of results
        default: 50
    responses:
      200:
        description: List of all transactions with loan information
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
                    example: "abcsl00a.20250628143022.L001"
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
                  loan_reference:
                    type: string
                    example: "L001"
                  customer_name:
                    type: string
                    example: "John Doe"
                  created_at:
                    type: string
                    example: "2025-06-27T10:30:00.123456"
    """
    try:
        # Get query parameters
        loan_id = request.args.get('loan_id')
        status_filter = request.args.get('status')
        limit = min(request.args.get('limit', 50, type=int), 200)
        
        # Build query
        query = Transaction.query
        
        # Apply filters
        if loan_id:
            loan = Loan.query.filter_by(loan_id=loan_id).first()
            if loan:
                query = query.filter_by(loan_id=loan.id)
            else:
                return APIResponse.not_found(f"Loan {loan_id} not found")
        
        if status_filter:
            query = query.filter_by(status=status_filter)
        
        # Order by most recent and limit
        transactions = query.order_by(Transaction.created_at.desc()).limit(limit).all()
        
        # Build enhanced response with loan information
        transactions_data = []
        for tx in transactions:
            tx_dict = tx.to_dict()
            
            # Add additional loan and customer information
            if tx.loan:
                tx_dict['loan_details'] = {
                    'loan_id': tx.loan.loan_id,
                    'original_amount': float(tx.loan.original_amount),
                    'outstanding_balance': float(tx.loan.outstanding_balance),
                    'status': tx.loan.status,
                    'progress_percentage': tx.loan.progress_percentage
                }
            
            if tx.user:
                tx_dict['customer_details'] = {
                    'id': tx.user.id,
                    'username': tx.user.username,
                    'full_name': tx.user.full_name,
                    'phone_number': tx.user.phone_number
                }
            
            transactions_data.append(tx_dict)
        
        # Add summary information
        summary = {
            'total_transactions': len(transactions_data),
            'filters_applied': {
                'loan_id': loan_id,
                'status': status_filter,
                'limit': limit
            }
        }
        
        return APIResponse.success(
            data=transactions_data,
            message="Transactions retrieved successfully",
            summary=summary
        )
    
    except Exception as e:
        return APIResponse.internal_error(f"Failed to retrieve transactions: {str(e)}")

@transaction_bp.route('/loans/<loan_id>/transactions', methods=['GET'])
def get_loan_transactions(loan_id):
    """
    Get all transactions for a specific loan
    ---
    tags:
      - Loans
    parameters:
      - in: path
        name: loan_id
        type: string
        required: true
        description: Loan ID (e.g., L001)
    responses:
      200:
        description: Loan transactions retrieved
      404:
        description: Loan not found
    """
    try:
        # Find loan
        loan = Loan.query.filter_by(loan_id=loan_id).first()
        if not loan:
            return APIResponse.not_found(f"Loan {loan_id} not found")
        
        # Get transactions for this loan
        transactions = Transaction.query.filter_by(loan_id=loan.id).order_by(
            Transaction.created_at.desc()
        ).all()
        
        # Build response
        transactions_data = [tx.to_dict() for tx in transactions]
        
        # Add loan summary
        loan_summary = loan.to_dict()
        loan_summary['payment_summary'] = {
            'total_payments': len(transactions_data),
            'completed_payments': len([tx for tx in transactions_data if tx['paid']]),
            'pending_payments': len([tx for tx in transactions_data if not tx['paid']]),
            'total_amount_paid_via_transactions': sum(tx['amount'] for tx in transactions_data if tx['paid'])
        }
        
        return APIResponse.success({
            'loan': loan_summary,
            'transactions': transactions_data
        })
    
    except Exception as e:
        return APIResponse.internal_error(f"Failed to get loan transactions: {str(e)}")

@transaction_bp.route('/customers/<int:customer_id>/transactions', methods=['GET'])
def get_customer_transactions(customer_id):
    """
    Get all transactions for a specific customer
    ---
    tags:
      - Customers
    parameters:
      - in: path
        name: customer_id
        type: integer
        required: true
        description: Customer user ID
    responses:
      200:
        description: Customer transactions retrieved
      404:
        description: Customer not found
    """
    try:
        # Find customer
        customer = User.query.filter_by(id=customer_id, role='customer').first()
        if not customer:
            return APIResponse.not_found(f"Customer {customer_id} not found")
        
        # Get transactions for this customer
        transactions = Transaction.query.filter_by(user_id=customer_id).order_by(
            Transaction.created_at.desc()
        ).all()
        
        # Get customer's loans
        loans = Loan.query.filter_by(user_id=customer_id).all()
        
        # Build response
        transactions_data = [tx.to_dict() for tx in transactions]
        loans_data = [loan.to_dict() for loan in loans]
        
        customer_summary = customer.to_dict()
        customer_summary['transaction_summary'] = {
            'total_transactions': len(transactions_data),
            'completed_transactions': len([tx for tx in transactions_data if tx['paid']]),
            'total_amount_transacted': sum(tx['amount'] for tx in transactions_data),
            'total_amount_paid': sum(tx['amount'] for tx in transactions_data if tx['paid'])
        }
        
        return APIResponse.success({
            'customer': customer_summary,
            'loans': loans_data,
            'transactions': transactions_data
        })
    
    except Exception as e:
        return APIResponse.internal_error(f"Failed to get customer transactions: {str(e)}")

@transaction_bp.route('/stats', methods=['GET'])
def get_transaction_stats():
    """
    Get transaction statistics
    ---
    tags:
      - Analytics
    responses:
      200:
        description: Transaction statistics
    """
    try:
        stats = Transaction.get_summary_stats()
        
        # Add additional breakdown
        from datetime import datetime, timedelta
        
        # Today's stats
        today = datetime.utcnow().date()
        today_stats = Transaction.query.filter(
            Transaction.created_at >= today
        )
        
        today_summary = {
            'transactions_today': today_stats.count(),
            'amount_today': float(db.session.query(db.func.sum(Transaction.amount)).filter(
                Transaction.created_at >= today
            ).scalar() or 0),
            'completed_today': today_stats.filter(
                Transaction.status.in_(['completed', 'paid'])
            ).count()
        }
        
        # Method breakdown
        method_stats = db.session.query(
            Transaction.method,
            db.func.count(Transaction.id).label('count'),
            db.func.sum(Transaction.amount).label('total_amount')
        ).group_by(Transaction.method).all()
        
        method_breakdown = [
            {
                'method': method,
                'count': count,
                'total_amount': float(total_amount),
                'percentage': round((count / max(stats['total_transactions'], 1)) * 100, 2)
            }
            for method, count, total_amount in method_stats
        ]
        
        enhanced_stats = {
            **stats,
            'today': today_summary,
            'method_breakdown': method_breakdown,
            'generated_at': datetime.utcnow().isoformat()
        }
        
        return APIResponse.success(enhanced_stats)
    
    except Exception as e:
        return APIResponse.internal_error(f"Failed to get transaction stats: {str(e)}")
