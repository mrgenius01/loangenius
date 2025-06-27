"""Models package initialization."""
from utils.database import db

# Import all models here for easy access
from .transaction import Transaction

__all__ = ['db', 'Transaction']
