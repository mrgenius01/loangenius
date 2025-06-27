"""Paynow integration service."""
import requests
import urllib.parse
from paynow import Paynow
from services.hash_service import HashService

class PaynowService:
    """Service class for Paynow integration operations."""
    
    def __init__(self, integration_id, integration_key, return_url, result_url):
        """Initialize Paynow service."""
        self.integration_id = integration_id
        self.integration_key = integration_key
        self.return_url = return_url
        self.result_url = result_url
        
        # Initialize Paynow SDK
        self.paynow = Paynow(
            integration_id,
            integration_key,
            return_url,
            result_url
        )
        
        # Initialize hash service
        self.hash_service = HashService(integration_key)
    
    def create_payment(self, reference, amount, phone_number, method):
        """Create and send a payment request to Paynow.
        
        Args:
            reference (str): Unique payment reference
            amount (float): Payment amount
            phone_number (str): Customer phone number
            method (str): Payment method (ecocash, innbucks, omari)
        
        Returns:
            PaynowResponse: Response from Paynow
        """
        # Create payment
        payment = self.paynow.create_payment(reference, f"loan-user@{phone_number}")
        payment.add('Loan Repayment', amount)
        
        # Send payment based on method
        if method == 'ecocash':
            response = self.paynow.send_mobile(payment, phone_number, 'ecocash')
        elif method == 'innbucks':
            # Note: Check if Paynow supports innbucks or use 'onemoney'
            response = self.paynow.send_mobile(payment, phone_number, 'onemoney')
        elif method == 'omari':
            # OMari uses Express Checkout, not mobile payments
            response = self.paynow.send_mobile(payment, phone_number, 'omari')
            # If mobile doesn't work, try express checkout
            if not response.success:
                print("Mobile OMari failed, trying Express Checkout...")
                response = self.paynow.create_checkout(payment)
        else:
            raise ValueError(f"Unsupported payment method: {method}")
        
        return PaynowResponse(response, method)
    
    def check_transaction_status(self, poll_url):
        """Check transaction status using poll URL.
        
        Args:
            poll_url (str): Poll URL from Paynow
        
        Returns:
            StatusResponse: Status response from Paynow
        """
        return self.paynow.check_transaction_status(poll_url)
    
    def submit_otp(self, otp_url, integration_id, otp, paynow_instance=None):
        """Submit OTP to Paynow for OMari payments.
        
        Args:
            otp_url (str): OTP submission URL
            integration_id (str): Paynow integration ID
            otp (str): OTP code
            paynow_instance: Paynow instance for hash generation
        
        Returns:
            dict: Parsed response from Paynow
        """
        # Prepare OTP submission data
        otp_data = {
            'id': integration_id,
            'otp': otp,
            'status': 'Message',
        }
        
        # Generate hash for OTP request
        try:
            if paynow_instance:
                otp_hash = paynow_instance._Paynow__hash(otp_data, self.integration_key)
            else:
                otp_hash = self.hash_service.generate_otp_hash(otp_data)
            otp_data['hash'] = otp_hash
        except Exception as e:
            print(f"Error generating OTP hash: {e}")
            # Fallback to custom hash function
            otp_hash = self.hash_service.generate_otp_hash(otp_data)
            otp_data['hash'] = otp_hash
        
        print(f"Submitting OTP to: {otp_url}")
        print(f"OTP data: {otp_data}")
        
        # Submit OTP to Paynow
        response = requests.post(otp_url, data=otp_data, timeout=30)
        
        print(f"OTP Response status: {response.status_code}")
        print(f"OTP Response text: {response.text}")
        
        if response.status_code == 200:
            # Parse response (Paynow returns URL-encoded data)
            response_data = {}
            for pair in response.text.split('&'):
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    # URL decode the value
                    response_data[key] = urllib.parse.unquote_plus(value)
            
            print(f"Parsed OTP response: {response_data}")
            return response_data
        else:
            raise Exception(f"OTP submission failed with status {response.status_code}: {response.text}")

class PaynowResponse:
    """Wrapper class for Paynow response data."""
    
    def __init__(self, paynow_response, method):
        """Initialize with Paynow response and payment method."""
        self.response = paynow_response
        self.method = method
        self.success = paynow_response.success
        self.data = paynow_response.data if hasattr(paynow_response, 'data') else {}
        
        # Extract OMari-specific data
        self.remoteotpurl = None
        self.otpreference = None
        self.redirect_url = None
        
        if method == 'omari' and self.data:
            self.remoteotpurl = self.data.get('remoteotpurl', '')
            self.otpreference = self.data.get('otpreference', '')
            
            # For Express Checkout, get redirect URL
            if hasattr(paynow_response, 'redirect_url') and paynow_response.redirect_url:
                self.redirect_url = str(paynow_response.redirect_url)
    
    def get_instructions(self):
        """Generate payment instructions based on method and response data."""
        instructions = ''
        
        # Check if there's actual instruction data in response
        if hasattr(self.response, 'data') and self.response.data:
            if isinstance(self.response.data, dict):
                instructions = self.response.data.get('instructions', '')
                if not instructions:
                    instructions = self.response.data.get('message', '')
        
        # If still no instructions, check redirect info
        if not instructions and hasattr(self.response, 'has_redirect') and self.response.has_redirect:
            if hasattr(self.response, 'redirect_url') and self.response.redirect_url:
                instructions = f"Please complete payment by visiting: {self.response.redirect_url}"
        
        # If still no instructions, provide method-specific default messages
        if not instructions:
            if self.method.lower() == 'ecocash':
                instructions = "Dial *151# on your EcoCash registered line and follow the prompts to complete payment."
            elif self.method.lower() == 'innbucks':
                instructions = "Check your phone for payment instructions."
            elif self.method.lower() == 'omari':
                if self.redirect_url:
                    instructions = f"Please visit the payment URL to complete your OMari payment: {self.redirect_url}"
                elif self.remoteotpurl:
                    instructions = f"Please visit the OTP URL to complete your OMari payment. OTP Reference: {self.otpreference}"
                else:
                    instructions = "Payment initiated via OMari. Please check your phone for payment instructions."
            else:
                instructions = f"Payment initiated via {self.method.upper()}. Please check your phone for payment instructions."
        
        # If there's a redirect URL, append it to instructions
        if hasattr(self.response, 'redirect_url') and self.response.redirect_url and str(self.response.redirect_url) != "<class 'str'>":
            redirect_url = str(self.response.redirect_url)
            if redirect_url and redirect_url != "<class 'str'>":
                instructions += f"\n\nAlternatively, complete payment at: {redirect_url}"
        
        return instructions
    
    def get_poll_url(self):
        """Get poll URL from response."""
        return str(self.response.poll_url) if self.response.poll_url else ''
    
    def get_paynow_reference(self):
        """Get Paynow reference from response."""
        return self.data.get('paynowreference', '') if self.data else ''
    
    def get_hash(self):
        """Get hash from response."""
        return self.data.get('hash', '') if self.data else ''
    
    def has_redirect(self):
        """Check if response has redirect."""
        return getattr(self.response, 'has_redirect', False)
