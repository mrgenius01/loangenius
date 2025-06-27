"""Security utilities and decorators."""
from functools import wraps
from flask import request, jsonify, session, abort
from flask_login import current_user
from services.auth_service import AuthService
import time
import hashlib

def login_required(f):
    """Require user to be logged in."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            else:
                abort(401)
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Require user to be admin."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            else:
                abort(401)
        
        if current_user.role != 'admin':
            if request.is_json:
                return jsonify({'error': 'Admin access required'}), 403
            else:
                abort(403)
        
        return f(*args, **kwargs)
    return decorated_function

def csrf_required(f):
    """Require valid CSRF token."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
            token = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token')
            if not AuthService.validate_csrf_token(token):
                if request.is_json:
                    return jsonify({'error': 'Invalid CSRF token'}), 403
                else:
                    abort(403)
        return f(*args, **kwargs)
    return decorated_function

def rate_limit(max_requests=60, window=60):
    """Rate limiting decorator."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Create unique key for this client and endpoint
            client_ip = AuthService.get_client_ip()
            endpoint = request.endpoint
            key = hashlib.md5(f"{client_ip}:{endpoint}".encode()).hexdigest()
            
            # Check rate limit (you might want to use Redis for production)
            current_time = int(time.time())
            window_start = current_time - window
            
            # For now, we'll store in session (in production, use Redis)
            if 'rate_limits' not in session:
                session['rate_limits'] = {}
            
            if key not in session['rate_limits']:
                session['rate_limits'][key] = []
            
            # Clean old entries
            session['rate_limits'][key] = [
                req_time for req_time in session['rate_limits'][key] 
                if req_time > window_start
            ]
            
            # Check if limit exceeded
            if len(session['rate_limits'][key]) >= max_requests:
                if request.is_json:
                    return jsonify({'error': 'Rate limit exceeded'}), 429
                else:
                    abort(429)
            
            # Add current request
            session['rate_limits'][key].append(current_time)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
