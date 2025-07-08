"""Enhanced dashboard routes with loan management."""
from flask import Blueprint, render_template, jsonify, request
from datetime import datetime, timedelta
from sqlalchemy import func, desc, text
from models.transaction import Transaction
from models.loan import Loan
from models.user import User, LoginAttempt
from utils.database import db
from utils.responses import success_response, error_response
from utils.security import login_required, admin_required, csrf_required, rate_limit, api_admin_required
from services.auth_service import AuthService

enhanced_dashboard_bp = Blueprint('enhanced_dashboard', __name__, url_prefix='/admin/enhanced')

@enhanced_dashboard_bp.route('/')
@login_required
@admin_required
def enhanced_dashboard_home():
    """Enhanced Admin Dashboard Home."""
    csrf_token = AuthService.generate_csrf_token()
    return render_template('dashboard/enhanced.html', csrf_token=csrf_token)

@enhanced_dashboard_bp.route('/api/overview')
@api_admin_required
@rate_limit(max_requests=30, window=60)
def get_enhanced_overview():
    """Get comprehensive dashboard overview with loan management."""
    try:
        # Get date ranges
        now = datetime.utcnow()
        today = now.date()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        
        # === USER STATISTICS ===
        total_users = User.query.count()
        total_customers = User.query.filter_by(role='customer').count()
        active_customers = User.query.filter_by(role='customer', is_active=True).count()
        new_customers_this_month = User.query.filter(
            User.role == 'customer',
            User.created_at >= month_ago
        ).count()
        
        # === LOAN STATISTICS ===
        total_loans = Loan.query.count()
        active_loans = Loan.query.filter_by(status='active').count()
        completed_loans = Loan.query.filter_by(status='completed').count()
        
        # Loan amounts
        loan_amounts = db.session.query(
            func.sum(Loan.original_amount).label('total_disbursed'),
            func.sum(Loan.outstanding_balance).label('total_outstanding')
        ).first()
        
        total_disbursed = float(loan_amounts.total_disbursed or 0)
        total_outstanding = float(loan_amounts.total_outstanding or 0)
        total_collected = total_disbursed - total_outstanding
        
        # Collection rate
        collection_rate = (total_collected / max(total_disbursed, 1)) * 100
        
        # Loans this month
        loans_this_month = db.session.query(
            func.count(Loan.id),
            func.sum(Loan.original_amount)
        ).filter(Loan.created_at >= month_ago).first()
        
        # === TRANSACTION STATISTICS ===
        total_transactions = Transaction.query.count()
        completed_transactions = Transaction.query.filter(
            Transaction.status.in_(['completed', 'paid'])
        ).count()
        pending_transactions = Transaction.query.filter_by(status='pending').count()
          # Transaction amounts - using separate queries for MySQL compatibility
        total_transaction_amount = db.session.query(
            func.sum(Transaction.amount)
        ).scalar() or 0
        
        total_completed_amount = db.session.query(
            func.sum(Transaction.amount)
        ).filter(
            Transaction.status.in_(['completed', 'paid'])
        ).scalar() or 0
        
        total_transaction_amount = float(total_transaction_amount)
        total_completed_amount = float(total_completed_amount)
        
        # Transactions today
        transactions_today = Transaction.query.filter(
            Transaction.created_at >= today
        ).count()
        
        amount_collected_today = db.session.query(
            func.sum(Transaction.amount)
        ).filter(
            Transaction.created_at >= today,
            Transaction.status.in_(['completed', 'paid'])
        ).scalar() or 0
        
        # Success rate
        success_rate = (completed_transactions / max(total_transactions, 1)) * 100
        
        # === PAYMENT METHOD BREAKDOWN ===
        payment_methods = db.session.query(
            Transaction.method,
            func.count(Transaction.id).label('count'),
            func.sum(Transaction.amount).label('total_amount')
        ).filter(
            Transaction.status.in_(['completed', 'paid'])
        ).group_by(Transaction.method).all()
        
        # === RECENT ACTIVITY ===
        recent_loans = Loan.query.order_by(Loan.created_at.desc()).limit(5).all()
        recent_transactions = Transaction.query.order_by(Transaction.created_at.desc()).limit(10).all()
        recent_logins = LoginAttempt.query.filter_by(success=True).order_by(
            LoginAttempt.created_at.desc()
        ).limit(5).all()
        
        # === PERFORMANCE METRICS ===
        avg_loan_amount = db.session.query(func.avg(Loan.original_amount)).scalar() or 0
        avg_payment_amount = db.session.query(
            func.avg(Transaction.amount)
        ).filter(Transaction.status.in_(['completed', 'paid'])).scalar() or 0
        
        overview_data = {
            'summary': {
                'total_users': total_users,
                'total_customers': total_customers,
                'active_customers': active_customers,
                'total_loans': total_loans,
                'active_loans': active_loans,
                'total_transactions': total_transactions,
                'pending_transactions': pending_transactions
            },
            
            'financial': {
                'total_disbursed': total_disbursed,
                'total_outstanding': total_outstanding,
                'total_collected': total_collected,
                'collection_rate': round(collection_rate, 2),
                'total_transaction_amount': total_transaction_amount,
                'total_completed_amount': total_completed_amount,
                'amount_collected_today': float(amount_collected_today),
                'avg_loan_amount': round(float(avg_loan_amount), 2),
                'avg_payment_amount': round(float(avg_payment_amount), 2)
            },
            
            'growth': {
                'new_customers_this_month': new_customers_this_month,
                'loans_this_month_count': loans_this_month[0] or 0,
                'loans_this_month_amount': float(loans_this_month[1] or 0),
                'transactions_today': transactions_today,
                'customer_growth_rate': round((new_customers_this_month / max(total_customers - new_customers_this_month, 1)) * 100, 2)
            },
            
            'performance': {
                'success_rate': round(success_rate, 2),
                'completed_loans': completed_loans,
                'completion_rate': round((completed_loans / max(total_loans, 1)) * 100, 2)
            },
            
            'payment_methods': [
                {
                    'method': method,
                    'count': count,
                    'total_amount': float(total_amount),
                    'percentage': round((count / max(completed_transactions, 1)) * 100, 2)
                }
                for method, count, total_amount in payment_methods
            ],
            
            'recent_activity': {
                'loans': [
                    {
                        **loan.to_dict(),
                        'customer_name': loan.customer.full_name if loan.customer else 'Unknown'
                    }
                    for loan in recent_loans
                ],
                'transactions': [tx.to_dict() for tx in recent_transactions],
                'logins': [login.to_dict() for login in recent_logins]
            },
            
            'last_updated': now.isoformat()
        }
        
        return success_response(overview_data)
        
    except Exception as e:
        return error_response(f'Failed to get enhanced overview: {str(e)}', 500)

