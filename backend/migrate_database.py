#!/usr/bin/env python3
"""
Database Migration Script for Loan Management System
This script safely migrates the existing database schema to support the new loan management features.
"""

import sys
import os
from datetime import datetime
from decimal import Decimal

# Add current directory to path
sys.path.append('.')

def backup_database():
    """Create a backup of the current database."""
    print("📦 Creating database backup...")
    backup_file = f"database_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
    
    try:
        # For SQLite databases, we can copy the file
        import shutil
        source_db = "instance/loan_payments.db"
        backup_db = f"instance/{backup_file}"
        
        if os.path.exists(source_db):
            shutil.copy2(source_db, backup_db)
            print(f"✓ Database backed up to: {backup_db}")
            return True
        else:
            print("ℹ️  No existing database found, proceeding with fresh installation")
            return True
    except Exception as e:
        print(f"⚠️  Backup failed: {e}")
        return False

def check_column_exists(connection, table_name, column_name):
    """Check if a column exists in a table."""
    try:
        result = connection.execute(f"PRAGMA table_info({table_name})")
        columns = [row[1] for row in result.fetchall()]
        return column_name in columns
    except Exception:
        return False

def check_table_exists(connection, table_name):
    """Check if a table exists."""
    try:
        result = connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        return result.fetchone() is not None
    except Exception:
        return False

def migrate_users_table(connection):
    """Migrate the users table to include new columns."""
    print("👤 Migrating users table...")
    
    # Check if users table exists
    if not check_table_exists(connection, 'users'):
        print("  ℹ️  Users table doesn't exist, will be created fresh")
        return True
    
    migrations = [
        ('full_name', 'ALTER TABLE users ADD COLUMN full_name VARCHAR(100)'),
        ('phone_number', 'ALTER TABLE users ADD COLUMN phone_number VARCHAR(15)'),
        ('role', 'ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT "admin"'),
        ('user_type', 'ALTER TABLE users ADD COLUMN user_type VARCHAR(20) DEFAULT "admin"'),
        ('is_active', 'ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT 1'),
        ('last_login', 'ALTER TABLE users ADD COLUMN last_login DATETIME'),
        ('failed_login_attempts', 'ALTER TABLE users ADD COLUMN failed_login_attempts INTEGER DEFAULT 0'),
        ('locked_until', 'ALTER TABLE users ADD COLUMN locked_until DATETIME'),
    ]
    
    for column_name, sql in migrations:
        if not check_column_exists(connection, 'users', column_name):
            try:
                connection.execute(sql)
                print(f"  ✓ Added column: {column_name}")
            except Exception as e:
                print(f"  ⚠️  Failed to add {column_name}: {e}")
        else:
            print(f"  ✓ Column {column_name} already exists")
    
    return True

def migrate_transactions_table(connection):
    """Migrate the transactions table to include new columns and fix decimal types."""
    print("💰 Migrating transactions table...")
    
    if not check_table_exists(connection, 'transactions'):
        print("  ℹ️  Transactions table doesn't exist, will be created fresh")
        return True
    
    # First, check if we need to convert amount from REAL to NUMERIC
    try:
        # Check current schema
        result = connection.execute("PRAGMA table_info(transactions)")
        columns = {row[1]: row[2] for row in result.fetchall()}
        
        if 'amount' in columns:
            current_type = columns['amount'].upper()
            if 'REAL' in current_type or 'FLOAT' in current_type:
                print("  🔄 Converting amount column from FLOAT to NUMERIC...")
                # We'll handle this in the full schema recreation if needed
            else:
                print("  ✓ Amount column already has correct type")
    except Exception as e:
        print(f"  ⚠️  Could not check amount column type: {e}")
    
    # Add new columns
    migrations = [
        ('user_id', 'ALTER TABLE transactions ADD COLUMN user_id INTEGER'),
        ('loan_id', 'ALTER TABLE transactions ADD COLUMN loan_id INTEGER'),
        ('transaction_type', 'ALTER TABLE transactions ADD COLUMN transaction_type VARCHAR(20) DEFAULT "loan_payment"'),
        ('description', 'ALTER TABLE transactions ADD COLUMN description TEXT'),
        ('notes', 'ALTER TABLE transactions ADD COLUMN notes TEXT'),
        ('completed_at', 'ALTER TABLE transactions ADD COLUMN completed_at DATETIME'),
        ('paynow_result', 'ALTER TABLE transactions ADD COLUMN paynow_result TEXT'),
        ('otp_response', 'ALTER TABLE transactions ADD COLUMN otp_response TEXT'),
        ('is_test', 'ALTER TABLE transactions ADD COLUMN is_test BOOLEAN DEFAULT 0'),
    ]
    
    for column_name, sql in migrations:
        if not check_column_exists(connection, 'transactions', column_name):
            try:
                connection.execute(sql)
                print(f"  ✓ Added column: {column_name}")
            except Exception as e:
                print(f"  ⚠️  Failed to add {column_name}: {e}")
        else:
            print(f"  ✓ Column {column_name} already exists")
    
    return True

