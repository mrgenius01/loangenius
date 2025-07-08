#!/usr/bin/env python3
"""
Database migration script to add fee and total fields to transactions table.
"""

import sys
import os
from sqlalchemy import text
from decimal import Decimal

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.database import db
from models.transaction import Transaction
from app import create_app

def add_transaction_fields():
    """Add fee and total fields to transactions table."""
    app = create_app()
    
    with app.app_context():
        try:
            # Check if columns already exist
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('transactions')]
            
            print(f"Current columns in transactions table: {columns}")
            
            # Add fee column if it doesn't exist
            if 'fee' not in columns:
                print("Adding 'fee' column...")
                db.engine.execute(text("""
                    ALTER TABLE transactions 
                    ADD COLUMN fee DECIMAL(10,2) DEFAULT 0.00 NOT NULL
                """))
                print("✅ Added 'fee' column")
            else:
                print("✅ 'fee' column already exists")
            
            # Add total column if it doesn't exist
            if 'total' not in columns:
                print("Adding 'total' column...")
                db.engine.execute(text("""
                    ALTER TABLE transactions 
                    ADD COLUMN total DECIMAL(10,2) NOT NULL DEFAULT 0.00
                """))
                print("✅ Added 'total' column")
            else:
                print("✅ 'total' column already exists")
            
            # Update existing transactions to have proper total values
            print("Updating existing transaction totals...")
            
            transactions = Transaction.query.all()
            updated_count = 0
            
            for transaction in transactions:
                # Calculate total = amount + fee (fee defaults to 0)
                fee = getattr(transaction, 'fee', Decimal('0.00')) or Decimal('0.00')
                amount = transaction.amount or Decimal('0.00')
                new_total = amount + fee
                
                # Update total if it's different
                current_total = getattr(transaction, 'total', Decimal('0.00')) or Decimal('0.00')
                if current_total != new_total:
                    transaction.total = new_total
                    updated_count += 1
            
            # Commit all changes
            db.session.commit()
            
            print(f"✅ Updated {updated_count} transactions with correct totals")
            
            # Verify the changes
            print("\nVerification:")
            sample_transactions = Transaction.query.limit(5).all()
            for tx in sample_transactions:
                print(f"  Transaction {tx.id}: amount=${tx.amount}, fee=${getattr(tx, 'fee', 'N/A')}, total=${getattr(tx, 'total', 'N/A')}")
            
            print("\n🎉 Migration completed successfully!")
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    print("Starting transaction fields migration...")
    add_transaction_fields()
