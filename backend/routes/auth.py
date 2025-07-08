# Update the auth.py file - remove the duplicate route and fix the setup logic

"""Authentication routes."""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user, login_required
from models.user import User, LoginAttempt
from services.auth_service import AuthService
from utils.security import csrf_required, rate_limit, api_login_required
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
@api_login_required
def get_current_user():
    """Get current user info."""
    return success_response(current_user.to_dict())

@auth_bp.route('/setup', methods=['GET', 'POST'])
def setup():
    """Initial admin setup - works whether users exist or not."""
    
    if request.method == 'GET':
        # Show setup form regardless of existing users
        csrf_token = AuthService.generate_csrf_token()
        
        # Check if any admin exists
        admin_exists = User.query.filter_by(role='admin').first() is not None
        total_users = User.query.count()
        
        return render_template('auth/setup.html', 
                             csrf_token=csrf_token, 
                             admin_exists=admin_exists,
                             total_users=total_users)
    
    try:
        # Get form data
        data = request.get_json() if request.is_json else request.form
        
        # Validate CSRF token
        csrf_token = data.get('csrf_token')
        if not AuthService.validate_csrf_token(csrf_token):
            return jsonify({'error': 'Invalid CSRF token'}), 403
        
        # Validate required fields
        required_fields = ['username', 'email', 'password', 'full_name']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            return jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400
        
        # Check if username already exists
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': f'Username "{data["username"]}" already exists'}), 400
        
        # Check if email already exists
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': f'Email "{data["email"]}" already exists'}), 400
        
        # Validate password length
        if len(data['password']) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        
        # Create admin user
        admin = User(
            username=data['username'],
            email=data['email'],
            full_name=data['full_name'],
            phone_number=data.get('phone_number', ''),
            role='admin',
            user_type='admin',
            is_active=True
        )
        
        admin.set_password(data['password'])
        
        db.session.add(admin)
        db.session.commit()
        
        print(f"✅ Admin user created: {admin.username} (ID: {admin.id})")
        
        if request.is_json:
            return jsonify({
                'success': True,
                'message': 'Admin user created successfully',
                'admin_id': admin.id,
                'username': admin.username
            }), 201
        else:
            flash('Admin user created successfully! You can now login.', 'success')
            return redirect(url_for('auth.login'))
            
    except Exception as e:
        db.session.rollback()
        print(f"❌ Failed to create admin: {e}")
        
        error_msg = f'Error creating admin: {str(e)}'
        
        if request.is_json:
            return jsonify({'error': error_msg}), 500
        else:
            flash(error_msg, 'error')
            csrf_token = AuthService.generate_csrf_token()
            return render_template('auth/setup.html', csrf_token=csrf_token, error=error_msg)

@auth_bp.route('/check-setup')
def check_setup():
    """Check setup status."""
    admin_count = User.query.filter_by(role='admin').count()
    total_users = User.query.count()
    
    return jsonify({
        'admin_exists': admin_count > 0,
        'admin_count': admin_count,
        'total_users': total_users,
        'setup_needed': admin_count == 0
    })