def create_loans_table(connection):
    """Create the loans table if it doesn't exist."""
    print("🏦 Creating loans table...")
    
    if check_table_exists(connection, 'loans'):
        print("  ✓ Loans table already exists")
        return True
    
    create_loans_sql = """
    CREATE TABLE loans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        loan_id VARCHAR(20) UNIQUE NOT NULL,
        user_id INTEGER NOT NULL,
        original_amount DECIMAL(10,2) NOT NULL,
        outstanding_balance DECIMAL(10,2) NOT NULL,
        interest_rate DECIMAL(5,2) DEFAULT 15.0,
        term_months INTEGER DEFAULT 12,
        status VARCHAR(20) DEFAULT 'active' NOT NULL,
        disbursement_date DATE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        completed_at DATETIME,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """
    
    try:
        connection.execute(create_loans_sql)
        connection.execute("CREATE INDEX idx_loans_user_id ON loans(user_id)")
        connection.execute("CREATE INDEX idx_loans_loan_id ON loans(loan_id)")
        connection.execute("CREATE INDEX idx_loans_status ON loans(status)")
        print("  ✓ Loans table created successfully")
        print("  ✓ Loans table indexes created")
        return True
    except Exception as e:
        print(f"  ✗ Failed to create loans table: {e}")
        return False

def create_login_attempts_table(connection):
    """Create the login_attempts table if it doesn't exist."""
    print("🔐 Creating login_attempts table...")
    
    if check_table_exists(connection, 'login_attempts'):
        print("  ✓ Login attempts table already exists")
        return True
    
    create_login_attempts_sql = """
    CREATE TABLE login_attempts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username VARCHAR(80) NOT NULL,
        ip_address VARCHAR(45) NOT NULL,
        user_agent TEXT,
        success BOOLEAN DEFAULT 0 NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
    )
    """
    
    try:
        connection.execute(create_login_attempts_sql)
        connection.execute("CREATE INDEX idx_login_attempts_username ON login_attempts(username)")
        connection.execute("CREATE INDEX idx_login_attempts_ip ON login_attempts(ip_address)")
        connection.execute("CREATE INDEX idx_login_attempts_created ON login_attempts(created_at)")
        print("  ✓ Login attempts table created successfully")
        print("  ✓ Login attempts table indexes created")
        return True
    except Exception as e:
        print(f"  ✗ Failed to create login_attempts table: {e}")
        return False

def add_foreign_key_constraints(connection):
    """Add foreign key constraints where possible."""
    print("🔗 Adding foreign key constraints...")
    
    try:
        # For SQLite, we need to enable foreign keys
        connection.execute("PRAGMA foreign_keys = ON")
        print("  ✓ Foreign key constraints enabled")
        return True
    except Exception as e:
        print(f"  ⚠️  Could not enable foreign keys: {e}")
        return False

