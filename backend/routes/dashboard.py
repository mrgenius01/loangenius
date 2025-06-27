"""Dashboard routes for admin interface."""
from flask import Blueprint, render_template, jsonify, request
from datetime import datetime, timedelta
from sqlalchemy import func, desc
from models.transaction import Transaction
from utils.database import db
from utils.responses import success_response, error_response
from utils.security import login_required, admin_required, csrf_required, rate_limit
from services.auth_service import AuthService
from flasgger import swag_from

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/admin')

@dashboard_bp.route('/')
@login_required
@admin_required
def dashboard_home():
    """Admin Dashboard Home."""
    csrf_token = AuthService.generate_csrf_token()
    return render_template('dashboard/index.html', csrf_token=csrf_token)

@dashboard_bp.route('/api/stats')
@login_required
@admin_required
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

@dashboard_bp.route('/api/transactions')
@login_required
@admin_required
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
@login_required
@admin_required
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
