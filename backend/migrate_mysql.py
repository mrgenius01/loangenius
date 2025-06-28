#!/usr/bin/env python3
"""
MySQL Database Schema Migration Script
Updates the remote MySQL database schema to match the new models.
"""

import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.append('.')

def migrate_mysql_schema():
    """Migrate the MySQL database schema."""
    print("🗄️  MySQL Database Schema Migration")
    print("="*50)
    
    try:
        from app import create_app
        app = create_app()
        
        print(f"📊 Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
        
        with app.app_context():
            from utils.database import db
            
            # Get raw connection for DDL operations
            with db.engine.connect() as conn:
                print("🔍 Checking current MySQL schema...")
                
                # Check if users table exists and its structure
                try:
                    result = conn.execute("DESCRIBE users")
                    existing_columns = [row[0] for row in result.fetchall()]
                    print(f"  Current users columns: {existing_columns}")
                    
                    # Define required columns with their definitions
                    required_columns = {
                        'full_name': 'VARCHAR(100)',
                        'phone_number': 'VARCHAR(15)',
                        'role': 'VARCHAR(20) DEFAULT "admin"',
                        'user_type': 'VARCHAR(20) DEFAULT "admin"',
                        'is_active': 'BOOLEAN DEFAULT 1',
                        'last_login': 'DATETIME',
                        'failed_login_attempts': 'INT DEFAULT 0',
                        'locked_until': 'DATETIME'
                    }
                    
                    print("🔧 Adding missing columns to users table...")
                    for col_name, col_def in required_columns.items():
                        if col_name not in existing_columns:
                            try:
                                sql = f"ALTER TABLE users ADD COLUMN {col_name} {col_def}"
                                conn.execute(sql)
                                print(f"  ✓ Added column: {col_name}")
                            except Exception as e:
                                print(f"  ⚠️  Failed to add {col_name}: {e}")
                        else:
                            print(f"  ✓ Column {col_name} already exists")
                    
                    # Update existing users with default values
                    print("🔄 Updating existing users with default values...")
                    update_queries = [
                        "UPDATE users SET role = 'admin' WHERE role IS NULL OR role = ''",
                        "UPDATE users SET user_type = 'admin' WHERE user_type IS NULL OR user_type = ''",
                        "UPDATE users SET is_active = 1 WHERE is_active IS NULL",
                        "UPDATE users SET failed_login_attempts = 0 WHERE failed_login_attempts IS NULL"
                    ]
                    
                    for query in update_queries:
                        try:
                            conn.execute(query)
                            print("  ✓ Updated existing user records")
                        except Exception as e:
                            print(f"  ⚠️  Update failed: {e}")
                
                except Exception as e:
                    print(f"  ⚠️  Could not check users table: {e}")
                
                # Check if transactions table needs decimal field fix
                try:
                    result = conn.execute("DESCRIBE transactions")
                    trans_columns = {row[0]: row[1] for row in result.fetchall()}
                    
                    if 'amount' in trans_columns:
                        amount_type = trans_columns['amount'].upper()
                        if 'FLOAT' in amount_type or 'REAL' in amount_type:
                            print("🔧 Converting transactions.amount to DECIMAL...")
                            try:
                                conn.execute("ALTER TABLE transactions MODIFY COLUMN amount DECIMAL(10,2)")
                                print("  ✓ Converted amount column to DECIMAL")
                            except Exception as e:
                                print(f"  ⚠️  Could not convert amount column: {e}")
                        else:
                            print("  ✓ Transactions amount column already DECIMAL")
                    
                    # Add missing transaction columns
                    trans_required_columns = {
                        'user_id': 'INT',
                        'loan_id': 'INT',
                        'transaction_type': 'VARCHAR(20) DEFAULT "loan_payment"',
                        'description': 'TEXT',
                        'notes': 'TEXT',
                        'completed_at': 'DATETIME',
                        'paynow_result': 'TEXT',
                        'otp_response': 'TEXT',
                        'is_test': 'BOOLEAN DEFAULT 0'
                    }
                    
                    trans_existing = [row[0] for row in conn.execute("DESCRIBE transactions").fetchall()]
                    
                    for col_name, col_def in trans_required_columns.items():
                        if col_name not in trans_existing:
                            try:
                                conn.execute(f"ALTER TABLE transactions ADD COLUMN {col_name} {col_def}")
                                print(f"  ✓ Added transactions.{col_name}")
                            except Exception as e:
                                print(f"  ⚠️  Failed to add transactions.{col_name}: {e}")
                
                except Exception as e:
                    print(f"  ℹ️  Transactions table check: {e}")
                
                # Create loans table if it doesn't exist
                print("🏦 Creating loans table...")
                try:
                    # Check if loans table exists
                    result = conn.execute("SHOW TABLES LIKE 'loans'")
                    if result.fetchone() is None:
                        create_loans_sql = """
                        CREATE TABLE loans (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            loan_id VARCHAR(20) UNIQUE NOT NULL,
                            user_id INT NOT NULL,
                            original_amount DECIMAL(10,2) NOT NULL,
                            outstanding_balance DECIMAL(10,2) NOT NULL,
                            interest_rate DECIMAL(5,2) DEFAULT 15.0,
                            term_months INT DEFAULT 12,
                            status VARCHAR(20) DEFAULT 'active' NOT NULL,
                            disbursement_date DATE,
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                            completed_at DATETIME,
                            INDEX idx_loans_user_id (user_id),
                            INDEX idx_loans_loan_id (loan_id),
                            INDEX idx_loans_status (status)
                        ) ENGINE=InnoDB
                        """
                        conn.execute(create_loans_sql)
                        print("  ✓ Loans table created")
                    else:
                        print("  ✓ Loans table already exists")
                except Exception as e:
                    print(f"  ⚠️  Loans table creation failed: {e}")
                
                # Create login_attempts table
                print("🔐 Creating login_attempts table...")
                try:
                    result = conn.execute("SHOW TABLES LIKE 'login_attempts'")
                    if result.fetchone() is None:
                        create_login_attempts_sql = """
                        CREATE TABLE login_attempts (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            username VARCHAR(80) NOT NULL,
                            ip_address VARCHAR(45) NOT NULL,
                            user_agent TEXT,
                            success BOOLEAN DEFAULT 0 NOT NULL,
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                            INDEX idx_login_attempts_username (username),
                            INDEX idx_login_attempts_ip (ip_address),
                            INDEX idx_login_attempts_created (created_at)
                        ) ENGINE=InnoDB
                        """
                        conn.execute(create_login_attempts_sql)
                        print("  ✓ Login attempts table created")
                    else:
                        print("  ✓ Login attempts table already exists")
                except Exception as e:
                    print(f"  ⚠️  Login attempts table creation failed: {e}")
                
                # Commit all changes
                conn.commit()
                print("💾 All schema changes committed")
        
        # Now test the updated schema
        print("\n📊 Testing updated schema...")
        with app.app_context():
            from models.user import User
            from models.loan import Loan
            from models.transaction import Transaction
            
            try:
                user_count = User.query.count()
                print(f"  ✓ Users: {user_count} records accessible")
            except Exception as e:
                print(f"  ✗ Users table error: {e}")
                return False
            
            try:
                loan_count = Loan.query.count()
                print(f"  ✓ Loans: {loan_count} records accessible")
            except Exception as e:
                print(f"  ✗ Loans table error: {e}")
                return False
            
            try:
                transaction_count = Transaction.query.count()
                print(f"  ✓ Transactions: {transaction_count} records accessible")
            except Exception as e:
                print(f"  ✗ Transactions table error: {e}")
                return False
        
        print("\n✅ MySQL Schema Migration Completed!")
        print("="*50)
        print("🎯 Your MySQL database now has:")
        print("  ✓ Updated users table with all required columns")
        print("  ✓ Fixed decimal field types (DECIMAL instead of FLOAT)")
        print("  ✓ New loans table for loan management")
        print("  ✓ New login_attempts table for security")
        print("  ✓ Proper indexes for performance")
        print("\n🚀 Your application should now work without schema errors!")
        
    except Exception as e:
        print(f"\n❌ MySQL migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def main():
    """Main function."""
    print("This will update your MySQL database schema to match the new models.")
    print("⚠️  Make sure you have a backup of your database before proceeding.")
    response = input("Continue with MySQL schema migration? (y/N): ")
    
    if response.lower() != 'y':
        print("❌ Migration cancelled")
        return False
    
    success = migrate_mysql_schema()
    
    if success:
        print("\n🎉 MySQL database updated successfully!")
        print("You can now run: python app.py")
    else:
        print("\n❌ Please check the errors above and try again.")
    
    return success

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
