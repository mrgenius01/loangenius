"""Customer routes for loan management."""
from flask import Blueprint, request, jsonify
from flask_login import login_user, login_required, current_user, logout_user
from models.user import User, LoginAttempt
from models.loan import Loan
from models.transaction import Transaction
from utils.database import db
from utils.responses import APIResponse
from utils.validators import PaymentValidator, ValidationError
from services.payment_service import PaymentService
from datetime import datetime

customer_bp = Blueprint('customer', __name__, url_prefix='/customer')

# Payment service will be injected when blueprint is registered
payment_service = None

def init_customer_routes(service):
    """Initialize customer routes with payment service dependency."""
    global payment_service
    payment_service = service

@customer_bp.route('/login', methods=['POST'])
def login():
    """Customer login endpoint."""
    try:
        data = request.get_json()
        if not data:
            return APIResponse.validation_error('No data provided')
        
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return APIResponse.validation_error('Username and password required')
        
        # Log login attempt
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent', '')
        
        # Find user (customer only)
        user = User.query.filter_by(username=username, role='customer', is_active=True).first()
        
        if user and user.check_password(password):
            # Check if account is locked
            if user.is_locked():
                return APIResponse.error('Account is temporarily locked due to failed login attempts', 423)
            
            # Successful login
            login_user(user)
            user.reset_failed_attempts()
            
            # Log successful attempt
            attempt = LoginAttempt(
                username=username,
                ip_address=ip_address,
                user_agent=user_agent,
                success=True
            )
            db.session.add(attempt)
            db.session.commit()
            
            return APIResponse.success({
                'user': user.to_dict(),
                'message': 'Login successful'
            })
        else:
            # Failed login
            if user:
                user.increment_failed_attempts()
            
            # Log failed attempt
            attempt = LoginAttempt(
                username=username,
                ip_address=ip_address,
                user_agent=user_agent,
                success=False
            )
            db.session.add(attempt)
            db.session.commit()
            
            return APIResponse.error('Invalid credentials', 401)
            
    except Exception as e:
        return APIResponse.internal_error(f'Login failed: {str(e)}')

@customer_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """Customer logout endpoint."""
    try:
        logout_user()
        return APIResponse.success({'message': 'Logout successful'})
    except Exception as e:
        return APIResponse.internal_error(f'Logout failed: {str(e)}')

@customer_bp.route('/profile', methods=['GET'])
@login_required
def get_profile():
    """Get customer profile."""
    try:
        if current_user.role != 'customer':
            return APIResponse.error('Access denied', 403)
        
        return APIResponse.success({
            'user': current_user.to_dict()
        })
    except Exception as e:
        return APIResponse.internal_error(f'Failed to get profile: {str(e)}')

@customer_bp.route('/loans', methods=['GET'])
@login_required
def get_user_loans():
    """Get customer's loans with detailed information."""
    try:
        if current_user.role != 'customer':
            return APIResponse.error('Access denied', 403)
        
        # Get all loans for the customer
        loans = Loan.query.filter_by(user_id=current_user.id).order_by(Loan.created_at.desc()).all()
        loans_data = [loan.to_dict() for loan in loans]
        
        # Calculate summary
        active_loans = [loan for loan in loans_data if loan['is_active']]
        total_outstanding = sum(loan['outstanding_balance'] for loan in active_loans)
        total_original = sum(loan['original_amount'] for loan in loans_data)
        total_paid = sum(loan['paid_amount'] for loan in loans_data)
        
        return APIResponse.success({
            'loans': loans_data,
            'summary': {
                'total_loans': len(loans_data),
                'active_loans': len(active_loans),
                'completed_loans': len([l for l in loans_data if l['status'] == 'completed']),
                'total_outstanding': total_outstanding,
                'total_original_amount': total_original,
                'total_paid_amount': total_paid
            }
        })
        
    except Exception as e:
        return APIResponse.internal_error(f'Failed to get loans: {str(e)}')

@customer_bp.route('/loan/<loan_id>', methods=['GET'])
@login_required
def get_loan_details(loan_id):
    """Get detailed loan information including payment history."""
    try:
        if current_user.role != 'customer':
            return APIResponse.error('Access denied', 403)
        
        # Find loan
        loan = Loan.query.filter_by(
            loan_id=loan_id, 
            user_id=current_user.id
        ).first()
        
        if not loan:
            return APIResponse.not_found('Loan not found')
        
        # Get payment history
        transactions = Transaction.query.filter_by(
            loan_id=loan.id,
            user_id=current_user.id
        ).order_by(Transaction.created_at.desc()).all()
        
        transactions_data = [tx.to_dict() for tx in transactions]
        
        return APIResponse.success({
            'loan': loan.to_dict(),
            'payment_history': transactions_data,
            'payment_summary': {
                'total_payments': len(transactions_data),
                'completed_payments': len([tx for tx in transactions_data if tx['paid']]),
                'pending_payments': len([tx for tx in transactions_data if not tx['paid']]),
                'total_paid_via_transactions': sum(tx['amount'] for tx in transactions_data if tx['paid'])
            }
        })
        
    except Exception as e:
        return APIResponse.internal_error(f'Failed to get loan details: {str(e)}')

