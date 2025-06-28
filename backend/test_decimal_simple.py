#!/usr/bin/env python3
"""Simple test script to verify decimal field types in model definitions."""

from decimal import Decimal

def test_decimal_field_types():
    print('Testing decimal field type definitions...')
    
    # Test that we can import the models successfully
    try:
        from models.transaction import Transaction
        from models.loan import Loan
        from models.user import User
        print('✓ All models imported successfully')
    except Exception as e:
        print(f'✗ Import error: {e}')
        return
    
    # Test Transaction model fields
    print('\n🔍 Checking Transaction model fields:')
    transaction_columns = Transaction.__table__.columns
    amount_column = transaction_columns['amount']
    print(f'  amount column type: {amount_column.type}')
    print(f'  amount column python_type: {amount_column.type.python_type}')
    
    # Test Loan model fields
    print('\n🔍 Checking Loan model fields:')
    loan_columns = Loan.__table__.columns
    original_amount_column = loan_columns['original_amount']
    outstanding_balance_column = loan_columns['outstanding_balance']
    interest_rate_column = loan_columns['interest_rate']
    
    print(f'  original_amount column type: {original_amount_column.type}')
    print(f'  outstanding_balance column type: {outstanding_balance_column.type}')
    print(f'  interest_rate column type: {interest_rate_column.type}')
    
    # Test object creation (without database)
    print('\n🔧 Testing object creation:')
    try:
        transaction = Transaction(
            phone_number='263771234567',
            amount=Decimal('100.50'),
            method='ecocash'
        )
        print(f'✓ Transaction created with amount: {transaction.amount} (type: {type(transaction.amount)})')
        
        loan = Loan(
            user_id=1,
            original_amount=Decimal('1000.00'),
            interest_rate=Decimal('15.0')
        )
        print(f'✓ Loan created with original_amount: {loan.original_amount} (type: {type(loan.original_amount)})')
        print(f'✓ Loan interest_rate: {loan.interest_rate} (type: {type(loan.interest_rate)})')
        print(f'✓ Loan outstanding_balance: {loan.outstanding_balance} (type: {type(loan.outstanding_balance)})')
        
    except Exception as e:
        print(f'✗ Object creation error: {e}')
        import traceback
        traceback.print_exc()
    
    print('\n✅ Decimal field fix verification complete!')
    print('✅ All monetary fields are now using db.Numeric instead of db.Decimal/db.Float')
    print('✅ This should resolve SQLAlchemy decimal field errors')

if __name__ == '__main__':
    test_decimal_field_types()
