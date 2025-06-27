"""Authentication service for admin panel."""
from flask import request, session
from flask_login import login_user, logout_user, current_user
from datetime import datetime, timedelta
from models.user import User, LoginAttempt
from utils.database import db
import secrets
import hashlib

class AuthService:
    """Service for handling authentication."""
    
    @staticmethod
    def authenticate_user(username, password, ip_address=None, user_agent=None):
        """
        Authenticate user with rate limiting and attempt tracking.
        
        Args:
            username: Username to authenticate
            password: Password to check
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            dict: Authentication result
        """
        # Check for too many recent failed attempts from this IP
        recent_attempts = LoginAttempt.query.filter(
            LoginAttempt.ip_address == ip_address,
            LoginAttempt.success == False,
            LoginAttempt.created_at >= datetime.utcnow() - timedelta(minutes=15)
        ).count()
        
        if recent_attempts >= 10:
            return {
                'success': False,
                'message': 'Too many failed attempts. Please try again later.',
                'locked': True
            }
        
        # Find user
        user = User.query.filter_by(username=username).first()
        
        # Log attempt
        attempt = LoginAttempt(
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            success=False
        )
        
        if not user or not user.is_active:
            db.session.add(attempt)
            db.session.commit()
            return {
                'success': False,
                'message': 'Invalid credentials.',
                'user_exists': False
            }
        
        # Check if account is locked
        if user.is_locked():
            db.session.add(attempt)
            db.session.commit()
            return {
                'success': False,
                'message': 'Account is temporarily locked. Please try again later.',
                'locked': True
            }
        
        # Check password
        if not user.check_password(password):
            user.increment_failed_attempts()
            db.session.add(attempt)
            db.session.commit()
            return {
                'success': False,
                'message': 'Invalid credentials.',
                'attempts_remaining': max(0, 5 - user.failed_login_attempts)
            }
        
        # Successful login
        user.reset_failed_attempts()
        attempt.success = True
        db.session.add(attempt)
        db.session.commit()
        
        # Login user
        login_user(user, remember=True)
        
        return {
            'success': True,
            'message': 'Login successful.',
            'user': user.to_dict()
        }
    
    @staticmethod
    def create_admin_user(username, email, password):
        """Create admin user."""
        if User.query.filter_by(username=username).first():
            return {'success': False, 'message': 'Username already exists'}
        
        if User.query.filter_by(email=email).first():
            return {'success': False, 'message': 'Email already exists'}
        
        user = User(username=username, email=email, role='admin')
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        return {'success': True, 'message': 'Admin user created successfully'}
    
    @staticmethod
    def generate_csrf_token():
        """Generate CSRF token."""
        if 'csrf_token' not in session:
            session['csrf_token'] = secrets.token_hex(16)
        return session['csrf_token']
    
    @staticmethod
    def validate_csrf_token(token):
        """Validate CSRF token."""
        return token and session.get('csrf_token') == token
    
    @staticmethod
    def get_client_ip():
        """Get client IP address."""
        if request.headers.get('X-Forwarded-For'):
            return request.headers.get('X-Forwarded-For').split(',')[0].strip()
        elif request.headers.get('X-Real-IP'):
            return request.headers.get('X-Real-IP')
        else:
            return request.remote_addr