@customer_bp.route('/loan/<loan_id>/payment', methods=['POST'])
@login_required
def make_payment(loan_id):
    """Make a payment for a specific loan."""
    try:
        if current_user.role != 'customer':
            return APIResponse.error('Access denied', 403)
        
        data = request.get_json()
        if not data:
            return APIResponse.validation_error('No payment data provided')
        
        # Validate inputs
        try:
            amount = PaymentValidator.validate_amount(data.get('amount'))
            phone_number = PaymentValidator.validate_phone_number(data.get('phone_number'))
            method = PaymentValidator.validate_method(data.get('method', 'ecocash'))
        except ValidationError as e:
            return APIResponse.validation_error(str(e))
        
        # Find loan
        loan = Loan.query.filter_by(
            loan_id=loan_id, 
            user_id=current_user.id,
            status='active'
        ).first()
        
        if not loan:
            return APIResponse.not_found('Active loan not found')
        
        # Check amount against outstanding balance
        if amount > float(loan.outstanding_balance):
            return APIResponse.validation_error(
                f'Amount ${amount} exceeds outstanding balance ${loan.outstanding_balance}'
            )
        
        # Create transaction
        transaction = Transaction(
            user_id=current_user.id,
            loan_id=loan.id,
            phone_number=phone_number,
            amount=amount,
            method=method,
            transaction_type='loan_payment',
            description=f'Payment for loan {loan_id}'
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        # Process with payment service
        result = payment_service.create_payment(phone_number, amount, method)
        
        if result.get('status') == 'success':
            # Update transaction with payment gateway details
            if 'data' in result:
                payment_data = result['data']
                transaction.paynow_reference = payment_data.get('paynow_reference')
                transaction.poll_url = payment_data.get('poll_url')
                transaction.redirect_url = payment_data.get('redirect_url')
                transaction.remoteotpurl = payment_data.get('remoteotpurl')
                transaction.instructions = payment_data.get('instructions')
                db.session.commit()
        
        return APIResponse.success({
            'transaction': transaction.to_dict(),
            'payment_result': result,
            'loan': loan.to_dict()
        })
        
    except ValidationError as e:
        return APIResponse.validation_error(str(e))
    except Exception as e:
        db.session.rollback()
        return APIResponse.internal_error(f'Payment failed: {str(e)}')

@customer_bp.route('/transactions', methods=['GET'])
@login_required
def get_customer_transactions():
    """Get customer's transaction history."""
    try:
        if current_user.role != 'customer':
            return APIResponse.error('Access denied', 403)
        
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        # Get transactions
        transactions_query = Transaction.query.filter_by(
            user_id=current_user.id
        ).order_by(Transaction.created_at.desc())
        
        transactions_paginated = transactions_query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        transactions_data = [tx.to_dict() for tx in transactions_paginated.items]
        
        return APIResponse.success({
            'transactions': transactions_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': transactions_paginated.total,
                'pages': transactions_paginated.pages,
                'has_next': transactions_paginated.has_next,
                'has_prev': transactions_paginated.has_prev
            }
        })
        
    except Exception as e:
        return APIResponse.internal_error(f'Failed to get transactions: {str(e)}')

@customer_bp.route('/payment/status/<reference>', methods=['GET'])
@login_required
def check_payment_status(reference):
    """Check payment status for customer's transaction."""
    try:
        if current_user.role != 'customer':
            return APIResponse.error('Access denied', 403)
        
        # Validate reference
        validated_reference = PaymentValidator.validate_reference(reference)
        
        # Find transaction belonging to current user
        transaction = Transaction.query.filter_by(
            reference=validated_reference,
            user_id=current_user.id
        ).first()
        
        if not transaction:
            return APIResponse.not_found('Transaction not found')
        
        # Check payment status
        result = payment_service.check_payment_status(validated_reference)
        
        if 'error' in result:
            return APIResponse.error(result['error'])
        
        # If payment is completed, update loan balance
        if result.get('paid') and not transaction.paid:
            transaction.mark_as_completed()
        
        return APIResponse.success(result, "Payment status retrieved")
    
    except ValidationError as e:
        return APIResponse.validation_error(str(e))
    except Exception as e:
        return APIResponse.internal_error(f"Status check failed: {str(e)}")

# Customer dashboard summary
@customer_bp.route('/dashboard', methods=['GET'])
@login_required
def get_dashboard():
    """Get customer dashboard data."""
    try:
        if current_user.role != 'customer':
            return APIResponse.error('Access denied', 403)
        
        # Get active loans
        active_loans = current_user.active_loans
        
        # Get recent transactions (last 10)
        recent_transactions = Transaction.query.filter_by(
            user_id=current_user.id
        ).order_by(Transaction.created_at.desc()).limit(10).all()
        
        # Calculate summary
        total_outstanding = sum(float(loan.outstanding_balance) for loan in active_loans)
        total_original = sum(float(loan.original_amount) for loan in current_user.loans)
        total_paid = total_original - total_outstanding
        
        dashboard_data = {
            'user': current_user.to_dict(),
            'summary': {
                'active_loans': len(active_loans),
                'total_loans': current_user.loans.count(),
                'total_outstanding': total_outstanding,
                'total_paid': total_paid,
                'payment_progress': round((total_paid / max(total_original, 1)) * 100, 2)
            },
            'active_loans': [loan.to_dict() for loan in active_loans],
            'recent_transactions': [tx.to_dict() for tx in recent_transactions]
        }
        
        return APIResponse.success(dashboard_data)
        
    except Exception as e:
        return APIResponse.internal_error(f'Failed to get dashboard: {str(e)}')
