"""Main Flask application factory and initialization."""
from flask import Flask
from flask_cors import CORS
from flasgger import Swagger

from config import get_config
from utils.database import init_db
from services import PaynowService, PaymentService
from routes import blueprints
from routes.payment import init_payment_routes
from routes.transaction import init_transaction_routes
from routes.webhook import init_webhook_routes

def create_app(config_name=None):
    """Create and configure Flask application.
    
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
    CORS(app)  # Enable CORS for React Native app
    Swagger(app, template={
        "swagger": "2.0",
        "info": {
            "title": app.config['API_TITLE'],
            "version": app.config['API_VERSION'],
            "description": "Loan Repayment API with Paynow integration"
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
      # Register blueprints
    for blueprint in blueprints:
        app.register_blueprint(blueprint)
    
    # Perform startup checks
    startup_check(app)
    
    return app

def startup_check(app):
    """Perform startup checks."""
    with app.app_context():
        print("="*50)
        print("🚀 Loan Repayment Backend Starting...")
        print(f"📊 Environment: {app.config.get('ENV', 'development')}")
        print(f"🔧 Debug Mode: {app.config['DEBUG']}")
        print(f"💳 Paynow Integration ID: {app.config['PAYNOW_INTEGRATION_ID']}")
        print(f"✅ Credentials Configured: {get_config().credentials_configured}")
        
        if not get_config().credentials_configured:
            print("⚠️  WARNING: Paynow credentials not configured!")
            print("   Set PAYNOW_INTEGRATION_ID and PAYNOW_INTEGRATION_KEY environment variables")
        
        print("="*50)

def main():
    """Run the application in development mode."""
    app = create_app()
    
    print("Starting Loan Repayment Backend...")
    print("Make sure to set your Paynow credentials in environment variables:")
    print("- PAYNOW_INTEGRATION_ID")
    print("- PAYNOW_INTEGRATION_KEY")
    
    app.run(
        debug=app.config['DEBUG'],
        host='0.0.0.0',
        port=5000
    )

if __name__ == '__main__':
    main()
