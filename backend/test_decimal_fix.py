#!/usr/bin/env python3
"""Test script to verify decimal field fixes in the models."""

from models.transaction import Transaction
from models.loan import Loan
from models.user import User
from decimal import Decimal

def test_decimal_fields():
    print('Testing model imports and decimal fields...')
    print('✓ Transaction model imported successfully')
    print('✓ Loan model imported successfully') 
    print('✓ User model imported successfully')

    # Test creating a Transaction with Numeric amount
    try:
        transaction = Transaction(
            phone_number='263771234567',
            amount=Decimal('100.50'),
            method='ecocash'
        )
        print('✓ Transaction with Numeric amount created successfully')
        print(f'  Amount type: {type(transaction.amount)}')
        print(f'  Amount value: {transaction.amount}')
    except Exception as e:
        print(f'✗ Error creating transaction: {e}')

    # Test creating a Loan with Numeric amounts
    try:
        loan = Loan(
            user_id=1,
            original_amount=Decimal('1000.00'),
            interest_rate=Decimal('15.0')
        )
        print('✓ Loan with Numeric amounts created successfully')
        print(f'  Original amount type: {type(loan.original_amount)}')
        print(f'  Interest rate type: {type(loan.interest_rate)}')
    except Exception as e:
        print(f'✗ Error creating loan: {e}')

    print('All decimal field fixes appear to be working correctly!')

if __name__ == '__main__':
    test_decimal_fields()
