"""Standardized API response utilities."""
from flask import jsonify
from datetime import datetime

class APIResponse:
    """Utility class for creating standardized API responses."""
    
    @staticmethod
    def success(data=None, message="Success", status_code=200):
        """Create a success response.
        
        Args:
            data: Response data
            message: Success message
            status_code: HTTP status code
            
        Returns:
            tuple: (response, status_code)
        """
        response = {
            "status": "success",
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        
        if data is not None:
            if isinstance(data, dict):
                response.update(data)
            else:
                response["data"] = data
        
        return jsonify(response), status_code
    
    @staticmethod
    def error(message="An error occurred", errors=None, status_code=400, error_code=None):
        """Create an error response.
        
        Args:
            message: Error message
            errors: List of specific errors
            status_code: HTTP status code
            error_code: Application-specific error code
            
        Returns:
            tuple: (response, status_code)
        """
        response = {
            "status": "error",
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        
        if errors:
            response["errors"] = errors if isinstance(errors, list) else [errors]
        
        if error_code:
            response["error_code"] = error_code
        
        return jsonify(response), status_code
    
    @staticmethod
    def validation_error(message="Validation failed", errors=None):
        """Create a validation error response.
        
        Args:
            message: Error message
            errors: List of validation errors
            
        Returns:
            tuple: (response, status_code)
        """
        return APIResponse.error(
            message=message,
            errors=errors,
            status_code=400,
            error_code="VALIDATION_ERROR"
        )
    
    @staticmethod
    def not_found(message="Resource not found", resource_type=None):
        """Create a not found response.
        
        Args:
            message: Error message
            resource_type: Type of resource not found
            
        Returns:
            tuple: (response, status_code)
        """
        if resource_type:
            message = f"{resource_type} not found"
        
        return APIResponse.error(
            message=message,
            status_code=404,
            error_code="NOT_FOUND"
        )
    
    @staticmethod
    def internal_error(message="Internal server error", debug_info=None):
        """Create an internal server error response.
        
        Args:
            message: Error message
            debug_info: Debug information (only in development)
            
        Returns:
            tuple: (response, status_code)
        """
        response_data = {
            "message": message,
            "error_code": "INTERNAL_ERROR"
        }
        
        if debug_info:
            response_data["debug_info"] = debug_info
        
        return APIResponse.error(
            **response_data,
            status_code=500
        )
    
    @staticmethod
    def payment_success(data):
        """Create a payment success response.
        
        Args:
            data: Payment response data
            
        Returns:
            tuple: (response, status_code)
        """
        return APIResponse.success(
            data=data,
            message="Payment request processed successfully"
        )
    
    @staticmethod
    def payment_error(message, errors=None, debug_info=None):
        """Create a payment error response.
        
        Args:
            message: Error message
            errors: List of errors
            debug_info: Debug information
            
        Returns:
            tuple: (response, status_code)
        """
        response_data = {
            "message": message,
            "error_code": "PAYMENT_ERROR"
        }
        
        if errors:
            response_data["errors"] = errors
        
        if debug_info:
            response_data["debug_info"] = debug_info
        
        return APIResponse.error(**response_data, status_code=400)
