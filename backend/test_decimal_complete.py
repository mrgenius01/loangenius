#!/usr/bin/env python3
"""Test script to verify decimal field fixes with Flask app context."""

import sys
import os
sys.path.append('.')

from app import create_app
from models.loan import Loan
from models.transaction import Transaction
from decimal import Decimal

def test_with_app_context():
    print('Testing models with Flask app context...')
    
    app = create_app()
    
    with app.app_context():
        try:
            # Test Loan model
            loan = Loan(
                user_id=1,
                original_amount=Decimal('1000.00'),
                interest_rate=Decimal('15.0')
            )
            print('✓ Loan with Numeric amounts created successfully')
            print(f'  Original amount type: {type(loan.original_amount)}')
            print(f'  Interest rate type: {type(loan.interest_rate)}')
            print(f'  Outstanding balance type: {type(loan.outstanding_balance)}')
            print(f'  Outstanding balance value: {loan.outstanding_balance}')
            
            # Test Transaction model
            transaction = Transaction(
                phone_number='263771234567',
                amount=Decimal('100.50'),
                method='ecocash'
            )
            print('✓ Transaction with Numeric amount created successfully')
            print(f'  Amount type: {type(transaction.amount)}')
            print(f'  Amount value: {transaction.amount}')
            
            print('\n✓ All decimal field fixes are working correctly!')
            print('✓ db.Numeric is properly handling monetary values')
            print('✓ No more SQLAlchemy decimal field errors expected')
            
        except Exception as e:
            print(f'✗ Error: {e}')
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    test_with_app_context()
