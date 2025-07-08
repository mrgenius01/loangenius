"""Dashboard routes for admin interface."""
from flask import Blueprint, render_template, jsonify, request
from datetime import datetime, timedelta
from sqlalchemy import func, desc
from utils.validators import PaymentValidator, ValidationError, validate_json_data
from models.transaction import Transaction
from utils.database import db
from utils.responses import APIResponse, success_response, error_response
from utils.security import login_required, admin_required, csrf_required, rate_limit, api_admin_required
from services.auth_service import AuthService
from services.payment_service import PaymentService
from flasgger import swag_from

# Initialize payment service
payment_service = None
try:
    from flask import current_app
    payment_service = PaymentService(None)  # Will be properly initialized when needed
except ImportError:
    pass

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/admin')

@dashboard_bp.route('/')
@login_required
@admin_required
def dashboard_home():
    """Admin Dashboard Home."""
    csrf_token = AuthService.generate_csrf_token()
    return render_template('dashboard/enhanced.html', csrf_token=csrf_token)

@dashboard_bp.route('/api/stats')
@api_admin_required
@rate_limit(max_requests=30, window=60)
def get_dashboard_stats():
    """
    Get dashboard statistics
    ---
    tags:
      - Dashboard
    responses:
      200:
        description: Dashboard statistics
        schema:
          type: object
          properties:
            total_transactions:
              type: integer
            total_amount:
              type: number
            successful_payments:
              type: integer
            pending_payments:
              type: integer
            failed_payments:
              type: integer
            today_transactions:
              type: integer
            today_amount:
              type: number
    """
    try:
        # Get date ranges
        today = datetime.utcnow().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        # Total stats
        total_transactions = Transaction.query.count()
        total_amount = db.session.query(func.sum(Transaction.amount)).scalar() or 0
        
        # Status breakdown
        successful = Transaction.query.filter_by(status='paid').count()
        pending = Transaction.query.filter(Transaction.status.in_(['pending', 'sent'])).count()
        failed = Transaction.query.filter_by(status='cancelled').count()
        
        # Today's stats
        today_transactions = Transaction.query.filter(
            func.date(Transaction.created_at) == today
        ).count()
        
        today_amount = db.session.query(func.sum(Transaction.amount)).filter(
            func.date(Transaction.created_at) == today
        ).scalar() or 0
        
        # Weekly trend
        weekly_stats = db.session.query(
            func.date(Transaction.created_at).label('date'),
            func.count(Transaction.id).label('count'),
            func.sum(Transaction.amount).label('amount')
        ).filter(
            Transaction.created_at >= week_ago
        ).group_by(
            func.date(Transaction.created_at)
        ).all()
        
        # Payment method breakdown
        method_stats = db.session.query(
            Transaction.method,
            func.count(Transaction.id).label('count'),
            func.sum(Transaction.amount).label('amount')
        ).group_by(Transaction.method).all()
        
        return success_response({
            'total_transactions': total_transactions,
            'total_amount': float(total_amount),
            'successful_payments': successful,
            'pending_payments': pending,
            'failed_payments': failed,
            'today_transactions': today_transactions,
            'today_amount': float(today_amount),            'weekly_trend': [
                {
                    'date': str(stat.date),
                    'count': stat.count,
                    'amount': float(stat.amount or 0)
                } for stat in weekly_stats
            ],
            'method_breakdown': [
                {
                    'method': stat.method,
                    'count': stat.count,
                    'amount': float(stat.amount or 0)
                } for stat in method_stats
            ]
        })
        
    except Exception as e:
        return error_response(f"Failed to get dashboard stats: {str(e)}", 500)

