"""Debug script to test transaction saving."""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models.transaction import Transaction
from utils.database import db
import uuid

def test_transaction_saving():
    """Test if transactions can be saved to database."""
    app = create_app()
    
    with app.app_context():
        try:
            print("🔍 Testing transaction saving...")
              # Check database connection
            print("1. Testing database connection...")
            from sqlalchemy import text
            result = db.session.execute(text('SELECT 1')).fetchone()
            print(f"   ✅ Database connected: {result}")
              # Check if transaction table exists
            print("2. Checking transaction table...")
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"   📋 Available tables: {tables}")
            
            if 'transactions' not in tables:
                print("   ❌ Transaction table does not exist!")
                print("   Creating tables...")
                db.create_all()
                
            # Test basic transaction creation
            print("3. Testing transaction creation...")
            test_ref = f"DEBUG_{uuid.uuid4().hex[:8].upper()}"
            
            transaction = Transaction(
                reference=test_ref,
                phone_number="0771234567",
                amount=10.00,
                method="test",
                status="pending"
            )
            
            print(f"   📄 Created transaction object: {test_ref}")
            
            # Add to session
            db.session.add(transaction)
            print("   ➕ Added to session")
            
            # Commit
            db.session.commit()
            print("   💾 Committed to database")
            
            # Verify it was saved
            saved = Transaction.query.filter_by(reference=test_ref).first()
            if saved:
                print(f"   ✅ Transaction found in database: {saved.reference}")
                print(f"      ID: {saved.id}")
                print(f"      Amount: ${saved.amount}")
                print(f"      Created: {saved.created_at}")
                
                # Clean up
                db.session.delete(saved)
                db.session.commit()
                print("   🧹 Test transaction cleaned up")
            else:
                print("   ❌ Transaction NOT found in database after commit!")
            
            # Count all transactions
            total = Transaction.query.count()
            print(f"4. Total transactions in database: {total}")
            
            # Test payment service transaction creation
            print("5. Testing PaymentService transaction creation...")
            from services.payment_service import PaymentService
            from services.paynow_service import PaynowService
            
            # Create minimal paynow service for testing
            paynow_service = PaynowService("test_id", "test_key", "http://test.com", "http://test.com")
            payment_service = PaymentService(paynow_service)
            
            # Test create_test_payment (should work without Paynow)
            result = payment_service.create_test_payment("0771234567", 15.00, "ecocash")
            print(f"   📤 Test payment result: {result.get('status')}")
            print(f"   📝 Reference: {result.get('reference')}")
            
            if result.get('status') == 'success':
                test_ref_2 = result.get('reference')
                saved_2 = Transaction.query.filter_by(reference=test_ref_2).first()
                if saved_2:
                    print(f"   ✅ PaymentService transaction saved: {saved_2.reference}")
                    # Clean up
                    db.session.delete(saved_2)
                    db.session.commit()
                else:
                    print(f"   ❌ PaymentService transaction NOT saved: {test_ref_2}")
            
            print("\n🎯 Diagnosis complete!")
            
        except Exception as e:
            print(f"❌ Error during testing: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()

if __name__ == '__main__':
    test_transaction_saving()
