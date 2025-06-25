# Deployment Guide

## 🚀 Backend Deployment (Render)

### Prerequisites
- Render account (free tier available)
- Paynow merchant account with API credentials

### Steps

1. **Push code to GitHub**
   ```bash
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **Create Render Web Service**
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New" → "Web Service"
   - Connect your GitHub repository
   - Configure:
     - **Name**: `loan-repayment-backend`
     - **Environment**: `Python 3`
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `python app.py`
     - **Root Directory**: `backend`

3. **Environment Variables**
   Add these in Render dashboard:
   ```
   PAYNOW_INTEGRATION_ID=your_actual_integration_id
   PAYNOW_INTEGRATION_KEY=your_actual_integration_key
   RETURN_URL=https://your-frontend-url.com/payment/return
   RESULT_URL=https://your-backend-url.onrender.com/paynow/result
   ```

4. **Deploy**
   - Render will automatically deploy on every push to main branch
   - Your API will be available at: `https://loan-repayment-backend.onrender.com`

### Free Tier Limitations
- Service spins down after 15 minutes of inactivity
- First request after downtime may take 30+ seconds
- 750 hours/month free

## 📱 Mobile App Deployment (Expo)

### Development Build
```bash
cd mobile
npx expo start
```

### Production Build
```bash
# Update API_BASE_URL in App.js to your Render URL
# Build for stores
npx expo build:android
npx expo build:ios
```

### Expo Publish
```bash
npx expo publish
```

## 🔄 CI/CD Pipeline (Optional)

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Render

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Deploy to Render
      run: echo "Render auto-deploys on git push"
```

## 🛡️ Security Considerations

### Production Checklist
- [ ] Use environment variables for all secrets
- [ ] Enable HTTPS (automatic on Render)
- [ ] Set up proper CORS origins
- [ ] Implement rate limiting
- [ ] Add request validation
- [ ] Set up monitoring and logging
- [ ] Use a proper database (PostgreSQL/MongoDB)
- [ ] Implement user authentication
- [ ] Add input sanitization

### Paynow Security
- [ ] Verify webhook signatures
- [ ] Use HTTPS for all callbacks
- [ ] Validate payment amounts
- [ ] Log all transactions
- [ ] Implement fraud detection