@enhanced_dashboard_bp.route('/api/loans')
@api_admin_required
@rate_limit(max_requests=20, window=60)
def get_loans_management():
    """Get loan management data with filtering and pagination."""
    try:
        # Get query parameters
        status_filter = request.args.get('status')
        customer_filter = request.args.get('customer')
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 50, type=int), 200)
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        
        # Base query with joins for customer data
        loans_query = db.session.query(Loan).join(User, Loan.user_id == User.id)
        
        # Apply filters
        if status_filter:
            loans_query = loans_query.filter(Loan.status == status_filter)
        
        if customer_filter:
            loans_query = loans_query.filter(
                User.full_name.ilike(f'%{customer_filter}%') |
                User.username.ilike(f'%{customer_filter}%')
            )
        
        # Apply sorting
        if hasattr(Loan, sort_by):
            order_col = getattr(Loan, sort_by)
            if sort_order == 'desc':
                loans_query = loans_query.order_by(desc(order_col))
            else:
                loans_query = loans_query.order_by(order_col)
        else:
            loans_query = loans_query.order_by(desc(Loan.created_at))
        
        # Paginate
        loans_paginated = loans_query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Build response data
        loans_data = []
        for loan in loans_paginated.items:
            loan_dict = loan.to_dict()
            # Add customer information
            loan_dict['customer'] = {
                'id': loan.customer.id,
                'username': loan.customer.username,
                'full_name': loan.customer.full_name,
                'phone_number': loan.customer.phone_number,
                'email': loan.customer.email
            }
            
            # Add payment summary
            loan_transactions = Transaction.query.filter_by(loan_id=loan.id).all()
            loan_dict['payment_summary'] = {
                'total_payments': len(loan_transactions),
                'completed_payments': len([tx for tx in loan_transactions if tx.paid]),
                'last_payment_date': max([tx.created_at for tx in loan_transactions if tx.paid], default=None),
                'next_expected_payment': loan.monthly_payment
            }
            
            loans_data.append(loan_dict)
        
        # Get summary statistics
        summary_stats = {
            'total_loans': Loan.query.count(),
            'active_loans': Loan.query.filter_by(status='active').count(),
            'completed_loans': Loan.query.filter_by(status='completed').count(),
            'defaulted_loans': Loan.query.filter_by(status='defaulted').count(),
            'total_disbursed': float(db.session.query(func.sum(Loan.original_amount)).scalar() or 0),
            'total_outstanding': float(db.session.query(func.sum(Loan.outstanding_balance)).scalar() or 0)
        }
        
        return success_response({
            'loans': loans_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': loans_paginated.total,
                'pages': loans_paginated.pages,
                'has_next': loans_paginated.has_next,
                'has_prev': loans_paginated.has_prev
            },
            'summary': summary_stats,
            'filters_applied': {
                'status': status_filter,
                'customer': customer_filter,
                'sort_by': sort_by,
                'sort_order': sort_order
            }
        })
        
    except Exception as e:
        return error_response(f'Failed to get loans management data: {str(e)}', 500)

