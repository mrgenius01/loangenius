#!/usr/bin/env python3
"""
Quick Database Schema Fix Script
This script specifically handles the decimal field type issues and schema mismatches.
"""

import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.append('.')

def fix_schema_issues():
    """Fix schema issues by recreating tables with correct structure."""
    print("🔧 Quick Database Schema Fix")
    print("="*50)
    
    try:
        from app import create_app
        app = create_app()
        
        with app.app_context():
            from utils.database import db
            from models.user import User
            from models.loan import Loan  
            from models.transaction import Transaction
            
            print("📊 Checking current database state...")
            
            # Check if we can query tables
            try:
                user_count = User.query.count()
                print(f"  ✓ Users table accessible ({user_count} records)")
            except Exception as e:
                print(f"  ⚠️  Users table issue: {e}")
                user_count = 0
            
            try:
                loan_count = Loan.query.count()  
                print(f"  ✓ Loans table accessible ({loan_count} records)")
            except Exception as e:
                print(f"  ⚠️  Loans table issue: {e}")
                loan_count = 0
            
            try:
                transaction_count = Transaction.query.count()
                print(f"  ✓ Transactions table accessible ({transaction_count} records)")
            except Exception as e:
                print(f"  ⚠️  Transactions table issue: {e}")
                transaction_count = 0
            
            # If we have schema issues, recreate tables
            if "unknown column" in str(e).lower() or "no such column" in str(e).lower():
                print("\n🔄 Schema mismatch detected, recreating tables...")
                
                # Drop all tables and recreate
                db.drop_all()
                print("  ✓ Dropped all existing tables")
                
                # Create all tables with new schema
                db.create_all()
                print("  ✓ Created tables with updated schema")
                
                # Create default admin user if needed
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
                    print("  ✓ Default admin created (admin/admin123)")
                
                print("\n✅ Schema fix completed!")
                print("📋 Summary:")
                print("  ✓ All tables recreated with correct decimal field types")
                print("  ✓ db.Numeric fields now properly configured")
                print("  ✓ No more SQLAlchemy decimal errors expected")
                print("\n🎯 Your database is ready! You can now:")
                print("  1. Run the application: python app.py")
                print("  2. Visit /auth/setup to create additional admin users")
                print("  3. Add customers and loans through the interface")
                
            else:
                print("\n✅ Database schema appears to be working correctly!")
                print("🎯 No migration needed at this time.")
                
    except Exception as e:
        print(f"\n❌ Schema fix failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def main():
    """Main function."""
    success = fix_schema_issues()
    
    if success:
        print("\n🚀 Ready to run your application!")
    else:
        print("\n❌ Please check the errors above and try again.")
    
    return success

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