@dashboard_bp.route('/api/overview')
@api_admin_required
@rate_limit(max_requests=30, window=60)
def get_dashboard_overview():
    """
    Get comprehensive dashboard overview with users, loans, transactions and analytics
    Compatible with SQL Server, MySQL, and SQLite
    """
    from models.loan import Loan
    from models.user import User, LoginAttempt
    from models.transaction import Transaction
    from utils.database import db
    from sqlalchemy import func, and_
    from datetime import datetime, timedelta
    import logging

    logger = logging.getLogger(__name__)

    try:
        # Date ranges
        now = datetime.utcnow()
        today = now.date()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        # Transaction stats with SQL Server compatibility
        total_transactions = Transaction.query.count()
        total_amount = float(db.session.query(func.sum(Transaction.amount)).scalar() or 0)
        successful_payments = Transaction.query.filter_by(status='paid').count()
        pending_payments = Transaction.query.filter(Transaction.status.in_(['pending','sent'])).count()
        failed_payments = Transaction.query.filter_by(status='cancelled').count()
        
        # Use CAST for SQL Server compatibility instead of func.date()
        today_transactions = Transaction.query.filter(
            func.cast(Transaction.created_at, db.Date) == today
        ).count()
        
        today_amount = float(db.session.query(func.sum(Transaction.amount)).filter(
            func.cast(Transaction.created_at, db.Date) == today
        ).scalar() or 0)

        # User and loan stats
        total_users = User.query.count()
        total_loans = Loan.query.count()
        active_loans = Loan.query.filter_by(status='active').count()

        # Build response
        data = {
            'total_transactions': total_transactions,
            'total_amount': total_amount,
            'successful_payments': successful_payments,
            'pending_payments': pending_payments,
            'failed_payments': failed_payments,
            'today_transactions': today_transactions,
            'today_amount': today_amount,
            'total_users': total_users,
            'total_loans': total_loans,
            'active_loans': active_loans
        }
        # Recent activity: last 5 loans
        recent_loans = Loan.query.order_by(Loan.created_at.desc()).limit(5).all()
        data['recent_activity'] = {
            'loans': [loan.to_dict() for loan in recent_loans]
        }
        # Alerts placeholder
        data['alerts'] = []
        return success_response(data)
    except Exception as e:
        return error_response(f"Failed to get dashboard overview: {str(e)}", 500)

@dashboard_bp.route('/api/transactions')
@api_admin_required
@rate_limit(max_requests=60, window=60)
def get_dashboard_transactions():
    """
    Get transactions for dashboard with enhanced data structure
    ---
    tags:
      - Dashboard
    parameters:
      - name: page
        in: query
        type: integer
        default: 1
      - name: per_page
        in: query
        type: integer
        default: 10
      - name: status
        in: query
        type: string
      - name: method
        in: query
        type: string
      - name: search
        in: query
        type: string
    responses:
      200:
        description: Paginated transactions with summary
    """
    try:
        from models.transaction import Transaction
        from sqlalchemy import desc, func
        
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        status_filter = request.args.get('status')
        method_filter = request.args.get('method')
        search = request.args.get('search')
        
        query = Transaction.query
        
        # Apply filters
        if status_filter:
            query = query.filter(Transaction.status == status_filter)
        if method_filter:
            query = query.filter(Transaction.method == method_filter)
        if search:
            query = query.filter(
                Transaction.reference.contains(search) |
                Transaction.phone_number.contains(search) |
                (Transaction.paynow_reference.contains(search) if Transaction.paynow_reference else False)
            )
        
        # Order by latest first
        query = query.order_by(desc(Transaction.created_at))
        
        # Paginate
        pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Get transaction summary
        total_transactions = Transaction.query.count()
        total_amount = db.session.query(func.sum(Transaction.amount)).scalar() or 0
        successful_transactions = Transaction.query.filter(
            Transaction.status.in_(['completed', 'paid'])
        ).count()
        
        # Convert transactions to dict using the model method
        transactions = []
        for t in pagination.items:
            tx_dict = t.to_dict()
            transactions.append(tx_dict)
        
        return success_response({
            'transactions': transactions,
            'summary': {
                'total_transactions': total_transactions,
                'total_amount': float(total_amount),
                'successful_transactions': successful_transactions
            },
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        })
        
    except Exception as e:
        return error_response(f"Failed to get transactions: {str(e)}", 500)

@dashboard_bp.route('/api/system/health')
@api_admin_required
@rate_limit(max_requests=20, window=60)
def system_health():
    """
    Get system health status
    ---
    tags:
      - Dashboard
    responses:
      200:
        description: System health information
    """
    try:
        db_status = 'healthy'
        db_error = None
        
        # Check database connectivity by performing actual operations
        try:
            # Test 1: Count transactions (tests basic query functionality)
            total_transactions = Transaction.query.count()
            
            # Test 2: Try to access database with SQLAlchemy text()
            from sqlalchemy import text
            db.session.execute(text('SELECT 1')).fetchone()
            
        except Exception as e:
            db_status = 'unhealthy'
            db_error = str(e)
            print(f"Database health check failed: {e}")
        
        # Check recent transaction activity
        try:
            recent_transactions = Transaction.query.filter(
                Transaction.created_at >= datetime.utcnow() - timedelta(hours=1)
            ).count()
        except Exception:
            recent_transactions = 0
        
        # Get additional metrics
        try:
            total_transactions = Transaction.query.count() if db_status == 'healthy' else 0
        except Exception:
            total_transactions = 0
        
        health_data = {
            'database': db_status,
            'recent_activity': recent_transactions,
            'total_transactions': total_transactions,
            'server_time': datetime.utcnow().isoformat(),
            'uptime': 'healthy'
        }
        
        # Include error details if database is unhealthy
        if db_status == 'unhealthy' and db_error:
            health_data['database_error'] = db_error
        
        return success_response(health_data)
        
    except Exception as e:
        print(f"System health check error: {e}")
        return error_response(f"Failed to get system health: {str(e)}", 500)

