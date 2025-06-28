"""Loan model for customer loan management."""
from utils.database import db
from datetime import datetime
from decimal import Decimal

class Loan(db.Model):
    """Loan model for tracking customer loans."""
    __tablename__ = 'loans'
    
    id = db.Column(db.Integer, primary_key=True)
    loan_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    
    # Foreign key
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
      # Core loan details
    original_amount = db.Column(db.Numeric(10, 2), nullable=False)    # Total loan amount
    outstanding_balance = db.Column(db.Numeric(10, 2), nullable=False)  # Amount still owed
    
    # Additional loan details
    interest_rate = db.Column(db.Numeric(5, 2), default=15.0)  # Annual interest rate %
    term_months = db.Column(db.Integer, default=12)            # Loan term in months
    
    # Status and dates
    status = db.Column(db.String(20), default='active', nullable=False)  # active, completed, defaulted
    disbursement_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    transactions = db.relationship('Transaction', backref='loan', lazy='dynamic')
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.loan_id:
            self.loan_id = self.generate_loan_id()
        # Set outstanding balance to original amount initially
        if self.original_amount and not self.outstanding_balance:
            self.outstanding_balance = self.original_amount
    
    @staticmethod
    def generate_loan_id():
        """Generate unique loan ID (L001, L002, etc.)."""
        last_loan = Loan.query.order_by(Loan.id.desc()).first()
        if last_loan and last_loan.loan_id.startswith('L'):
            try:
                last_number = int(last_loan.loan_id[1:])
                new_number = last_number + 1
            except ValueError:
                new_number = 1
        else:
            new_number = 1
        return f"L{new_number:03d}"
    
    def process_payment(self, amount):
        """Process a payment and update balance."""
        payment_amount = Decimal(str(amount))
        self.outstanding_balance -= payment_amount
        
        # Mark as completed if fully paid
        if self.outstanding_balance <= 0:
            self.outstanding_balance = Decimal('0.00')
            self.status = 'completed'
            self.completed_at = datetime.utcnow()
        
        self.updated_at = datetime.utcnow()
    
    @property
    def progress_percentage(self):
        """Calculate payment progress."""
        if self.original_amount > 0:
            paid = self.original_amount - self.outstanding_balance
            return min(100, (float(paid) / float(self.original_amount)) * 100)
        return 0
    
    @property
    def paid_amount(self):
        """Calculate total amount paid."""
        return self.original_amount - self.outstanding_balance
    
    @property
    def monthly_payment(self):
        """Calculate expected monthly payment."""
        if self.term_months and self.original_amount:
            return self.original_amount / self.term_months
        return self.original_amount
    
    def to_dict(self):
        return {
            'id': self.id,
            'loan_id': self.loan_id,
            'user_id': self.user_id,
            'customer_name': self.customer.full_name if hasattr(self, 'customer') and self.customer else 'Unknown',
            'original_amount': float(self.original_amount),
            'outstanding_balance': float(self.outstanding_balance),
            'paid_amount': float(self.paid_amount),
            'progress_percentage': round(self.progress_percentage, 1),
            'interest_rate': float(self.interest_rate),
            'term_months': self.term_months,
            'monthly_payment': float(self.monthly_payment),
            'status': self.status,
            'is_active': self.status == 'active' and self.outstanding_balance > 0,
            'disbursement_date': self.disbursement_date.isoformat() if self.disbursement_date else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
    
    @classmethod
    def get_summary_stats(cls):
        """Get loan summary statistics for admin dashboard."""
        from sqlalchemy import func
        
        stats = db.session.query(
            func.count(cls.id).label('total_loans'),
            func.sum(cls.original_amount).label('total_disbursed'),
            func.sum(cls.outstanding_balance).label('total_outstanding'),
            func.sum(cls.original_amount - cls.outstanding_balance).label('total_collected')
        ).first()
        
        active_loans = cls.query.filter_by(status='active').count()
        completed_loans = cls.query.filter_by(status='completed').count()
        
        return {
            'total_loans': stats.total_loans or 0,
            'active_loans': active_loans,
            'completed_loans': completed_loans,
            'total_disbursed': float(stats.total_disbursed or 0),
            'total_outstanding': float(stats.total_outstanding or 0),
            'total_collected': float(stats.total_collected or 0),
            'collection_rate': round(float(stats.total_collected or 0) / float(stats.total_disbursed or 1) * 100, 2)
        }
