"""Dashboard routes for admin interface."""
from flask import Blueprint, render_template, jsonify, request
from datetime import datetime, timedelta
from sqlalchemy import func, desc
from models.transaction import Transaction
from utils.database import db
from utils.responses import success_response, error_response
from utils.security import login_required, admin_required, csrf_required, rate_limit, api_admin_required
from services.auth_service import AuthService
from flasgger import swag_from

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
    """
    from models.loan import Loan
    from models.user import User, LoginAttempt
    from models.transaction import Transaction
    from utils.database import db
    from sqlalchemy import func
    from datetime import datetime, timedelta

    try:
        # Date ranges
        now = datetime.utcnow()
        today = now.date()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        # Transaction stats
        total_transactions = Transaction.query.count()
        total_amount = float(db.session.query(func.sum(Transaction.amount)).scalar() or 0)
        successful_payments = Transaction.query.filter_by(status='paid').count()
        pending_payments = Transaction.query.filter(Transaction.status.in_(['pending','sent'])).count()
        failed_payments = Transaction.query.filter_by(status='cancelled').count()
        today_transactions = Transaction.query.filter(func.date(Transaction.created_at) == today).count()
        today_amount = float(db.session.query(func.sum(Transaction.amount)).filter(func.date(Transaction.created_at) == today).scalar() or 0)

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
    Get transactions for dashboard
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
        description: Paginated transactions
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 100)
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
                Transaction.paynow_reference.contains(search)
            )
        
        # Order by latest first
        query = query.order_by(desc(Transaction.created_at))
        
        # Paginate
        pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return success_response({
            'transactions': [
                {
                    'id': t.id,
                    'reference': t.reference,
                    'phone_number': t.phone_number,
                    'amount': float(t.amount),
                    'method': t.method,
                    'status': t.status,
                    'paynow_reference': t.paynow_reference,
                    'poll_url': t.poll_url,
                    'created_at': t.created_at.isoformat(),
                    'updated_at': t.updated_at.isoformat() if t.updated_at else None,
                    'paid': t.paid
                } for t in pagination.items
            ],
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
@csrf_required
def admin_toggle_user(user_id):
    """Activate/deactivate a user"""
    from models.user import User
    user = User.query.get(user_id)
    if not user:
        return error_response('User not found', 404)
    user.is_active = not user.is_active
    db.session.commit()
    return success_response({'id': user.id, 'is_active': user.is_active})

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

# Transaction Management
@dashboard_bp.route('/api/transactions', methods=['GET'])
@api_admin_required
@rate_limit(max_requests=60, window=60)
def admin_get_transactions():
    """Get paginated transactions with loan info"""
    from models.transaction import Transaction
    from models.loan import Loan
    from sqlalchemy import desc
    page = request.args.get('page',1,type=int)
    per_page = min(request.args.get('per_page',20,type=int),100)
    qry = Transaction.query.order_by(desc(Transaction.created_at))
    pagination = qry.paginate(page=page, per_page=per_page, error_out=False)
    items = []
    for t in pagination.items:
        td = t.to_dict()
        if t.loan:
            td['loan'] = t.loan.to_dict()
        items.append(td)
    return success_response({'transactions':items,'pagination':{
        'page':page,'per_page':per_page,'total':pagination.total,'pages':pagination.pages
    }})

@dashboard_bp.route('/api/payments', methods=['POST'])
@api_admin_required
@csrf_required
def admin_process_payment():
    """Process loan payment"""
    from models.transaction import Transaction
    from models.loan import Loan
    from utils.validators import PaymentValidator
    errors = []
    data = request.get_json() or {}
    try:
        loan_id = int(data.get('loan_id'))
        amount = PaymentValidator.validate_amount(data.get('amount'))
        phone = PaymentValidator.validate_phone_number(data.get('phone_number'))
        method = PaymentValidator.validate_method(data.get('method'))
    except Exception as e:
        return error_response(str(e),400)
    loan = Loan.query.get(loan_id)
    if not loan:
        return error_response('Loan not found',404)
    if amount>loan.outstanding_balance:
        return error_response('Amount exceeds balance',400)
    tx = Transaction(
        user_id=loan.user_id, loan_id=loan.id,
        amount=amount, phone_number=phone, method=method,
        transaction_type='loan_payment'
    )
    db.session.add(tx)
    db.session.commit()
    # Trigger payment_service asynchronously if set
    if payment_service:
        payment_service.process_transaction(tx.reference)
    return success_response(tx.to_dict(),201)
