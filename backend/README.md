# Loan Repayment Backend

Python Flask backend with Paynow integration for processing loan repayments via mobile money (EcoCash, InnBucks, etc.).

## Features

- ✅ **Paynow Integration** - Official Paynow Python SDK
- ✅ **Mobile Money Support** - EcoCash, InnBucks/OneMoney
- ✅ **Payment Status Tracking** - Real-time payment status checks
- ✅ **CORS Enabled** - Ready for React Native frontend
- ✅ **Transaction Management** - Store and retrieve payment history
- ✅ **Webhook Support** - Handle Paynow result callbacks

## Quick Start

### 1. Install Dependencies

```bash
# Option 1: Using setup script
python setup.py

# Option 2: Manual installation
pip install -r requirements.txt
```

### 2. Configure Paynow Credentials

1. Copy `.env.example` to `.env`
2. Get your credentials from [Paynow Dashboard](https://www.paynow.co.zw/)
3. Update `.env` with your integration ID and key:

```env
PAYNOW_INTEGRATION_ID=your_integration_id_here
PAYNOW_INTEGRATION_KEY=your_integration_key_here
```

### 3. Run the Server

```bash
python app.py
```

Server will start at: `http://localhost:5000`

## API Endpoints

### `POST /payment`
Create a new payment request

**Request Body:**
```json
{
  "phoneNumber": "0771234567",
  "amount": "10.00",
  "method": "ecocash"
}
```

**Response:**
```json
{
  "status": "success",
  "reference": "LOAN_A1B2C3D4",
  "poll_url": "https://paynow.co.zw/interface/poll/...",
  "instructions": "Send payment via EcoCash...",
  "message": "Payment request sent successfully"
}
```

### `GET /payment/status/<reference>`
Check payment status

**Response:**
```json
{
  "reference": "LOAN_A1B2C3D4",
  "status": "paid",
  "paid": true,
  "amount": 10.00,
  "method": "ecocash",
  "created_at": "2025-01-01T12:00:00"
}
```

### `GET /health`
Health check endpoint

### `GET /transactions`
Get all transactions (for debugging)

## Payment Methods Supported

- **EcoCash** - `"ecocash"`
- **InnBucks/OneMoney** - `"innbucks"`

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PAYNOW_INTEGRATION_ID` | Your Paynow integration ID | Required |
| `PAYNOW_INTEGRATION_KEY` | Your Paynow integration key | Required |
| `RETURN_URL` | URL to redirect after payment | `http://localhost:3000/payment/return` |
| `RESULT_URL` | Webhook URL for payment results | `http://localhost:5000/paynow/result` |

## Testing

You can test the API using curl:

```bash
# Create payment
curl -X POST http://localhost:5000/payment \
  -H "Content-Type: application/json" \
  -d '{
    "phoneNumber": "0771234567",
    "amount": "5.00",
    "method": "ecocash"
  }'

# Check status
curl http://localhost:5000/payment/status/LOAN_A1B2C3D4
```

## Production Considerations

- Replace in-memory storage with a proper database (PostgreSQL, MySQL, etc.)
- Add proper logging and monitoring
- Implement rate limiting
- Add input validation and sanitization
- Use environment-specific configuration
- Set up proper error handling and alerting

## Documentation

- [Paynow Developer Documentation](https://developers.paynow.co.zw/)
- [Python SDK Documentation](https://developers.paynow.co.zw/docs/python_quickstart.html)
