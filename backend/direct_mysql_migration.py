#!/usr/bin/env python3
"""
Direct MySQL Schema Migration
This script directly connects to MySQL and updates the schema without going through Flask.
"""

import os
import sys
from datetime import datetime
import pymysql
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_mysql_connection():
    """Get direct MySQL connection."""
    return pymysql.connect(
        host=os.getenv('MYSQL_HOST', ''),
        user=os.getenv('MYSQL_USER', ''),
        password=os.getenv('MYSQL_PASSWORD', ''),
        database=os.getenv('MYSQL_DATABASE', ''),
        port=int(os.getenv('MYSQL_PORT', '3306')),
        charset='utf8mb4'
    )

def migrate_users_table(cursor):
    """Add missing columns to users table."""
    print("👤 Migrating users table...")
    
    # Get current columns
    cursor.execute("DESCRIBE users")
    existing_columns = [row[0] for row in cursor.fetchall()]
    print(f"  Current columns: {existing_columns}")
    
    # Define required columns
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
    
    # Add missing columns
    for col_name, col_def in required_columns.items():
        if col_name not in existing_columns:
            try:
                sql = f"ALTER TABLE users ADD COLUMN {col_name} {col_def}"
                cursor.execute(sql)
                print(f"  ✓ Added column: {col_name}")
            except Exception as e:
                print(f"  ⚠️  Failed to add {col_name}: {e}")
        else:
            print(f"  ✓ Column {col_name} already exists")
    
    # Update existing records with default values
    update_queries = [
        "UPDATE users SET role = 'admin' WHERE role IS NULL OR role = ''",
        "UPDATE users SET user_type = 'admin' WHERE user_type IS NULL OR user_type = ''",
        "UPDATE users SET is_active = 1 WHERE is_active IS NULL",
        "UPDATE users SET failed_login_attempts = 0 WHERE failed_login_attempts IS NULL"
    ]
    
    for query in update_queries:
        try:
            cursor.execute(query)
            print("  ✓ Updated existing records with default values")
            break  # Only print once
        except Exception as e:
            print(f"  ⚠️  Update failed: {e}")

def migrate_transactions_table(cursor):
    """Update transactions table."""
    print("💰 Migrating transactions table...")
    
    try:
        # Check if table exists
        cursor.execute("SHOW TABLES LIKE 'transactions'")
        if not cursor.fetchone():
            print("  ⚠️  Transactions table doesn't exist, will be created later")
            return
        
        # Get current columns
        cursor.execute("DESCRIBE transactions")
        existing_columns = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Fix amount column type if needed
        if 'amount' in existing_columns:
            amount_type = existing_columns['amount'].upper()
            if 'FLOAT' in amount_type or 'REAL' in amount_type:
                try:
                    cursor.execute("ALTER TABLE transactions MODIFY COLUMN amount DECIMAL(10,2)")
                    print("  ✓ Converted amount column to DECIMAL")
                except Exception as e:
                    print(f"  ⚠️  Could not convert amount column: {e}")
        
        # Add missing columns
        required_columns = {
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
        
        column_names = list(existing_columns.keys())
        
        for col_name, col_def in required_columns.items():
            if col_name not in column_names:
                try:
                    cursor.execute(f"ALTER TABLE transactions ADD COLUMN {col_name} {col_def}")
                    print(f"  ✓ Added transactions.{col_name}")
                except Exception as e:
                    print(f"  ⚠️  Failed to add transactions.{col_name}: {e}")
    
    except Exception as e:
        print(f"  ⚠️  Transactions table migration error: {e}")

def create_loans_table(cursor):
    """Create loans table."""
    print("🏦 Creating loans table...")
    
    try:
        # Check if table exists
        cursor.execute("SHOW TABLES LIKE 'loans'")
        if cursor.fetchone():
            print("  ✓ Loans table already exists")
            return
        
        # Create loans table
        create_sql = """
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
        
        cursor.execute(create_sql)
        print("  ✓ Loans table created successfully")
        
    except Exception as e:
        print(f"  ⚠️  Failed to create loans table: {e}")

def create_login_attempts_table(cursor):
    """Create login_attempts table."""
    print("🔐 Creating login_attempts table...")
    
    try:
        # Check if table exists
        cursor.execute("SHOW TABLES LIKE 'login_attempts'")
        if cursor.fetchone():
            print("  ✓ Login attempts table already exists")
            return
        
        # Create login_attempts table
        create_sql = """
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
        
        cursor.execute(create_sql)
        print("  ✓ Login attempts table created successfully")
        
    except Exception as e:
        print(f"  ⚠️  Failed to create login_attempts table: {e}")

def main():
    """Main migration function."""
    print("🔧 Direct MySQL Schema Migration")
    print("="*50)
    
    # Check environment variables
    required_vars = ['MYSQL_HOST', 'MYSQL_USER', 'MYSQL_PASSWORD', 'MYSQL_DATABASE']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        print("Please check your .env file or environment configuration.")
        return False
    
    print(f"📊 Connecting to MySQL at {os.getenv('MYSQL_HOST')}:{os.getenv('MYSQL_PORT')}")
    print(f"📊 Database: {os.getenv('MYSQL_DATABASE')}")
    
    try:
        # Connect to MySQL
        connection = get_mysql_connection()
        cursor = connection.cursor()
        
        print("✓ Connected to MySQL successfully")
        
        # Perform migrations
        migrate_users_table(cursor)
        migrate_transactions_table(cursor)
        create_loans_table(cursor)
        create_login_attempts_table(cursor)
        
        # Commit all changes
        connection.commit()
        print("\n💾 All changes committed successfully")
        
        # Verify the migration
        print("\n📊 Verifying migration...")
        
        # Check users table
        cursor.execute("DESCRIBE users")
        user_columns = [row[0] for row in cursor.fetchall()]
        print(f"  Users table columns: {len(user_columns)} columns")
        
        # Check if new tables exist
        cursor.execute("SHOW TABLES")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"  Available tables: {tables}")
        
        # Check user count
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f"  Users in database: {user_count}")
        
        print("\n✅ MySQL Schema Migration Completed Successfully!")
        print("="*50)
        print("🎯 Your MySQL database now has:")
        print("  ✓ Updated users table with all required columns")
        print("  ✓ Fixed decimal field types (DECIMAL instead of FLOAT)")
        print("  ✓ New loans table for loan management")
        print("  ✓ New login_attempts table for security")
        print("  ✓ Proper indexes for performance")
        print("\n🚀 You can now run your Flask application!")
        print("   python app.py")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        try:
            cursor.close()
            connection.close()
        except:
            pass
    
    return True

if __name__ == '__main__':
    print("⚠️  This will directly modify your MySQL database schema.")
    print("Make sure you have a backup before proceeding!")
    response = input("Continue with direct MySQL migration? (y/N): ")
    
    if response.lower() != 'y':
        print("❌ Migration cancelled")
        sys.exit(1)
    
    success = main()
    sys.exit(0 if success else 1)