# User Management
@dashboard_bp.route('/api/users', methods=['GET'])
@api_admin_required
@rate_limit(max_requests=30, window=60)
def admin_get_users():
    """Get all users"""
    from models.user import User
    users = User.query.order_by(User.created_at.desc()).all()
    return success_response([u.to_dict() for u in users])

@dashboard_bp.route('/api/users', methods=['POST'])
@api_admin_required
@csrf_required
def admin_create_user():
    """Create a new user"""
    data = request.get_json() or {}
    from models.user import User
    if not data.get('username') or not data.get('password'):
        return error_response('Username and password are required', 400)
    user = User(
        username=data['username'], email=data.get('email'),
        full_name=data.get('full_name'), phone_number=data.get('phone_number'),
        role=data.get('role', 'customer'), user_type=data.get('role', 'customer'),
        is_active=True
    )
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()
    return success_response(user.to_dict(), 201)

@dashboard_bp.route('/api/users/<int:user_id>', methods=['PUT'])
@api_admin_required
@csrf_required
def admin_update_user(user_id):
    """Update user details"""
    data = request.get_json() or {}
    from models.user import User
    user = User.query.get(user_id)
    if not user:
        return error_response('User not found', 404)
    for field in ['email','full_name','phone_number','role','user_type']:
        if field in data:
            setattr(user, field, data[field])
    if 'password' in data:
        user.set_password(data['password'])
    db.session.commit()
    return success_response(user.to_dict())

@dashboard_bp.route('/api/users/<int:user_id>/toggle-status', methods=['POST'])
@api_admin_required
def admin_toggle_user(user_id):
    """Activate/deactivate a user"""
    from models.user import User
    user = User.query.get(user_id)
    if not user:
        return error_response('User not found', 404)
    user.is_active = not user.is_active
    db.session.commit()
    return success_response({'id': user.id, 'is_active': user.is_active})

# Get single user details
@dashboard_bp.route('/api/users/<int:user_id>', methods=['GET'])
@api_admin_required
@rate_limit(max_requests=30, window=60)
def admin_get_user(user_id):
    """Get a single user's details"""
    from models.user import User
    user = User.query.get(user_id)
    if not user:
        return error_response('User not found', 404)
    return success_response(user.to_dict())

# Loan Management
@dashboard_bp.route('/api/loans', methods=['GET'])
@api_admin_required
@rate_limit(max_requests=30, window=60)
def admin_get_loans():
    """Get all loans with summary"""
    from models.loan import Loan
    loans = Loan.query.order_by(Loan.created_at.desc()).all()
    data = [l.to_dict() for l in loans]
    summary = {
        'total_loans': len(data),
        'active_loans': len([l for l in data if l['status']=='active']),
        'completed_loans': len([l for l in data if l['status']=='completed'])
    }
    return success_response({'loans': data, 'summary': summary})

@dashboard_bp.route('/api/loans', methods=['POST'])
@api_admin_required
@csrf_required
def admin_create_loan():
    """Create a new loan"""
    data = request.get_json() or {}
    from models.loan import Loan
    from models.user import User
    # Validate
    user = User.query.get(data.get('user_id'))
    if not user:
        return error_response('Customer not found',404)
    loan = Loan(
        user_id=user.id,
        original_amount=data['original_amount'],
        interest_rate=data.get('interest_rate',15),
        term_months=data.get('term_months',12),
        disbursement_date=data.get('disbursement_date')
    )
    db.session.add(loan)
    db.session.commit()
    return success_response(loan.to_dict(),201)

@dashboard_bp.route('/api/loans/<int:loan_id>', methods=['PUT'])
@api_admin_required
@csrf_required
def admin_update_loan(loan_id):
    """Update loan details"""
    data = request.get_json() or {}
    from models.loan import Loan
    loan = Loan.query.get(loan_id)
    if not loan:
        return error_response('Loan not found',404)
    for field in ['interest_rate','term_months','status']:
        if field in data:
            setattr(loan, field, data[field])
    db.session.commit()
    return success_response(loan.to_dict())

