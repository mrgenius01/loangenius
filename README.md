# 💰 Loan Repayment App

A complete loan repayment system with React Native mobile app and Python Flask backend, integrated with Paynow payment gateway.

## 🚀 Features

### Mobile App (React Native + Expo)
- ✅ Beautiful login interface with mock authentication
- ✅ Professional dashboard for loan repayments
- ✅ Real-time payment processing
- ✅ Payment status tracking
- ✅ API connection testing
- ✅ Support for EcoCash and InnBucks

### Backend API (Python Flask)
- ✅ Paynow payment gateway integration
- ✅ RESTful API for payment processing
- ✅ Real-time payment status checking
- ✅ Transaction management
- ✅ CORS enabled for mobile app
- ✅ Environment-based configuration

## 📱 Demo Credentials
- **Username**: `admin`
- **Password**: `password123`

## 🛠️ Quick Start

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your Paynow credentials
python app.py
```

### Mobile App Setup
```bash
cd mobile
npm install
npx expo start
```

## 🌐 Deployment

### Backend (Render)
- Deploys automatically from `main` branch
- Environment variables configured in Render dashboard
- See `backend/README.md` for detailed deployment guide

### Mobile App (Expo)
- Build and publish with Expo CLI
- See `mobile/README.md` for deployment guide

## 📚 API Documentation

### Endpoints
- `GET /health` - Health check
- `POST /payment` - Create payment
- `GET /payment/status/<reference>` - Check payment status
- `POST /payment/test` - Test payment (no real processing)
- `GET /transactions` - List all transactions

### Payment Request
```json
{
  "phoneNumber": "0771234567",
  "amount": "50.00",
  "method": "ecocash"
}
```

### Payment Response
```json
{
  "status": "success",
  "reference": "LOAN_ABC123",
  "paynow_reference": "12345678",
  "poll_url": "https://...",
  "instructions": "Dial *151# to complete payment",
  "redirect_url": "https://...",
  "message": "Payment request sent successfully"
}
```

## 🔧 Environment Variables

### Backend
```env
PAYNOW_INTEGRATION_ID=your_integration_id
PAYNOW_INTEGRATION_KEY=your_integration_key
RETURN_URL=http://localhost:3000/payment/return
RESULT_URL=http://localhost:5000/paynow/result
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support, create an issue in this repository.

## Tools

- [Paynow Zimbabwe](https://paynow.co.zw) for payment processing
- [Expo](https://expo.dev) for React Native development
- [Render](https://render.com) for backend hosting
