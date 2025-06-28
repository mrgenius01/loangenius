"""Test script to verify the new loan models work correctly."""
from app import create_app
from utils.database import db
from models.user import User
from models.loan import Loan
from models.transaction import Transaction
from datetime import datetime, date
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_models():
    """Test the loan models and relationships."""
    app = create_app()
    
    with app.app_context():
        try:
            logger.info("🧪 Testing loan models...")
            
            # Test database connection
            db.engine.execute('SELECT 1').fetchone()
            logger.info("✅ Database connection successful")
            
            # Create tables
            db.create_all()
            logger.info("✅ Tables created successfully")
            
            # Test creating a customer
            logger.info("📝 Creating test customer...")
            customer = User(
                username="test_customer",
                phone_number="0771234567",
                full_name="Test Customer",
                email="test@example.com",
                user_type="customer"
            )
            customer.set_password("password123")
            
            db.session.add(customer)
            db.session.commit()
            logger.info(f"✅ Customer created: {customer.full_name}")
            
            # Test creating a loan
            logger.info("💰 Creating test loan...")
            loan = Loan(
                user_id=customer.id,
                original_amount=1000.00,
                interest_rate=15.0,
                term_months=12,
                disbursement_date=date.today()
            )
            
            db.session.add(loan)
            db.session.commit()
            logger.info(f"✅ Loan created: {loan.loan_id} for ${loan.original_amount}")
            
            # Test creating a transaction
            logger.info("💳 Creating test transaction...")
            transaction = Transaction(
                user_id=customer.id,
                loan_id=loan.id,
                phone_number=customer.phone_number,
                amount=100.00,
                method="ecocash",
                transaction_type="loan_payment"
            )
            
            db.session.add(transaction)
            db.session.commit()
            logger.info(f"✅ Transaction created: {transaction.reference}")
            
            # Test marking transaction as completed
            logger.info("✅ Marking transaction as completed...")
            transaction.mark_as_completed()
            logger.info(f"✅ Transaction completed. Loan balance: ${loan.outstanding_balance}")
            
            # Test getting summary stats
            logger.info("📊 Testing summary statistics...")
            user_stats = User.get_summary_stats()
            loan_stats = Loan.get_summary_stats()
            transaction_stats = Transaction.get_summary_stats()
            
            logger.info(f"📈 Users: {user_stats}")
            logger.info(f"📈 Loans: {loan_stats}")
            logger.info(f"📈 Transactions: {transaction_stats}")
            
            # Test relationships
            logger.info("🔗 Testing relationships...")
            logger.info(f"Customer's loans: {[loan.loan_id for loan in customer.loans]}")
            logger.info(f"Customer's active loans: {[loan.loan_id for loan in customer.active_loans]}")
            logger.info(f"Loan's transactions: {[t.reference for t in loan.transactions]}")
            
            logger.info("🎉 All tests passed!")
            
        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    test_models()