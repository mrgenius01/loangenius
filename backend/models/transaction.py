"""Transaction model for storing payment transactions with loan relationships."""
from datetime import datetime
import json
import random
import string
from utils.database import db

class Transaction(db.Model):
    """Database model for storing payment transactions."""
    __tablename__ = 'transactions'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign keys for loan relationships
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    loan_id = db.Column(db.Integer, db.ForeignKey('loans.id'), nullable=True, index=True)
      # Basic transaction info
    reference = db.Column(db.String(100), unique=True, nullable=False, index=True)
    phone_number = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Numeric(precision=10, scale=2), nullable=False)
    method = db.Column(db.String(20), nullable=False)
    
    # Transaction type
    transaction_type = db.Column(db.String(20), default='loan_payment', nullable=False)
    
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
    
    # Additional details
    description = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    paid_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Additional data fields (JSON)
    paynow_result = db.Column(db.Text)  # JSON string for Paynow callback data
    otp_response = db.Column(db.Text)   # JSON string for OTP response data
    is_test = db.Column(db.Boolean, default=False)
    
    def __init__(self, **kwargs):
        """Initialize transaction with auto-generated reference if not provided."""
        super().__init__(**kwargs)
        if not self.reference:
            self.reference = self.generate_reference()
    
    def generate_reference(self):
        """Generate randomized transaction reference: {random}sl00a.{timestamp}.{loan_id}"""
        # Add randomness: 3 random letters + sl00a + timestamp + loan_id
        random_prefix = ''.join(random.choices(string.ascii_lowercase, k=3))
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        
        if self.loan_id:
            # Import here to avoid circular imports
            from models.loan import Loan
            loan = db.session.get(Loan, self.loan_id)
            loan_ref = loan.loan_id if loan else f"L{self.loan_id:03d}"
        else:
            loan_ref = "GEN"
        
        return f"{random_prefix}sl00a.{timestamp}.{loan_ref}"
    def to_dict(self):
        """Convert transaction to dictionary."""
        return {
            'id': self.id,
            'reference': self.reference,
            'user_id': self.user_id,
            'loan_id': self.loan_id,
            'loan_reference': self.loan.loan_id if hasattr(self, 'loan') and self.loan else None,
            'customer_name': self.user.full_name if hasattr(self, 'user') and self.user else 'Unknown',
            'phone_number': self.phone_number,
            'amount': self.amount,
            'method': self.method,
            'transaction_type': self.transaction_type,
            'poll_url': self.poll_url,
            'status': self.status,
            'instructions': self.instructions,
            'paynow_reference': self.paynow_reference,
            'hash': self.hash,
            'redirect_url': self.redirect_url,
            'has_redirect': self.has_redirect,
            'remoteotpurl': self.remoteotpurl,
            'otpreference': self.otpreference,
            'description': self.description,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'paid_at': self.paid_at.isoformat() if self.paid_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'paynow_result': json.loads(self.paynow_result) if self.paynow_result else None,
            'otp_response': json.loads(self.otp_response) if self.otp_response else None,
            'is_test': self.is_test,
            'paid': self.paid
        }
    
    @property
    def paid(self):
        """Check if transaction is paid."""
        return self.paid_at is not None or self.status.lower() == 'paid'
    
    def mark_as_completed(self):
        """Mark transaction as completed and update loan."""
        self.status = 'completed'
        self.paid_at = datetime.utcnow()
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        # Update loan balance if this is a loan payment
        if hasattr(self, 'loan') and self.loan and self.transaction_type == 'loan_payment':
            self.loan.process_payment(self.amount)
        
        # Save changes
        db.session.commit()
    
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
    
    @classmethod
    def get_summary_stats(cls):
        """Get transaction summary statistics for admin dashboard."""
        from sqlalchemy import func
        
        # Overall stats
        stats = db.session.query(
            func.count(cls.id).label('total_transactions'),
            func.sum(cls.amount).label('total_amount'),
            func.sum(cls.amount).filter(cls.status == 'completed').label('total_completed_amount')
        ).first()
        
        # Status breakdown
        pending_count = cls.query.filter_by(status='pending').count()
        completed_count = cls.query.filter_by(status='completed').count()
        failed_count = cls.query.filter(cls.status.in_(['failed', 'cancelled'])).count()
        
        # Recent transactions (last 24 hours)
        from datetime import timedelta
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_count = cls.query.filter(cls.created_at >= yesterday).count()
        
        return {
            'total_transactions': stats.total_transactions or 0,
            'total_amount': float(stats.total_amount or 0),
            'total_completed_amount': float(stats.total_completed_amount or 0),
            'pending_transactions': pending_count,
            'completed_transactions': completed_count,
            'failed_transactions': failed_count,
            'recent_transactions': recent_count,
            'success_rate': round((completed_count / max(stats.total_transactions, 1)) * 100, 2)
        }
