"""Transaction model for storing payment transactions."""
from datetime import datetime
import json
from utils.database import db

class Transaction(db.Model):
    """Database model for storing payment transactions."""
    __tablename__ = 'transactions'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Basic transaction info
    reference = db.Column(db.String(50), unique=True, nullable=False, index=True)
    phone_number = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    method = db.Column(db.String(20), nullable=False)
    
    # Paynow data
    poll_url = db.Column(db.Text)
    status = db.Column(db.String(50), default='pending')
    instructions = db.Column(db.Text)
    paynow_reference = db.Column(db.String(100))
    hash = db.Column(db.String(256))
    redirect_url = db.Column(db.Text)
    has_redirect = db.Column(db.Boolean, default=False)
    
    # OMari-specific fields
    remoteotpurl = db.Column(db.Text)
    otpreference = db.Column(db.String(100))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    paid_at = db.Column(db.DateTime)
    
    # Additional data fields (JSON)
    paynow_result = db.Column(db.Text)  # JSON string for Paynow callback data
    otp_response = db.Column(db.Text)   # JSON string for OTP response data
    is_test = db.Column(db.Boolean, default=False)
    
    def to_dict(self):
        """Convert transaction to dictionary."""
        return {
            'id': self.id,
            'reference': self.reference,
            'phone_number': self.phone_number,
            'amount': self.amount,
            'method': self.method,
            'poll_url': self.poll_url,
            'status': self.status,
            'instructions': self.instructions,
            'paynow_reference': self.paynow_reference,
            'hash': self.hash,
            'redirect_url': self.redirect_url,
            'has_redirect': self.has_redirect,
            'remoteotpurl': self.remoteotpurl,
            'otpreference': self.otpreference,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'paid_at': self.paid_at.isoformat() if self.paid_at else None,
            'paynow_result': json.loads(self.paynow_result) if self.paynow_result else None,
            'otp_response': json.loads(self.otp_response) if self.otp_response else None,
            'is_test': self.is_test,
            'paid': self.paid
        }
    
    @property
    def paid(self):
        """Check if transaction is paid."""
        return self.paid_at is not None or self.status.lower() == 'paid'
    
    def update_status(self, status, **kwargs):
        """Update transaction status and optional fields."""
        self.status = status
        self.updated_at = datetime.utcnow()
        
        # Update additional fields if provided
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def mark_as_paid(self):
        """Mark transaction as paid."""
        self.status = 'paid'
        self.paid_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def set_paynow_result(self, result_data):
        """Set Paynow result data."""
        self.paynow_result = json.dumps(result_data)
        self.updated_at = datetime.utcnow()
    
    def set_otp_response(self, response_data):
        """Set OTP response data."""
        self.otp_response = json.dumps(response_data)
        self.updated_at = datetime.utcnow()
    
    def __repr__(self):
        return f'<Transaction {self.reference}: {self.method} ${self.amount}>'
