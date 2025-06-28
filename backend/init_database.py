#!/usr/bin/env python3
"""
Database Initialization Script
Creates a fresh database with the correct schema and sample data.
"""

import sys
import os
from datetime import datetime, date
from decimal import Decimal

# Add current directory to path  
sys.path.append('.')

def initialize_database():
    """Initialize a fresh database with correct schema."""
    print("🚀 Database Initialization Script")
    print("="*50)
    
    try:
        from app import create_app
        app = create_app()
        
        with app.app_context():
            from utils.database import db
            from models.user import User
            from models.loan import Loan
            from models.transaction import Transaction
            
            print("📊 Initializing database with correct schema...")
            
            # Create all tables
            db.create_all()
            print("  ✓ All tables created with db.Numeric decimal fields")
            
            # Check if we need to create an admin user
            admin_count = User.query.filter_by(role='admin').count()
            if admin_count == 0:
                print("  🔧 Creating default admin user...")
                admin = User(
                    username='admin',
                    email='admin@example.com', 
                    full_name='System Administrator',
                    role='admin',
                    user_type='admin',
                    is_active=True
                )
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
                print("  ✓ Admin user created: admin/admin123")
            
            # Create sample customer data if none exists
            customer_count = User.query.filter_by(role='customer').count()
            if customer_count == 0:
                print("  📋 Creating sample customer data...")
                
                # Create sample customers
                customers = [
                    User(
                        username='john_doe',
                        email='john@example.com',
                        full_name='John Doe',
                        phone_number='0771234567',
                        role='customer',
                        user_type='customer',
                        is_active=True
                    ),
                    User(
                        username='jane_smith', 
                        email='jane@example.com',
                        full_name='Jane Smith',
                        phone_number='0779876543',
                        role='customer',
                        user_type='customer',
                        is_active=True
                    ),
                    User(
                        username='mike_wilson',
                        email='mike@example.com',
                        full_name='Mike Wilson',
                        phone_number='0775555555',
                        role='customer',
                        user_type='customer',
                        is_active=True
                    )
                ]
                
                for customer in customers:
                    customer.set_password('password123')
                    db.session.add(customer)
                
                db.session.commit()
                print("  ✓ Sample customers created")
                
                # Create sample loans
                john = User.query.filter_by(username='john_doe').first()
                jane = User.query.filter_by(username='jane_smith').first() 
                mike = User.query.filter_by(username='mike_wilson').first()
                
                loans = [
                    Loan(
                        user_id=john.id,
                        original_amount=Decimal('1000.00'),
                        outstanding_balance=Decimal('750.00'),
                        interest_rate=Decimal('15.0'),
                        term_months=12,
                        status='active',
                        disbursement_date=date(2024, 1, 15)
                    ),
                    Loan(
                        user_id=jane.id,
                        original_amount=Decimal('500.00'), 
                        outstanding_balance=Decimal('100.00'),
                        interest_rate=Decimal('12.0'),
                        term_months=6,
                        status='active',
                        disbursement_date=date(2024, 3, 1)
                    ),
                    Loan(
                        user_id=mike.id,
                        original_amount=Decimal('2000.00'),
                        outstanding_balance=Decimal('1500.00'),
                        interest_rate=Decimal('18.0'),
                        term_months=24,
                        status='active',
                        disbursement_date=date(2024, 2, 1)
                    ),
                    Loan(
                        user_id=john.id,
                        original_amount=Decimal('300.00'),
                        outstanding_balance=Decimal('0.00'),
                        interest_rate=Decimal('10.0'),
                        term_months=3,
                        status='completed',
                        disbursement_date=date(2023, 10, 1),
                        completed_at=datetime(2024, 1, 5)
                    )
                ]
                
                for loan in loans:
                    db.session.add(loan)
                
                db.session.commit()
                print("  ✓ Sample loans created")
                
                # Create some sample transactions
                active_loans = Loan.query.filter_by(status='active').all()
                
                for i, loan in enumerate(active_loans[:2]):  # Just first 2 loans
                    transaction = Transaction(
                        user_id=loan.user_id,
                        loan_id=loan.id,
                        phone_number=loan.customer.phone_number,
                        amount=Decimal('50.00'),
                        method='ecocash',
                        transaction_type='loan_payment',
                        status='completed',
                        description=f'Payment for loan {loan.loan_id}',
                        paid_at=datetime.now(),
                        completed_at=datetime.now()
                    )
                    db.session.add(transaction)
                
                db.session.commit()
                print("  ✓ Sample transactions created")
            
            # Print summary
            print("\n📊 Database Status:")
            print(f"  👤 Users: {User.query.count()}")
            print(f"  🏦 Loans: {Loan.query.count()}")
            print(f"  💰 Transactions: {Transaction.query.count()}")
            
            print("\n✅ Database initialization completed!")
            print("="*50)
            print("🎯 Your database is ready with:")
            print("  ✓ Correct db.Numeric decimal field types")
            print("  ✓ All necessary tables and relationships")
            print("  ✓ Sample data for testing")
            print("\n🔑 Login Credentials:")
            print("  Admin: admin / admin123")
            print("  Customer: john_doe / password123")
            print("  Customer: jane_smith / password123")
            print("  Customer: mike_wilson / password123")
            print("\n🚀 Start the application with: python app.py")
            
    except Exception as e:
        print(f"\n❌ Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def main():
    """Main function."""
    print("This will initialize/reset your database with the correct schema.")
    response = input("Continue? (y/N): ")
    
    if response.lower() != 'y':
        print("❌ Initialization cancelled")
        return False
    
    success = initialize_database()
    
    if success:
        print("\n🎉 Database ready! You can now run your loan management system.")
    else:
        print("\n❌ Please check the errors above and try again.")
    
    return success

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
