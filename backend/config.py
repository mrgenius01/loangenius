"""Application configuration settings."""
import os
from dotenv import load_dotenv
from urllib.parse import quote_plus
# Load environment variables
load_dotenv()

class Config:
    """Base configuration class."""
    
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    USE_SQLITE = os.getenv('USE_SQLITE', 'false').lower() == 'true'
    
    if USE_SQLITE:
        # SQLite configuration for development
        basedir = os.path.abspath(os.path.dirname(__file__))
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(basedir, os.getenv("SQLITE_DATABASE_PATH", "instance/loan_mg.db"))}'
        print(f"Using SQLite: {SQLALCHEMY_DATABASE_URI}")
    else:
        # SQL Server configuration
        server = os.getenv('MYSQL_HOST')  # Actually SQL Server
        database = os.getenv('MYSQL_DATABASE')
        username = os.getenv('MYSQL_USER')
        password = os.getenv('MYSQL_PASSWORD')
        port = os.getenv('MYSQL_PORT', '1433')
        
        # URL encode password to handle special characters
        encoded_password = quote_plus(password) if password else ''
        
        # SQL Server connection string
        SQLALCHEMY_DATABASE_URI = (
            f"mssql+pyodbc://{username}:{encoded_password}@{server}:{port}/{database}"
            f"?driver=ODBC+Driver+18+for+SQL+Server"
            f"&Encrypt=yes"
            f"&TrustServerCertificate=no"
        )
        print(f"Using SQL Server: {server}/{database}")
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_timeout': 30,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
        'echo': False
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
