"""Health check routes."""
from flask import Blueprint
from utils.responses import APIResponse

health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    ---
    tags:
      - System
    responses:
      200:
        description: System is healthy
        schema:
          type: object
          properties:
            status:
              type: string
              example: "success"
            message:
              type: string
              example: "Success"
            timestamp:
              type: string
              example: "2025-06-27T10:30:00.123456"
    """
    return APIResponse.success(
        message="System is healthy"
    )
