"""Input validation utilities."""
import re
from typing import Dict, List, Any

class ValidationError(Exception):
    """Custom validation error."""
    pass

class PaymentValidator:
    """Validator for payment-related data."""
    
    SUPPORTED_METHODS = ['ecocash', 'innbucks', 'omari']
    PHONE_PATTERN = re.compile(r'^(\+263|0)[0-9]{9}$')
    
    @classmethod
    def validate_payment_request(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate payment request data.
        
        Args:
            data: Payment request data
            
        Returns:
            dict: Validated and cleaned data
            
        Raises:
            ValidationError: If validation fails
        """
        errors = []
        
        # Check required fields
        required_fields = ['phoneNumber', 'amount', 'method']
        for field in required_fields:
            if field not in data or not data[field]:
                errors.append(f"Missing required field: {field}")
        
        if errors:
            raise ValidationError(f"Validation failed: {', '.join(errors)}")
        
        # Validate phone number
        phone_number = str(data['phoneNumber']).strip()
        if not cls.PHONE_PATTERN.match(phone_number):
            errors.append("Invalid phone number format. Expected format: +263XXXXXXXXX or 0XXXXXXXXX")
        
        # Validate amount
        try:
            amount = float(data['amount'])
            if amount <= 0:
                errors.append("Amount must be greater than 0")
            if amount > 10000:  # Set reasonable upper limit
                errors.append("Amount cannot exceed $10,000")
        except (ValueError, TypeError):
            errors.append("Invalid amount format")
            amount = 0
        
        # Validate method
        method = str(data['method']).lower().strip()
        if method not in cls.SUPPORTED_METHODS:
            errors.append(f"Unsupported payment method. Supported: {', '.join(cls.SUPPORTED_METHODS)}")
        
        if errors:
            raise ValidationError(f"Validation failed: {', '.join(errors)}")
        
        return {
            'phoneNumber': phone_number,
            'amount': amount,
            'method': method
        }
    
    @classmethod
    def validate_otp_request(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate OTP submission data.
        
        Args:
            data: OTP request data
            
        Returns:
            dict: Validated and cleaned data
            
        Raises:
            ValidationError: If validation fails
        """
        errors = []
        
        # Check required fields
        required_fields = ['reference', 'otp']
        for field in required_fields:
            if field not in data or not data[field]:
                errors.append(f"Missing required field: {field}")
        
        if errors:
            raise ValidationError(f"Validation failed: {', '.join(errors)}")
        
        # Validate reference
        reference = str(data['reference']).strip()
        if not reference:
            errors.append("Reference cannot be empty")
        
        # Validate OTP
        otp = str(data['otp']).strip()
        if not re.match(r'^\d{6}$', otp):
            errors.append("OTP must be a 6-digit number")
        
        if errors:
            raise ValidationError(f"Validation failed: {', '.join(errors)}")
        
        return {
            'reference': reference,
            'otp': otp
        }
    
    @classmethod
    def validate_reference(cls, reference: str) -> str:
        """Validate transaction reference.
        
        Args:
            reference: Transaction reference
            
        Returns:
            str: Validated reference
            
        Raises:
            ValidationError: If validation fails
        """
        if not reference or not reference.strip():
            raise ValidationError("Reference is required")
        
        reference = reference.strip()
        
        # Check reference format (should be LOAN_XXXXXXXX or TEST_XXXXXXXX)
        if not re.match(r'^(LOAN|TEST)_[A-Z0-9]{8}$', reference):
            raise ValidationError("Invalid reference format")
        
        return reference

def validate_json_data(data: Any) -> Dict[str, Any]:
    """Validate that data is a valid JSON object.
    
    Args:
        data: Data to validate
        
    Returns:
        dict: Validated data
        
    Raises:
        ValidationError: If data is not a valid dict
    """
    if not isinstance(data, dict):
        raise ValidationError("Request body must be a JSON object")
    
    return data
