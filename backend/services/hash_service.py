"""Hash generation utilities for Paynow integration."""
import hashlib

def generate_paynow_hash(items, integration_key):
    """Generate a SHA512 hash for Paynow requests (based on Paynow SDK implementation).
    
    Args:
        items (dict): The transaction dictionary to hash
        integration_key (str): Merchant integration key to use during hashing
    
    Returns:
        str: The hashed transaction
    """
    out = ""
    for key, value in items.items():
        if str(key).lower() == 'hash':
            continue
        out += str(value)
    
    out += integration_key.lower()
    
    return hashlib.sha512(out.encode('utf-8')).hexdigest().upper()

class HashService:
    """Service class for hash generation operations."""
    
    def __init__(self, integration_key):
        """Initialize hash service with integration key."""
        self.integration_key = integration_key
    
    def generate_hash(self, data):
        """Generate hash for the given data."""
        return generate_paynow_hash(data, self.integration_key)
    
    def generate_otp_hash(self, otp_data):
        """Generate hash specifically for OTP requests."""
        return self.generate_hash(otp_data)