@dashboard_bp.route('/api/loans/<int:loan_id>', methods=['GET'])
@api_admin_required
@rate_limit(max_requests=30, window=60)
def admin_get_loan(loan_id):
    """Get a single loan's details"""
    from models.loan import Loan
    loan = Loan.query.get(loan_id)
    if not loan:
        return error_response('Loan not found', 404)
    return success_response(loan.to_dict())

# Payment Management

@dashboard_bp.route('/api/payments', methods=['POST'])
@api_admin_required
@csrf_required
def admin_process_payment():
    """Process loan payment"""
    from models.transaction import Transaction
    from models.loan import Loan
    from utils.validators import PaymentValidator
    
    try:
        data = request.get_json() or {}
        
        # Validate required fields
        if not data.get('loan_id'):
            return error_response('Loan ID is required', 400)
        if not data.get('amount'):
            return error_response('Amount is required', 400)
        if not data.get('method'):
            return error_response('Payment method is required', 400)
        
        # Accept both 'phone' and 'phone_number' for compatibility
        phone_field = data.get('phone') or data.get('phone_number')
        if not phone_field:
            return error_response('Phone number is required', 400)
        

        # restructure data to match PaymentValidator expectations
        data['phoneNumber'] = phone_field
        # Validate and parse data
        try:
            loan_id = int(data.get('loan_id'))
            # validate payment request 
            paymentpayload = PaymentValidator.validate_payment_request(data)
            amount = paymentpayload.get('amount')
            phone = paymentpayload.get('phoneNumber')
            method = paymentpayload.get('method')
        except Exception as e:
            return error_response(f'Validation error: {str(e)}', 400)
        
        # Check loan exists
        loan = Loan.query.get(loan_id)
        if not loan:
            return error_response('Loan not found', 404)
        
        # Check amount doesn't exceed balance
        if amount > loan.outstanding_balance:
            return error_response('Amount exceeds outstanding balance', 400)
        
        # Create transaction
        transaction = Transaction(
            user_id=loan.user_id,
            loan_id=loan.id,
            amount=amount,
            phone_number=phone,
            method=method,
            transaction_type='loan_payment',
            status='pending'
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        # For OMari payments, create with OTP URLs
        if method == 'omari':
            transaction.remoteotpurl = f'https://mock-omari-otp.com/pay/{transaction.reference}'
            transaction.otpreference = f'OTP_{transaction.reference}'
            db.session.commit()
        
        # Process payment asynchronously if service is available
        if payment_service:
            try:
                payment_result = payment_service.process_transaction(transaction.reference)
                # If OMari and processing returns OTP data, use it
                if method == 'omari' and payment_result and payment_result.get('remoteotpurl'):
                    transaction.remoteotpurl = payment_result.get('remoteotpurl')
                    transaction.otpreference = payment_result.get('otpreference')
                    db.session.commit()
            except Exception as e:
                print(f"Payment processing failed: {e}")
        
        response_data = {
            'message': 'Payment initiated successfully',
            'transaction_id': transaction.id,
            'reference': transaction.reference,
            'amount': float(transaction.amount),
            'status': transaction.status
        }
        
        # Add OMari-specific fields if applicable
        if method == 'omari':
            response_data['remoteotpurl'] = transaction.remoteotpurl
            response_data['otpreference'] = transaction.otpreference
        
        return success_response(response_data, 201)
        
    except Exception as e:
        db.session.rollback()
        return error_response(f"Failed to process payment: {str(e)}", 500)


@dashboard_bp.route('api/payment/otp', methods=['POST'])
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

# Individual Resource Endpoints

@dashboard_bp.route('/api/users/<int:user_id>')
@api_admin_required
@rate_limit(max_requests=100, window=60)
def get_user_details(user_id):
    """Get individual user details."""
    from models.user import User
    try:
        user = User.query.get(user_id)
        if not user:
            return error_response('User not found', 404)
        
        return success_response({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'full_name': user.full_name,
            'phone_number': user.phone_number,
            'role': user.role,
            'is_active': user.is_active,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'updated_at': user.updated_at.isoformat() if user.updated_at else None
        })
    except Exception as e:
        return error_response(f"Failed to get user details: {str(e)}", 500)

@dashboard_bp.route('/api/users/<int:user_id>', methods=['PUT'])
@api_admin_required
@rate_limit(max_requests=30, window=60)
def update_user(user_id):
    """Update user details."""
    from models.user import User
    try:
        user = User.query.get(user_id)
        if not user:
            return error_response('User not found', 404)
        
        data = request.get_json() or {}
        
        # Update allowed fields
        if 'username' in data:
            # Check for duplicate username
            existing = User.query.filter(User.username == data['username'], User.id != user_id).first()
            if existing:
                return error_response('Username already exists', 400)
            user.username = data['username']
        
        if 'email' in data:
            # Check for duplicate email
            existing = User.query.filter(User.email == data['email'], User.id != user_id).first()
            if existing:
                return error_response('Email already exists', 400)
            user.email = data['email']
        
        if 'full_name' in data:
            user.full_name = data['full_name']
        
        if 'phone_number' in data:
            user.phone_number = data['phone_number']
        
        if 'role' in data and data['role'] in ['admin', 'customer']:
            user.role = data['role']
        
        if 'is_active' in data:
            user.is_active = bool(data['is_active'])
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return success_response({'message': 'User updated successfully'})
    except Exception as e:
        db.session.rollback()
        return error_response(f"Failed to update user: {str(e)}", 500)

@dashboard_bp.route('/api/loans/<int:loan_id>')
@api_admin_required
@rate_limit(max_requests=100, window=60)
def get_loan_details(loan_id):
    """Get individual loan details."""
    from models.loan import Loan
    from models.user import User
    try:
        loan = Loan.query.join(User).filter(Loan.id == loan_id).first()
        if not loan:
            return error_response('Loan not found', 404)
        
        return success_response({
            'id': loan.id,
            'loan_id': loan.loan_id,
            'user_id': loan.user_id,
            'customer_name': loan.user.full_name or loan.user.username,
            'original_amount': float(loan.original_amount),
            'outstanding_balance': float(loan.outstanding_balance),
            'interest_rate': float(loan.interest_rate),
            'term_months': loan.term_months,
            'status': loan.status,
            'disbursement_date': loan.disbursement_date.isoformat() if loan.disbursement_date else None,
            'created_at': loan.created_at.isoformat() if loan.created_at else None,
            'updated_at': loan.updated_at.isoformat() if loan.updated_at else None
        })
    except Exception as e:
        return error_response(f"Failed to get loan details: {str(e)}", 500)

@dashboard_bp.route('/api/loans/<int:loan_id>', methods=['PUT'])
@api_admin_required
@rate_limit(max_requests=30, window=60)
def update_loan(loan_id):
    """Update loan details."""
    from models.loan import Loan
    try:
        loan = Loan.query.get(loan_id)
        if not loan:
            return error_response('Loan not found', 404)
        
        data = request.get_json() or {}
        
        # Update allowed fields
        if 'original_amount' in data:
            try:
                loan.original_amount = float(data['original_amount'])
            except (ValueError, TypeError):
                return error_response('Invalid original amount', 400)
        
        if 'interest_rate' in data:
            try:
                loan.interest_rate = float(data['interest_rate'])
            except (ValueError, TypeError):
                return error_response('Invalid interest rate', 400)
        
        if 'status' in data and data['status'] in ['active', 'completed', 'defaulted']:
            loan.status = data['status']
        
        loan.updated_at = datetime.utcnow()
        db.session.commit()
        
        return success_response({'message': 'Loan updated successfully'})
    except Exception as e:
        db.session.rollback()
        return error_response(f"Failed to update loan: {str(e)}", 500)

@dashboard_bp.route('/api/transactions/<int:transaction_id>')
@api_admin_required
@rate_limit(max_requests=100, window=60)
def get_transaction_details(transaction_id):
    """Get individual transaction details."""
    from models.transaction import Transaction
    try:
        transaction = Transaction.query.get(transaction_id)
        if not transaction:
            return error_response('Transaction not found', 404)
        
        # Use to_dict method which handles all fields properly
        transaction_data = transaction.to_dict()
        return success_response(transaction_data)
    except Exception as e:
        return error_response(f"Failed to get transaction details: {str(e)}", 500)

@dashboard_bp.route('/api/test-csrf', methods=['POST'])
@api_admin_required
@csrf_required
def test_csrf():
    """Test CSRF token functionality."""
    data = request.get_json() or {}
    return success_response({
        'message': 'CSRF token validated successfully',
        'received_data': data,
        'timestamp': datetime.now().isoformat()
    })
