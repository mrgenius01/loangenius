"""Application configuration settings."""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Base configuration class."""
    
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Database settings
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///loan_payments.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Paynow settings
    PAYNOW_INTEGRATION_ID = os.getenv('PAYNOW_INTEGRATION_ID', 'YOUR_INTEGRATION_ID')
    PAYNOW_INTEGRATION_KEY = os.getenv('PAYNOW_INTEGRATION_KEY', 'YOUR_INTEGRATION_KEY')
    RETURN_URL = os.getenv('RETURN_URL', 'http://localhost:3000/payment/return')
    RESULT_URL = os.getenv('RESULT_URL', 'http://localhost:5000/paynow/result')
    
    # API settings
    API_TITLE = 'Loan Repayment API'
    API_VERSION = 'v1.0'
    
    @property
    def credentials_configured(self):
        """Check if Paynow credentials are configured."""
        return self.PAYNOW_INTEGRATION_ID != 'YOUR_INTEGRATION_ID'

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///loan_payments_dev.db')

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://user:pass@localhost/loan_payments')

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Get configuration based on environment."""
    env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, config['default'])
