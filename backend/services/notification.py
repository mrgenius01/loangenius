import requests

class SMSNotification:
    def __init__(self, sms_api_url, api_key, sender_id):
        self.sms_api_url = sms_api_url
        self.api_key = api_key
        self.sender_id = sender_id

    def send_payment_notification(self, phone_number, amount, transaction_id):
        message = (
            f"Payment of {amount} has been received for your automated tollgate billing. "
            f"Transaction ID: {transaction_id}. Thank you for using our service."
        )
        print("--- Simulated SMS Notification ---")
        print(f"To: {phone_number}")
        print(f"Message: {message}")
        print(f"Sender: {self.sender_id}")
        print(f"API Key: {self.api_key}")
        print(f"API URL: {self.sms_api_url}")
        print("--- End of Simulation ---")
        return {
            "status": "success",
            "to": phone_number,
            "message": message,
            "transaction_id": transaction_id
        }
    

smsModule = SMSNotification(
    sms_api_url="https://api.smsprovider.com/send",
    api_key="xbbdfhhfjdj-pwh666r",
    sender_id="ANRP"
)

smsModule.send_payment_notification(
    phone_number="+263785301077",
    amount=100.0,
    transaction_id="txn_123456"
)
