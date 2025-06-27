"""Test script to debug payment flow and transaction saving."""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models.transaction import Transaction
from utils.database import db
from services.paynow_service import PaynowService
from services.payment_service import PaymentService

def test_payment_flow():
    """Test the complete payment flow to identify where transactions aren't saving."""
    app = create_app()
    
    with app.app_context():
        try:
            print("🧪 Testing Payment Flow...")
            
            # Count existing transactions before test
            initial_count = Transaction.query.count()
            print(f"📊 Initial transaction count: {initial_count}")
            
            # Create services
            paynow_service = PaynowService(
                app.config['PAYNOW_INTEGRATION_ID'],
                app.config['PAYNOW_INTEGRATION_KEY'],
                app.config['RETURN_URL'],
                app.config['RESULT_URL']
            )
            payment_service = PaymentService(paynow_service)
            
            print(f"🔧 PaynowService created with ID: {paynow_service.integration_id}")
            print(f"🔐 Credentials configured: {paynow_service.integration_id != 'YOUR_INTEGRATION_ID'}")
            
            # Test 1: Test payment (should work)
            print("\n1️⃣ Testing create_test_payment...")
            test_result = payment_service.create_test_payment("0771234567", 10.00, "ecocash")
            print(f"   Result status: {test_result.get('status')}")
            print(f"   Reference: {test_result.get('reference')}")
            
            if test_result.get('status') == 'success':
                test_ref = test_result.get('reference')
                test_transaction = Transaction.query.filter_by(reference=test_ref).first()
                if test_transaction:
                    print(f"   ✅ Test transaction saved to database: {test_transaction.id}")
                else:
                    print(f"   ❌ Test transaction NOT found in database")
            
            # Test 2: Real payment (might fail due to credentials but let's see what happens)
            print("\n2️⃣ Testing create_payment with real Paynow...")
            real_result = payment_service.create_payment("0771234567", 15.00, "ecocash")
            print(f"   Result status: {real_result.get('status')}")
            print(f"   Message: {real_result.get('message')}")
            print(f"   Reference: {real_result.get('reference')}")
            
            if real_result.get('reference'):
                real_ref = real_result.get('reference')
                real_transaction = Transaction.query.filter_by(reference=real_ref).first()
                if real_transaction:
                    print(f"   ✅ Real transaction saved to database: {real_transaction.id}")
                    print(f"      Status: {real_transaction.status}")
                    print(f"      Amount: ${real_transaction.amount}")
                else:
                    print(f"   ❌ Real transaction NOT found in database")
            
            # Test 3: Check if Paynow response is successful
            print("\n3️⃣ Testing direct Paynow response...")
            try:
                test_payment = paynow_service.paynow.create_payment("TEST_DIRECT", "test@example.com")
                test_payment.add("Test Item", 5.00)
                paynow_response = paynow_service.paynow.send_mobile(test_payment, "0771234567", "ecocash")
                
                print(f"   Paynow success: {paynow_response.success}")
                print(f"   Paynow status: {getattr(paynow_response, 'status', 'No status')}")
                print(f"   Paynow errors: {getattr(paynow_response, 'errors', 'No errors')}")
                
                if hasattr(paynow_response, 'data') and paynow_response.data:
                    print(f"   Paynow data keys: {list(paynow_response.data.keys())}")
                
            except Exception as paynow_error:
                print(f"   ❌ Direct Paynow test failed: {paynow_error}")
            
            # Final count
            final_count = Transaction.query.count()
            print(f"\n📊 Final transaction count: {final_count}")
            print(f"📈 Transactions created during test: {final_count - initial_count}")
            
            # List all transactions
            if final_count > 0:
                print("\n📋 Current transactions in database:")
                transactions = Transaction.query.order_by(Transaction.created_at.desc()).limit(5).all()
                for t in transactions:
                    print(f"   - {t.reference}: ${t.amount} ({t.method}) - {t.status}")
            
        except Exception as e:
            print(f"❌ Error during payment flow test: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    test_payment_flow()