@enhanced_dashboard_bp.route('/api/customers')
@api_admin_required
@rate_limit(max_requests=20, window=60)
def get_customers_management():
    """Get customer management data with loan summaries."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 50, type=int), 200)
        search = request.args.get('search', '').strip()
        
        # Base query for customers
        customers_query = User.query.filter_by(role='customer')
        
        # Apply search filter
        if search:
            customers_query = customers_query.filter(
                User.full_name.ilike(f'%{search}%') |
                User.username.ilike(f'%{search}%') |
                User.email.ilike(f'%{search}%') |
                User.phone_number.ilike(f'%{search}%')
            )
        
        customers_query = customers_query.order_by(desc(User.created_at))
        
        # Paginate
        customers_paginated = customers_query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Build response data with loan summaries
        customers_data = []
        for customer in customers_paginated.items:
            customer_dict = customer.to_dict()
            
            # Add comprehensive loan summary
            customer_loans = Loan.query.filter_by(user_id=customer.id).all()
            customer_transactions = Transaction.query.filter_by(user_id=customer.id).all()
            
            customer_dict['loan_summary'] = {
                'total_loans': len(customer_loans),
                'active_loans': len([l for l in customer_loans if l.status == 'active']),
                'completed_loans': len([l for l in customer_loans if l.status == 'completed']),
                'total_borrowed': sum(float(l.original_amount) for l in customer_loans),
                'total_outstanding': sum(float(l.outstanding_balance) for l in customer_loans if l.status == 'active'),
                'total_paid': sum(float(l.original_amount - l.outstanding_balance) for l in customer_loans),
                'payment_history_count': len(customer_transactions),
                'last_payment_date': max([tx.created_at for tx in customer_transactions if tx.paid], default=None),
                'average_loan_amount': sum(float(l.original_amount) for l in customer_loans) / max(len(customer_loans), 1)
            }
            
            customers_data.append(customer_dict)
        
        return success_response({
            'customers': customers_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': customers_paginated.total,
                'pages': customers_paginated.pages,
                'has_next': customers_paginated.has_next,
                'has_prev': customers_paginated.has_prev
            },
            'search_applied': search
        })
        
    except Exception as e:
        return error_response(f'Failed to get customers management data: {str(e)}', 500)

@enhanced_dashboard_bp.route('/api/reports/financial')
@api_admin_required
@rate_limit(max_requests=10, window=60)
def get_financial_reports():
    """Generate comprehensive financial reports."""
    try:
        # Get date range parameters
        days = request.args.get('days', 30, type=int)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # === PERIOD SUMMARY ===
        period_loans = db.session.query(
            func.count(Loan.id),
            func.sum(Loan.original_amount)
        ).filter(Loan.created_at >= start_date).first()
        
        period_payments = db.session.query(
            func.count(Transaction.id),
            func.sum(Transaction.amount)
        ).filter(
            Transaction.created_at >= start_date,
            Transaction.status.in_(['completed', 'paid'])
        ).first()
        
        # === DAILY BREAKDOWN ===
        daily_data = []
        current_date = start_date.date()
        
        while current_date <= end_date.date():
            next_date = current_date + timedelta(days=1)
            
            # Loans disbursed
            loans_disbursed = db.session.query(
                func.count(Loan.id),
                func.sum(Loan.original_amount)
            ).filter(
                Loan.created_at >= current_date,
                Loan.created_at < next_date
            ).first()
            
            # Payments collected
            payments_collected = db.session.query(
                func.count(Transaction.id),
                func.sum(Transaction.amount)
            ).filter(
                Transaction.created_at >= current_date,
                Transaction.created_at < next_date,
                Transaction.status.in_(['completed', 'paid'])
            ).first()
            
            daily_data.append({
                'date': current_date.isoformat(),
                'loans_disbursed_count': loans_disbursed[0] or 0,
                'loans_disbursed_amount': float(loans_disbursed[1] or 0),
                'payments_collected_count': payments_collected[0] or 0,
                'payments_collected_amount': float(payments_collected[1] or 0),
                'net_cash_flow': float(payments_collected[1] or 0) - float(loans_disbursed[1] or 0)
            })
            
            current_date = next_date
        
        # === TOP PERFORMERS ===
        top_customers = db.session.query(
            User.id,
            User.username,
            User.full_name,
            func.sum(Transaction.amount).label('total_paid')
        ).join(Transaction).filter(
            Transaction.created_at >= start_date,
            Transaction.status.in_(['completed', 'paid'])
        ).group_by(User.id).order_by(text('total_paid DESC')).limit(10).all()
        
        financial_report = {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': days
            },
            'summary': {
                'loans_disbursed_count': period_loans[0] or 0,
                'loans_disbursed_amount': float(period_loans[1] or 0),
                'payments_collected_count': period_payments[0] or 0,
                'payments_collected_amount': float(period_payments[1] or 0),
                'net_cash_flow': float(period_payments[1] or 0) - float(period_loans[1] or 0),
                'collection_rate': round((float(period_payments[1] or 0) / max(float(period_loans[1] or 0), 1)) * 100, 2)
            },
            'daily_breakdown': daily_data,
            'top_customers': [
                {
                    'id': customer.id,
                    'username': customer.username,
                    'full_name': customer.full_name,
                    'total_paid': float(customer.total_paid)
                }
                for customer in top_customers
            ]
        }
        
        return success_response(financial_report)
        
    except Exception as e:
        return error_response(f'Failed to generate financial report: {str(e)}', 500)

# === COMPREHENSIVE USER MANAGEMENT ===

@enhanced_dashboard_bp.route('/api/users')
@api_admin_required
@rate_limit(max_requests=60, window=60)
def get_all_users():
    """Get all users with comprehensive details."""
    try:
        # Get query parameters for filtering and pagination
        role_filter = request.args.get('role')
        status_filter = request.args.get('status')
        search = request.args.get('search', '').strip()
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        
        # Build query
        query = User.query
        
        # Apply filters
        if role_filter:
            query = query.filter(User.role == role_filter)
        
        if status_filter == 'active':
            query = query.filter(User.is_active == True)
        elif status_filter == 'inactive':
            query = query.filter(User.is_active == False)
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                User.username.ilike(search_term) |
                User.full_name.ilike(search_term) |
                User.email.ilike(search_term) |
                User.phone_number.ilike(search_term)
            )
        
        # Order by creation date
        query = query.order_by(User.created_at.desc())
        
        # Paginate
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Prepare user data with additional statistics
        users_data = []
        for user in paginated.items:
            user_dict = user.to_dict()
            
            # Add loan statistics for customers
            if user.role == 'customer':
                user_dict['loans_count'] = user.loans.count()
                user_dict['active_loans_count'] = user.loans.filter_by(status='active').count()
                user_dict['total_borrowed'] = sum(float(loan.original_amount) for loan in user.loans)
                user_dict['total_outstanding'] = sum(float(loan.outstanding_balance) for loan in user.loans.filter_by(status='active'))
                
                # Recent transaction count
                user_dict['recent_transactions'] = user.transactions.filter(
                    Transaction.created_at >= datetime.utcnow() - timedelta(days=30)
                ).count()
            
            users_data.append(user_dict)
        
        return success_response({
            'users': users_data,
            'pagination': {
                'page': paginated.page,
                'per_page': paginated.per_page,
                'total': paginated.total,
                'pages': paginated.pages
            },
            'summary': {
                'total_users': User.query.count(),
                'total_customers': User.query.filter_by(role='customer').count(),
                'total_admins': User.query.filter_by(role='admin').count(),
                'active_users': User.query.filter_by(is_active=True).count(),
                'new_users_this_month': User.query.filter(
                    User.created_at >= datetime.utcnow() - timedelta(days=30)
                ).count()
            }
        })
        
    except Exception as e:
        return error_response(f"Failed to retrieve users: {str(e)}", 500)

@enhanced_dashboard_bp.route('/api/users', methods=['POST'])
@api_admin_required
@csrf_required
@rate_limit(max_requests=10, window=60)
def create_user():
    """Create a new user."""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['username', 'email', 'full_name', 'role', 'password']
        for field in required_fields:
            if not data.get(field):
                return error_response(f"Missing required field: {field}", 400)
        
        # Check if username or email already exists
        if User.query.filter_by(username=data['username']).first():
            return error_response("Username already exists", 400)
        
        if User.query.filter_by(email=data['email']).first():
            return error_response("Email already exists", 400)
        
        # Create new user
        user = User(
            username=data['username'],
            email=data['email'],
            full_name=data['full_name'],
            phone_number=data.get('phone_number'),
            role=data['role'],
            user_type=data['role'],  # Set same as role
            is_active=data.get('is_active', True)
        )
        
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        return success_response({
            'message': 'User created successfully',
            'user': user.to_dict()
        }, 201)
        
    except Exception as e:
        db.session.rollback()
        return error_response(f"Failed to create user: {str(e)}", 500)

@enhanced_dashboard_bp.route('/api/users/<int:user_id>', methods=['PUT'])
@api_admin_required
@csrf_required
@rate_limit(max_requests=20, window=60)
def update_user(user_id):
    """Update an existing user."""
    try:
        user = User.query.get_or_404(user_id)
        data = request.get_json()
        
        # Update allowed fields
        allowed_fields = ['full_name', 'email', 'phone_number', 'is_active']
        for field in allowed_fields:
            if field in data:
                setattr(user, field, data[field])
        
        # Handle password update separately
        if data.get('password'):
            user.set_password(data['password'])
        
        db.session.commit()
        
        return success_response({
            'message': 'User updated successfully',
            'user': user.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return error_response(f"Failed to update user: {str(e)}", 500)

@enhanced_dashboard_bp.route('/api/users/<int:user_id>/toggle-status', methods=['POST'])
@api_admin_required
@csrf_required
@rate_limit(max_requests=20, window=60)
def toggle_user_status(user_id):
    """Toggle user active status."""
    try:
        user = User.query.get_or_404(user_id)
        
        # Prevent deactivating admin users
        if user.role == 'admin':
            return error_response("Cannot deactivate admin users", 400)
        
        user.is_active = not user.is_active
        db.session.commit()
        
        return success_response({
            'message': f"User {'activated' if user.is_active else 'deactivated'} successfully",
            'user': user.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return error_response(f"Failed to toggle user status: {str(e)}", 500)

@enhanced_dashboard_bp.route('/api/users/<int:user_id>')
@api_admin_required
@rate_limit(max_requests=60, window=60)
def get_user_details(user_id):
    """Get detailed information about a specific user."""
    try:
        user = User.query.get_or_404(user_id)
        user_data = user.to_dict()
        
        # Add detailed statistics
        if user.role == 'customer':
            # Loan statistics
            loans = user.loans.all()
            user_data['loan_details'] = {
                'total_loans': len(loans),
                'active_loans': len([l for l in loans if l.status == 'active']),
                'completed_loans': len([l for l in loans if l.status == 'completed']),
                'total_borrowed': sum(float(l.original_amount) for l in loans),
                'total_outstanding': sum(float(l.outstanding_balance) for l in loans if l.status == 'active'),
                'total_paid': sum(float(l.paid_amount) for l in loans),
                'loans': [loan.to_dict() for loan in loans[-5:]]  # Recent 5 loans
            }
            
            # Transaction statistics
            transactions = user.transactions.all()
            user_data['transaction_details'] = {
                'total_transactions': len(transactions),
                'successful_transactions': len([t for t in transactions if t.status == 'completed']),
                'total_transaction_amount': sum(float(t.amount) for t in transactions),
                'recent_transactions': [tx.to_dict() for tx in transactions[-10:]]  # Recent 10 transactions
            }
        
        # Login history
        login_attempts = LoginAttempt.query.filter_by(username=user.username).order_by(
            LoginAttempt.created_at.desc()
        ).limit(10).all()
        
        user_data['login_history'] = [attempt.to_dict() for attempt in login_attempts]
        
        return success_response(user_data)
        
    except Exception as e:
        return error_response(f"Failed to retrieve user details: {str(e)}", 500)

# === COMPREHENSIVE LOAN MANAGEMENT ===

@enhanced_dashboard_bp.route('/api/loans')
@api_admin_required
@rate_limit(max_requests=60, window=60)
def get_all_loans():
    """Get all loans with comprehensive details."""
    try:
        # Get query parameters
        status_filter = request.args.get('status')
        customer_id = request.args.get('customer_id')
        amount_range = request.args.get('amount_range')
        search = request.args.get('search', '').strip()
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        
        # Build query
        query = Loan.query.join(User).add_columns(User.full_name.label('customer_name'))
        
        # Apply filters
        if status_filter:
            query = query.filter(Loan.status == status_filter)
        
        if customer_id:
            query = query.filter(Loan.user_id == customer_id)
        
        if amount_range:
            if amount_range == '0-500':
                query = query.filter(Loan.original_amount <= 500)
            elif amount_range == '500-1000':
                query = query.filter(Loan.original_amount.between(500, 1000))
            elif amount_range == '1000-5000':
                query = query.filter(Loan.original_amount.between(1000, 5000))
            elif amount_range == '5000+':
                query = query.filter(Loan.original_amount > 5000)
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                Loan.loan_id.ilike(search_term) |
                User.full_name.ilike(search_term) |
                User.username.ilike(search_term)
            )
        
        # Order by creation date
        query = query.order_by(Loan.created_at.desc())
        
        # Paginate
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Prepare loan data
        loans_data = []
        for loan, customer_name in paginated.items:
            loan_dict = loan.to_dict()
            loan_dict['customer_name'] = customer_name
            
            # Add transaction count
            loan_dict['transaction_count'] = loan.transactions.count()
            loan_dict['last_payment'] = None
            
            last_transaction = loan.transactions.filter_by(status='completed').order_by(
                Transaction.completed_at.desc()
            ).first()
            
            if last_transaction:
                loan_dict['last_payment'] = {
                    'amount': float(last_transaction.amount),
                    'date': last_transaction.completed_at.isoformat(),
                    'method': last_transaction.method
                }
            
            loans_data.append(loan_dict)
        
        # Calculate summary statistics
        summary = Loan.get_summary_stats()
        
        return success_response({
            'loans': loans_data,
            'pagination': {
                'page': paginated.page,
                'per_page': paginated.per_page,
                'total': paginated.total,
                'pages': paginated.pages
            },
            'summary': summary
        })
        
    except Exception as e:
        return error_response(f"Failed to retrieve loans: {str(e)}", 500)

@enhanced_dashboard_bp.route('/api/loans', methods=['POST'])
@api_admin_required
@csrf_required
@rate_limit(max_requests=10, window=60)
def create_loan():
    """Create a new loan."""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['user_id', 'original_amount', 'interest_rate', 'term_months']
        for field in required_fields:
            if not data.get(field):
                return error_response(f"Missing required field: {field}", 400)
        
        # Validate customer exists and is active
        customer = User.query.filter_by(id=data['user_id'], role='customer').first()
        if not customer:
            return error_response("Invalid customer ID", 400)
        
        if not customer.is_active:
            return error_response("Cannot create loan for inactive customer", 400)
        
        # Create new loan
        loan = Loan(
            user_id=data['user_id'],
            original_amount=Decimal(str(data['original_amount'])),
            interest_rate=Decimal(str(data['interest_rate'])),
            term_months=int(data['term_months']),
            disbursement_date=datetime.strptime(data['disbursement_date'], '%Y-%m-%d').date() if data.get('disbursement_date') else None,
            status='active'
        )
        
        db.session.add(loan)
        db.session.commit()
        
        return success_response({
            'message': 'Loan created successfully',
            'loan': loan.to_dict()
        }, 201)
        
    except Exception as e:
        db.session.rollback()
        return error_response(f"Failed to create loan: {str(e)}", 500)

@enhanced_dashboard_bp.route('/api/loans/<int:loan_id>')
@api_admin_required
@rate_limit(max_requests=60, window=60)
def get_loan_details(loan_id):
    """Get detailed information about a specific loan."""
    try:
        loan = Loan.query.get_or_404(loan_id)
        loan_data = loan.to_dict()
        
        # Add customer information
        customer = User.query.get(loan.user_id)
        loan_data['customer'] = customer.to_dict() if customer else None
        
        # Add transaction history
        transactions = loan.transactions.order_by(Transaction.created_at.desc()).all()
        loan_data['transactions'] = [tx.to_dict() for tx in transactions]
        
        # Add payment schedule calculation
        if loan.term_months and loan.original_amount:
            monthly_payment = float(loan.original_amount) / loan.term_months
            payment_schedule = []
            
            for month in range(1, loan.term_months + 1):
                payment_schedule.append({
                    'month': month,
                    'expected_payment': monthly_payment,
                    'expected_date': (loan.disbursement_date + timedelta(days=30*month)) if loan.disbursement_date else None
                })
            
            loan_data['payment_schedule'] = payment_schedule
        
        return success_response(loan_data)
        
    except Exception as e:
        return error_response(f"Failed to retrieve loan details: {str(e)}", 500)

# === COMPREHENSIVE TRANSACTION MANAGEMENT ===

@enhanced_dashboard_bp.route('/api/transactions')
@api_admin_required
@rate_limit(max_requests=60, window=60)
def get_all_transactions():
    """Get all transactions with comprehensive details."""
    try:
        # Get query parameters
        status_filter = request.args.get('status')
        method_filter = request.args.get('method')
        period_filter = request.args.get('period')
        loan_id = request.args.get('loan_id')
        customer_id = request.args.get('customer_id')
        search = request.args.get('search', '').strip()
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        
        # Build query with joins
        query = Transaction.query.outerjoin(Loan).outerjoin(User)
        
        # Apply filters
        if status_filter:
            query = query.filter(Transaction.status == status_filter)
        
        if method_filter:
            query = query.filter(Transaction.method == method_filter)
        
        if loan_id:
            query = query.filter(Transaction.loan_id == loan_id)
        
        if customer_id:
            query = query.filter(Transaction.user_id == customer_id)
        
        if period_filter:
            now = datetime.utcnow()
            if period_filter == 'today':
                query = query.filter(func.date(Transaction.created_at) == now.date())
            elif period_filter == 'week':
                week_start = now - timedelta(days=7)
                query = query.filter(Transaction.created_at >= week_start)
            elif period_filter == 'month':
                month_start = now - timedelta(days=30)
                query = query.filter(Transaction.created_at >= month_start)
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                Transaction.reference.ilike(search_term) |
                Transaction.phone_number.ilike(search_term) |
                User.full_name.ilike(search_term) |
                Loan.loan_id.ilike(search_term)
            )
        
        # Order by creation date
        query = query.order_by(Transaction.created_at.desc())
        
        # Paginate
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Prepare transaction data
        transactions_data = []
        for transaction in paginated.items:
            tx_dict = transaction.to_dict()
            transactions_data.append(tx_dict)
        
        # Calculate summary statistics
        summary = Transaction.get_summary_stats()
        
        return success_response({
            'transactions': transactions_data,
            'pagination': {
                'page': paginated.page,
                'per_page': paginated.per_page,
                'total': paginated.total,
                'pages': paginated.pages
            },
            'summary': summary
        })
        
    except Exception as e:
        return error_response(f"Failed to retrieve transactions: {str(e)}", 500)

# === SECURITY & MONITORING ===

@enhanced_dashboard_bp.route('/api/security/overview')
@api_admin_required
@rate_limit(max_requests=30, window=60)
def get_security_overview():
    """Get security overview and monitoring data."""
    try:
        now = datetime.utcnow()
        
        # Recent login attempts (last 24 hours)
        recent_attempts = LoginAttempt.query.filter(
            LoginAttempt.created_at >= now - timedelta(hours=24)
        ).order_by(LoginAttempt.created_at.desc()).limit(50).all()
        
        # Failed login attempts (last 24 hours)
        failed_attempts = LoginAttempt.query.filter(
            LoginAttempt.created_at >= now - timedelta(hours=24),
            LoginAttempt.success == False
        ).count()
        
        # Successful logins (last 24 hours)
        successful_logins = LoginAttempt.query.filter(
            LoginAttempt.created_at >= now - timedelta(hours=24),
            LoginAttempt.success == True
        ).count()
        
        # Locked accounts
        locked_accounts = User.query.filter(
            User.locked_until > now
        ).count()
        
        # System health metrics
        health_metrics = {
            'database_connected': True,  # If we got here, DB is connected
            'total_users': User.query.count(),
            'active_sessions': successful_logins,  # Approximation
            'failed_login_rate': (failed_attempts / max(failed_attempts + successful_logins, 1)) * 100,
            'locked_accounts': locked_accounts
        }
        
        return success_response({
            'login_attempts': [attempt.to_dict() for attempt in recent_attempts],
            'security_stats': {
                'failed_attempts_24h': failed_attempts,
                'successful_logins_24h': successful_logins,
                'locked_accounts': locked_accounts,
                'failed_login_rate': health_metrics['failed_login_rate']
            },
            'system_health': health_metrics
        })
        
    except Exception as e:
        return error_response(f"Failed to retrieve security overview: {str(e)}", 500)

# === ANALYTICS & REPORTING ===

@enhanced_dashboard_bp.route('/api/analytics/comprehensive')
@api_admin_required
@rate_limit(max_requests=20, window=60)
def get_comprehensive_analytics():
    """Get comprehensive analytics data for charts and reports."""
    try:
        now = datetime.utcnow()
        
        # Loan performance trends (last 12 months)
        months = []
        loan_trends = []
        for i in range(12):
            month_start = now - timedelta(days=30*(i+1))
            month_end = now - timedelta(days=30*i)
            
            loans_created = Loan.query.filter(
                Loan.created_at.between(month_start, month_end)
            ).count()
            
            loans_completed = Loan.query.filter(
                Loan.completed_at.between(month_start, month_end)
            ).count()
            
            months.append(month_start.strftime('%b %Y'))
            loan_trends.append({
                'month': month_start.strftime('%b %Y'),
                'loans_created': loans_created,
                'loans_completed': loans_completed
            })
        
        # Payment method distribution
        method_stats = db.session.query(
            Transaction.method,
            func.count(Transaction.id).label('count'),
            func.sum(Transaction.amount).label('total_amount')
        ).group_by(Transaction.method).all()
        
        payment_methods = {
            'labels': [stat[0] for stat in method_stats],
            'data': [int(stat[1]) for stat in method_stats],
            'amounts': [float(stat[2] or 0) for stat in method_stats]
        }
        
        # Collection rate by month
        collection_rates = []
        for i in range(6):
            month_start = now - timedelta(days=30*(i+1))
            month_end = now - timedelta(days=30*i)
            
            month_disbursed = db.session.query(func.sum(Loan.original_amount)).filter(
                Loan.created_at.between(month_start, month_end)
            ).scalar() or 0
            
            month_collected = db.session.query(func.sum(Transaction.amount)).filter(
                Transaction.created_at.between(month_start, month_end),
                Transaction.status == 'completed'
            ).scalar() or 0
            
            collection_rate = (float(month_collected) / float(month_disbursed) * 100) if month_disbursed > 0 else 0
            
            collection_rates.append({
                'month': month_start.strftime('%b %Y'),
                'collection_rate': round(collection_rate, 2),
                'disbursed': float(month_disbursed),
                'collected': float(month_collected)
            })
        
        # Customer growth
        customer_growth = []
        for i in range(12):
            month_start = now - timedelta(days=30*(i+1))
            month_end = now - timedelta(days=30*i)
            
            new_customers = User.query.filter(
                User.role == 'customer',
                User.created_at.between(month_start, month_end)
            ).count()
            
            customer_growth.append({
                'month': month_start.strftime('%b %Y'),
                'new_customers': new_customers
            })
        
        return success_response({
            'loan_trends': list(reversed(loan_trends)),
            'payment_methods': payment_methods,
            'collection_rates': list(reversed(collection_rates)),
            'customer_growth': list(reversed(customer_growth)),
            'summary_metrics': {
                'avg_loan_amount': float(db.session.query(func.avg(Loan.original_amount)).scalar() or 0),
                'avg_collection_time': 0,  # Calculate based on loan completion times
                'customer_retention_rate': 0,  # Calculate based on repeat customers
                'default_rate': 0  # Calculate based on defaulted loans
            }
        })
        
    except Exception as e:
        return error_response(f"Failed to retrieve analytics data: {str(e)}", 500)
