"""User model for admin authentication and customer management."""
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime
from utils.database import db

class User(UserMixin, db.Model):
    """User model for admin authentication and customer management."""
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Enhanced user details
    full_name = db.Column(db.String(100), nullable=True)
    phone_number = db.Column(db.String(15), nullable=True, index=True)
    
    # User type and status
    role = db.Column(db.String(20), default='admin', nullable=False)  # admin, customer
    user_type = db.Column(db.String(20), default='admin', nullable=False)  # alias for role
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Security fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime)
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime)
    
    # Relationships
    loans = db.relationship('Loan', backref='customer', lazy='dynamic')
    transactions = db.relationship('Transaction', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        """Set password hash."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash."""
        return check_password_hash(self.password_hash, password)
    
    @property
    def active_loans(self):
        """Get active loans with outstanding balance."""
        if self.role != 'customer':
            return []
        return [loan for loan in self.loans if loan.status == 'active' and loan.outstanding_balance > 0]
    
    @property
    def total_outstanding(self):
        """Get total outstanding amount."""
        return sum(float(loan.outstanding_balance) for loan in self.active_loans)    
    def is_locked(self):
        """Check if account is locked."""
        if self.locked_until and self.locked_until > datetime.utcnow():
            return True
        return False
    
    def lock_account(self, minutes=30):
        """Lock account for specified minutes."""
        from datetime import timedelta
        self.locked_until = datetime.utcnow() + timedelta(minutes=minutes)
        db.session.commit()
    
    def increment_failed_attempts(self):
        """Increment failed login attempts."""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            self.lock_account()
        db.session.commit()
    
    def reset_failed_attempts(self):
        """Reset failed login attempts."""
        self.failed_login_attempts = 0
        self.locked_until = None
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'phone_number': self.phone_number,
            'role': self.role,
            'user_type': self.role,  # alias for compatibility
            'is_active': self.is_active,
            'active_loans_count': len(self.active_loans) if self.role == 'customer' else None,
            'total_outstanding': self.total_outstanding if self.role == 'customer' else None,
            'created_at': self.created_at.isoformat(),
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

class LoginAttempt(db.Model):
    """Track login attempts for security monitoring."""
    
    __tablename__ = 'login_attempts'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, index=True)
    ip_address = db.Column(db.String(45), nullable=False, index=True)
    user_agent = db.Column(db.Text)
    success = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'username': self.username,
            'ip_address': self.ip_address,
            'success': self.success,
            'created_at': self.created_at.isoformat()
        }
