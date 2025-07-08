"""Enhanced Flask application with loan management."""
from flask import Flask
from flask_login import LoginManager
from flask_cors import CORS
from flasgger import Swagger

from config import get_config
from utils.database import init_db
from services import PaynowService, PaymentService
from routes import blueprints
from routes.auth import auth_bp
from routes.payment import init_payment_routes
from routes.transaction import init_transaction_routes
from routes.webhook import init_webhook_routes
from routes.customer import init_customer_routes, customer_bp
from routes.dashboard import dashboard_bp

# Initialize Flask-Login
login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    from models.user import User
    return User.query.get(int(user_id))

def create_app(config_name=None):
    """Create and configure Flask application with loan management.
    
    Args:
        config_name: Configuration name ('development', 'production', 'testing')
        
    Returns:
        Flask: Configured Flask application
    """
    # Create Flask app
    app = Flask(__name__)
    
    # Load configuration
    config_class = get_config()
    app.config.from_object(config_class)
    
    # Initialize extensions
    CORS(app, supports_credentials=True)  # Enable CORS for React Native app
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    
    Swagger(app, template={
        "swagger": "2.0",
        "info": {
            "title": app.config['API_TITLE'],
            "version": app.config['API_VERSION'],
            "description": "Loan Repayment API with Paynow integration and Loan Management"
        }
    })
    
    # Initialize database
    init_db(app)
    
    # Initialize services
    paynow_service = PaynowService(
        app.config['PAYNOW_INTEGRATION_ID'],
        app.config['PAYNOW_INTEGRATION_KEY'],
        app.config['RETURN_URL'],
        app.config['RESULT_URL']
    )
    
    payment_service = PaymentService(paynow_service)
    
    # Initialize routes with service dependencies
    init_payment_routes(payment_service)
    init_transaction_routes(payment_service)
    init_webhook_routes(payment_service)
    init_customer_routes(payment_service)
    
    # Register authentication blueprint
    app.register_blueprint(auth_bp)
    
    # Register customer management blueprint
    app.register_blueprint(customer_bp)
    
    # Register admin dashboard blueprint
    app.register_blueprint(dashboard_bp)
    
    # Register existing blueprints
    for blueprint in blueprints:
        app.register_blueprint(blueprint)
    
    # Perform startup checks
    startup_check(app)
    
    # Create tables and check for initial setup
    with app.app_context():
        from utils.database import db
        from models.user import User
        from models.loan import Loan
        from models.transaction import Transaction
        
        # Create all tables including new loan tables
        db.create_all()
        
        # Check if we need initial setup
        if User.query.count() == 0:
            print("⚠️  No admin users found. Please visit /auth/setup to create an admin user.")
            
        # Create some sample data for demonstration (remove in production)
        create_sample_data()
    
    return app

def create_sample_data():
    """Create sample loan data for demonstration."""
    from utils.database import db
    from models.user import User
    from models.loan import Loan
    from models.transaction import Transaction
    from decimal import Decimal
    from datetime import datetime, date
    
    try:
        # Check if sample data already exists
        if User.query.filter_by(role='customer').first():
            return  # Sample data already exists
        
        # Create sample customers
        customers = [
            {
                'username': 'john_doe',
                'full_name': 'John Doe',
                'phone_number': '0771234567',
                'email': 'john@example.com',
                'role': 'customer'
            },
            {
                'username': 'jane_smith',
                'full_name': 'Jane Smith', 
                'phone_number': '0779876543',
                'email': 'jane@example.com',
                'role': 'customer'
            },
            {
                'username': 'mike_jones',
                'full_name': 'Mike Jones',
                'phone_number': '0775555555',
                'email': 'mike@example.com',
                'role': 'customer'
            }
        ]
        
        created_customers = []
        for customer_data in customers:
            customer = User(**customer_data)
            customer.set_password('password123')  # Default password for demo
            db.session.add(customer)
            created_customers.append(customer)
        
        db.session.commit()
        
        # Create sample loans
        loans_data = [
            {
                'user_id': created_customers[0].id,
                'original_amount': Decimal('1000.00'),
                'interest_rate': Decimal('15.0'),
                'term_months': 12,
                'status': 'active',
                'disbursement_date': date(2024, 1, 15)
            },
            {
                'user_id': created_customers[0].id,
                'original_amount': Decimal('500.00'),
                'interest_rate': Decimal('12.0'),
                'term_months': 6,
                'status': 'completed',
                'disbursement_date': date(2023, 6, 1)
            },
            {
                'user_id': created_customers[1].id,
                'original_amount': Decimal('2000.00'),
                'interest_rate': Decimal('18.0'),
                'term_months': 24,
                'status': 'active',
                'disbursement_date': date(2024, 3, 1)
            },
            {
                'user_id': created_customers[2].id,
                'original_amount': Decimal('750.00'),
                'interest_rate': Decimal('15.0'),
                'term_months': 8,
                'status': 'active',
                'disbursement_date': date(2024, 5, 1)
            }
        ]
        
        for loan_data in loans_data:
            loan = Loan(**loan_data)
            db.session.add(loan)
        
        db.session.commit()
        
        print("✅ Sample loan data created successfully!")
        print("📋 Created 3 sample customers and 4 sample loans")
        print("🔑 Customer login credentials: username/password123")
        
    except Exception as e:
        print(f"⚠️  Failed to create sample data: {e}")
        db.session.rollback()

def startup_check(app):
    """Perform enhanced startup checks."""
    with app.app_context():
        
        if not get_config().credentials_configured:
            print("⚠️  WARNING: Paynow credentials not configured!")
            print("   Set PAYNOW_INTEGRATION_ID and PAYNOW_INTEGRATION_KEY environment variables")
        
        # Check database models
        from utils.database import db
        try:
            from models.user import User
            from models.loan import Loan
            from models.transaction import Transaction
            
            user_count = User.query.count()
            loan_count = Loan.query.count()
            transaction_count = Transaction.query.count()
            
            print(f"📊 Database Status:")
            print(f"   👤 Users: {user_count}")
            print(f"   🏦 Loans: {loan_count}")
            print(f"   💰 Transactions: {transaction_count}")
            
        except Exception as e:
            print(f"⚠️  Database check failed: {e}")
        
        print("="*60)

def main():
    """Run the enhanced application in development mode."""
    app = create_app()
    
    print("\nMake sure to set your Paynow credentials in environment variables:")
    print("- PAYNOW_INTEGRATION_ID")
    print("- PAYNOW_INTEGRATION_KEY")
    
    app.run(
        debug=app.config['DEBUG'],
        host='0.0.0.0',
        port=5000
    )

if __name__ == '__main__':
    main()
