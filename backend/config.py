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
    
    # Database settings - MySQL Remote
    MYSQL_HOST = os.getenv('MYSQL_HOST', '')
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', '')
    MYSQL_USER = os.getenv('MYSQL_USER', '')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', ''))
    
    # Construct MySQL connection string
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'connect_args': {
            'connect_timeout': 60,
            'read_timeout': 60,
            'write_timeout': 60
        }
    }
    
    # Paynow settings
    PAYNOW_INTEGRATION_ID = os.getenv('PAYNOW_INTEGRATION_ID', '19347')
    PAYNOW_INTEGRATION_KEY = os.getenv('PAYNOW_INTEGRATION_KEY', 'b2779626-ac45-40f1-9770-aa7cbc36f4e0')
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
    # Use the same MySQL database for development

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    # Use the same MySQL database for production

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
