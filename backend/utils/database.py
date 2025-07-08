"""Database utilities and initialization."""
from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy instance
db = SQLAlchemy()

def init_db(app):
    """Initialize database with Flask app."""
    db.init_app(app)
    
    with app.app_context():
        # Import all models here to ensure they are registered
        from models.transaction import Transaction
        from models.user import User
        
        # Create all tables
        db.create_all()
        print("Database tables created successfully")
        

def reset_db():
    """Reset database (drop all tables and recreate)."""
    db.drop_all()
    db.create_all()
    print("Database reset successfully")