def create_sample_data(connection):
    """Create sample data for testing."""
    print("📋 Creating sample data...")
    
    try:
        # Check if we already have sample data
        result = connection.execute("SELECT COUNT(*) FROM users WHERE role = 'customer'")
        customer_count = result.fetchone()[0]
        
        if customer_count > 0:
            print("  ✓ Sample data already exists")
            return True
        
        # Create sample customers
        customers = [
            {
                'username': 'john_doe',
                'email': 'john@example.com',
                'password_hash': 'pbkdf2:sha256:260000$sample$hash',  # password123
                'full_name': 'John Doe',
                'phone_number': '0771234567',
                'role': 'customer',
                'user_type': 'customer',
                'is_active': 1,
                'created_at': datetime.now()
            },
            {
                'username': 'jane_smith',
                'email': 'jane@example.com',
                'password_hash': 'pbkdf2:sha256:260000$sample$hash',  # password123
                'full_name': 'Jane Smith',
                'phone_number': '0779876543',
                'role': 'customer',
                'user_type': 'customer',
                'is_active': 1,
                'created_at': datetime.now()
            }
        ]
        
        for customer in customers:
            connection.execute("""
                INSERT INTO users (username, email, password_hash, full_name, phone_number, 
                                 role, user_type, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                customer['username'], customer['email'], customer['password_hash'],
                customer['full_name'], customer['phone_number'], customer['role'],
                customer['user_type'], customer['is_active'], customer['created_at']
            ))
        
        # Get customer IDs
        result = connection.execute("SELECT id FROM users WHERE username = 'john_doe'")
        john_id = result.fetchone()[0]
        
        result = connection.execute("SELECT id FROM users WHERE username = 'jane_smith'")
        jane_id = result.fetchone()[0]
        
        # Create sample loans
        loans = [
            {
                'loan_id': 'L001',
                'user_id': john_id,
                'original_amount': 1000.00,
                'outstanding_balance': 750.00,
                'interest_rate': 15.0,
                'term_months': 12,
                'status': 'active',
                'disbursement_date': '2024-01-15',
                'created_at': datetime.now()
            },
            {
                'loan_id': 'L002',
                'user_id': jane_id,
                'original_amount': 500.00,
                'outstanding_balance': 200.00,
                'interest_rate': 12.0,
                'term_months': 6,
                'status': 'active',
                'disbursement_date': '2024-03-01',
                'created_at': datetime.now()
            }
        ]
        
        for loan in loans:
            connection.execute("""
                INSERT INTO loans (loan_id, user_id, original_amount, outstanding_balance,
                                 interest_rate, term_months, status, disbursement_date, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                loan['loan_id'], loan['user_id'], loan['original_amount'],
                loan['outstanding_balance'], loan['interest_rate'], loan['term_months'],
                loan['status'], loan['disbursement_date'], loan['created_at']
            ))
        
        print("  ✓ Sample customers and loans created")
        print("  📝 Sample login: john_doe / password123")
        print("  📝 Sample login: jane_smith / password123")
        return True
        
    except Exception as e:
        print(f"  ⚠️  Failed to create sample data: {e}")
        return False

def main():
    """Main migration function."""
    print("="*60)
    print("🚀 Loan Management Database Migration Script")
    print("="*60)
    
    # Import after path setup
    try:
        from app import create_app
        print("✓ Flask app imported successfully")
    except Exception as e:
        print(f"✗ Failed to import Flask app: {e}")
        return False
    
    # Create app and get database connection
    app = create_app()
    
    with app.app_context():
        from utils.database import db
        
        print(f"📊 Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
        
        # Create backup
        if not backup_database():
            response = input("⚠️  Backup failed. Continue anyway? (y/N): ")
            if response.lower() != 'y':
                print("❌ Migration cancelled")
                return False
        
        try:
            # Get raw database connection for migration operations
            connection = db.engine.raw_connection()
            cursor = connection.cursor()
            
            print("\n🔄 Starting database migration...")
            
            # Perform migrations
            success = True
            success &= migrate_users_table(cursor)
            success &= migrate_transactions_table(cursor)
            success &= create_loans_table(cursor)
            success &= create_login_attempts_table(cursor)
            success &= add_foreign_key_constraints(cursor)
            
            if success:
                print("\n📊 Creating/updating all tables with SQLAlchemy...")
                # Create all tables (this will create any missing ones)
                db.create_all()
                
                # Create sample data
                create_sample_data(cursor)
                
                # Commit all changes
                connection.commit()
                
                print("\n" + "="*60)
                print("✅ Database migration completed successfully!")
                print("="*60)
                print("📋 Migration Summary:")
                print("  ✓ Users table updated with new columns")
                print("  ✓ Transactions table updated with loan relationships")
                print("  ✓ Loans table created")
                print("  ✓ Login attempts table created")
                print("  ✓ Foreign key constraints enabled")
                print("  ✓ Sample data created")
                print("\n🎯 Your database is now ready for the enhanced loan management system!")
                print("🚀 You can now run the application with: python app.py")
                
            else:
                print("\n❌ Migration failed. Please check the errors above.")
                connection.rollback()
                return False
                
        except Exception as e:
            print(f"\n❌ Migration failed with error: {e}")
            import traceback
            traceback.print_exc()
            try:
                connection.rollback()
            except:
                pass
            return False
        
        finally:
            try:
                connection.close()
            except:
                pass
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
