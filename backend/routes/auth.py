"""Authentication routes."""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user, login_required
from models.user import User, LoginAttempt
from services.auth_service import AuthService
from utils.security import csrf_required, rate_limit
from utils.responses import success_response, error_response
from utils.database import db

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
@rate_limit(max_requests=10, window=300)  # 10 attempts per 5 minutes
def login():
    """Admin login page and handler."""
    if current_user.is_authenticated:
        return redirect('/admin/')
    
    if request.method == 'GET':
        csrf_token = AuthService.generate_csrf_token()
        return render_template('auth/login.html', csrf_token=csrf_token)
    
    # Handle login attempt
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    csrf_token = request.form.get('csrf_token')
    
    # Validate CSRF token
    if not AuthService.validate_csrf_token(csrf_token):
        return jsonify({'error': 'Invalid CSRF token'}), 403
    
    # Validate input
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400    
    # Authenticate
    result = AuthService.authenticate_user(
        username=username,
        password=password,
        ip_address=AuthService.get_client_ip(),
        user_agent=request.headers.get('User-Agent')
    )
    
    if result['success']:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return success_response(result)
        else:
            return redirect('/admin/')
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return error_response(result['message'], 401)
        else:
            flash(result['message'], 'error')
            return redirect('/auth/login')

@auth_bp.route('/logout', methods=['POST'])
@login_required
@csrf_required
def logout():
    """Logout handler."""
    logout_user()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return success_response({'message': 'Logged out successfully'})
    else:
        return redirect('/auth/login')

@auth_bp.route('/api/csrf-token')
def get_csrf_token():
    """Get CSRF token."""
    token = AuthService.generate_csrf_token()
    return success_response({'csrf_token': token})

@auth_bp.route('/api/user')
@login_required
def get_current_user():
    """Get current user info."""
    return success_response(current_user.to_dict())

@auth_bp.route('/setup', methods=['GET', 'POST'])
def setup():
    """Initial admin setup (only if no users exist)."""
    if User.query.count() > 0:
        return redirect('/auth/login')
    
    if request.method == 'GET':
        csrf_token = AuthService.generate_csrf_token()
        return render_template('auth/setup.html', csrf_token=csrf_token)
    
    # Create initial admin user
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')
    csrf_token = request.form.get('csrf_token')
    
    # Validate CSRF token
    if not AuthService.validate_csrf_token(csrf_token):
        return jsonify({'error': 'Invalid CSRF token'}), 403
    
    # Validate input
    errors = []
    if not username or len(username) < 3:
        errors.append('Username must be at least 3 characters')
    if not email or '@' not in email:
        errors.append('Valid email is required')
    if not password or len(password) < 8:
        errors.append('Password must be at least 8 characters')
    if password != confirm_password:
        errors.append('Passwords do not match')
    
    if errors:
        return jsonify({'error': '; '.join(errors)}), 400
      # Create admin user
    result = AuthService.create_admin_user(username, email, password)
    
    if result['success']:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return success_response({'message': 'Admin user created successfully'})
        else:
            flash('Admin user created successfully. Please login.', 'success')
            return redirect('/auth/login')
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return error_response(result['message'], 400)
        else:
            flash(result['message'], 'error')
            csrf_token = AuthService.generate_csrf_token()
            return render_template('auth/setup.html', csrf_token=csrf_token, error=result['message'])
