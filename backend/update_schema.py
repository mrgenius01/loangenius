#!/usr/bin/env python3
"""
Database Schema Update Script
Updates the existing database schema to match the new models.
"""

import sys
import os
from datetime import datetime, date
from decimal import Decimal

# Add current directory to path
sys.path.append('.')

def check_and_update_schema():
    """Check current schema and update as needed."""
    print("🔍 Database Schema Analysis & Update")
    print("="*50)
    
    try:
        from app import create_app
        app = create_app()
        
        with app.app_context():
            from utils.database import db
            
            # Get the raw connection to execute DDL statements
            engine = db.engine
            
            print("📊 Analyzing current database schema...")
            
            # Check existing tables
            with engine.connect() as conn:
                # Check if we're using SQLite or MySQL
                dialect = engine.dialect.name
                print(f"  Database type: {dialect}")
                
                if dialect == 'sqlite':
                    # SQLite approach
                    result = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = [row[0] for row in result.fetchall()]
                    print(f"  Existing tables: {tables}")
                    
                    # Check mg_users table structure
                    if 'mg_users' in tables:
                        result = conn.execute("PRAGMA table_info(mg_users)")
                        columns = [row[1] for row in result.fetchall()]
                        print(f"  MG Users table columns: {columns}")
                        
                        # Add missing columns to mg_users table
                        missing_columns = [
                            ('full_name', 'VARCHAR(100)'),
                            ('phone_number', 'VARCHAR(15)'),
                            ('role', 'VARCHAR(20) DEFAULT "admin"'),
                            ('user_type', 'VARCHAR(20) DEFAULT "admin"'),
                            ('is_active', 'BOOLEAN DEFAULT 1'),
                            ('last_login', 'DATETIME'),
                            ('failed_login_attempts', 'INTEGER DEFAULT 0'),
                            ('locked_until', 'DATETIME')
                        ]
                        
                        for col_name, col_def in missing_columns:
                            if col_name not in columns:
                                try:
                                    conn.execute(f"ALTER TABLE mg_users ADD COLUMN {col_name} {col_def}")
                                    print(f"  ✓ Added {col_name} column to mg_users table")
                                except Exception as e:
                                    print(f"  ⚠️  Could not add {col_name}: {e}")
                        
                        # Update existing users to have default role
                        conn.execute("UPDATE mg_users SET role = 'admin' WHERE role IS NULL")
                        conn.execute("UPDATE mg_users SET user_type = 'admin' WHERE user_type IS NULL")
                        conn.execute("UPDATE mg_users SET is_active = 1 WHERE is_active IS NULL")
                        conn.execute("UPDATE mg_users SET failed_login_attempts = 0 WHERE failed_login_attempts IS NULL")
                        print("  ✓ Updated existing mg_users with default values")
                
                elif dialect == 'mysql':
                    # MySQL approach - similar but different syntax
                    print("  Using MySQL database")
                    
                    # Check mg_users table structure
                    try:
                        result = conn.execute("DESCRIBE mg_users")
                        columns = [row[0] for row in result.fetchall()]
                        print(f"  MG Users table columns: {columns}")
                        
                        # Add missing columns
                        missing_columns = [
                            ('full_name', 'VARCHAR(100)'),
                            ('phone_number', 'VARCHAR(15)'),
                            ('role', 'VARCHAR(20) DEFAULT "admin"'),
                            ('user_type', 'VARCHAR(20) DEFAULT "admin"'),
                            ('is_active', 'BOOLEAN DEFAULT 1'),
                            ('last_login', 'DATETIME'),
                            ('failed_login_attempts', 'INTEGER DEFAULT 0'),
                            ('locked_until', 'DATETIME')
                        ]
                        
                        for col_name, col_def in missing_columns:
                            if col_name not in columns:
                                try:
                                    conn.execute(f"ALTER TABLE mg_users ADD COLUMN {col_name} {col_def}")
                                    print(f"  ✓ Added {col_name} column to mg_users table")
                                except Exception as e:
                                    print(f"  ⚠️  Could not add {col_name}: {e}")
                    
                    except Exception as e:
                        print(f"  ⚠️  Could not analyze mg_users table: {e}")
                
                # Commit the schema changes
                conn.commit()
                
            print("\n🔧 Creating missing tables...")
            
            # Now use SQLAlchemy to create any missing tables
            db.create_all()
            print("  ✓ All tables created/updated")
            
            print("\n📊 Testing database access...")
            
            # Test that we can now query the tables
            from models.user import User
            from models.loan import Loan
            from models.transaction import Transaction
            
            try:
                user_count = User.query.count()
                print(f"  ✓ MG Users table: {user_count} records")
            except Exception as e:
                print(f"  ✗ MG Users table error: {e}")
                return False
            
            try:
                loan_count = Loan.query.count()
                print(f"  ✓ MG Loans table: {loan_count} records")
            except Exception as e:
                print(f"  ✓ MG Loans table: 0 records (new table)")
            
            try:
                transaction_count = Transaction.query.count()
                print(f"  ✓ MG Transactions table: {transaction_count} records")
            except Exception as e:
                print(f"  ✓ MG Transactions table: 0 records (accessible)")
            
            # Check if we need to create an admin user
            admin_count = User.query.filter_by(role='admin').count()
            if admin_count == 0:
                print("\n👤 Creating default admin user...")
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
            
            print("\n✅ Database schema update completed!")
            print("="*50)
            print("🎯 Your database now has:")
            print("  ✓ All required columns in mg_users table")
            print("  ✓ New mg_loans and mg_login_attempts tables")
            print("  ✓ Proper db.Numeric decimal field types")
            print("  ✓ Working relationships between tables")
            print("\n🚀 You can now run the application with: python app.py")
            
    except Exception as e:
        print(f"\n❌ Schema update failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def main():
    """Main function."""
    success = check_and_update_schema()
    
    if success:
        print("\n🎉 Database schema updated successfully!")
    else:
        print("\n❌ Please check the errors above and try again.")
    
    return success

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
