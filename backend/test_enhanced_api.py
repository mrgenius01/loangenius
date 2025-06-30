#!/usr/bin/env python3
"""
Test the enhanced overview API for MySQL compatibility
"""

import sys
import os

# Add current directory to path
sys.path.append('.')

def test_enhanced_overview():
    """Test the enhanced overview API."""
    print("🧪 Testing Enhanced Overview API")
    print("="*40)
    
    try:
        from app import create_app
        app = create_app()
        
        with app.app_context():
            from utils.database import db
            from models.user import User
            from models.loan import Loan
            from models.transaction import Transaction
            from datetime import datetime, timedelta
            from sqlalchemy import func
            
            print("📊 Testing database queries...")
            
            # Test basic counts
            print("  Testing basic counts...")
            total_users = User.query.count()
            total_loans = Loan.query.count()
            total_transactions = Transaction.query.count()
            print(f"  ✓ Users: {total_users}, Loans: {total_loans}, Transactions: {total_transactions}")
            
            # Test the problematic transaction amount queries
            print("  Testing transaction amount queries...")
            total_transaction_amount = db.session.query(
                func.sum(Transaction.amount)
            ).scalar() or 0
            print(f"  ✓ Total transaction amount: {total_transaction_amount}")
            
            total_completed_amount = db.session.query(
                func.sum(Transaction.amount)
            ).filter(
                Transaction.status.in_(['completed', 'paid'])
            ).scalar() or 0
            print(f"  ✓ Total completed amount: {total_completed_amount}")
            
            # Test loan amounts
            print("  Testing loan amount queries...")
            loan_amounts = db.session.query(
                func.sum(Loan.original_amount).label('total_disbursed'),
                func.sum(Loan.outstanding_balance).label('total_outstanding')
            ).first()
            print(f"  ✓ Loan amounts query successful")
            
            # Test payment methods breakdown
            print("  Testing payment methods breakdown...")
            payment_methods = db.session.query(
                Transaction.method,
                func.count(Transaction.id).label('count'),
                func.sum(Transaction.amount).label('total_amount')
            ).filter(
                Transaction.status.in_(['completed', 'paid'])
            ).group_by(Transaction.method).all()
            print(f"  ✓ Payment methods: {len(payment_methods)} methods found")
            
            print("\n✅ All queries executed successfully!")
            return True
            
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_enhanced_overview()
    if success:
        print("\n🎉 Enhanced overview API is working!")
    else:
        print("\n💥 Enhanced overview API has issues.")
    sys.exit(0 if success else 1)
