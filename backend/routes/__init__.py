"""Routes package initialization."""
from .health import health_bp
from .payment import payment_bp
from .transaction import transaction_bp
from .webhook import webhook_bp
from .dashboard import dashboard_bp

# List of all blueprints
blueprints = [
    health_bp,
    payment_bp,
    transaction_bp,
    webhook_bp,
    dashboard_bp
]

__all__ = ['blueprints']
