# Loan Management API Documentation

## Base URL
```
http://localhost:3000/api
```

---

## Endpoints

### 1. Health Check
**GET** `/health`

**Response:**
```
{
  "status": "ok",
  "timestamp": "2026-01-14T12:38:55.006Z"
}
```

---


# Loan Management API Documentation

## Base URL
```
http://localhost:3000/api
```

---

## Endpoints

### 1. Health Check
**GET** `/health`

**Response:**
```
{
  "status": "ok",
  "timestamp": "2026-01-14T12:38:55.006Z"
}
```

---

### 2. Register User
**POST** `/auth/register`

**Request Body:**
```
{
  "username": "testuser",
  "password": "testpass123",
  "email": "testuser@example.com"
}
```

**Response:**
```
{
  "user": { ... }
}
```

---

### 3. Login User
**POST** `/auth/login`

**Request Body:**
```
{
  "username": "testuser",
  "password": "testpass123"
}
```

**Response:**
```
{
  "user": { ... }
}
```

---

### 4. Create Transaction & Initiate Paynow Payment
**POST** `/transaction`

**Request Body:**
```
{
  "amount": 10.00,
  "type": "loan_payment",
  "userId": 1,
  "phone_number": "0771234567",
  "method": "ecocash", // or "onemoney", "innbucks", "omari"
  "email": "user@example.com" // optional
}
```

**Response:**
```
{
  "transaction": { ... },
  "paynow": {
    "success": true,
    "instructions": "...",
    "pollUrl": "...",
    // other Paynow response fields
  }
}
```

---

### 5. Poll Paynow Transaction Status
**GET** `/transaction/status?pollUrl=...`

**Response:**
```
{
  "status": {
    "paid": true,
    "amount": 10.00,
    // other status fields
  }
}
```

---

### 6. Submit OTP for Multistage Payments
**POST** `/transaction/otp`

**Request Body:**
```
{
  "otp": "123456",
  "otpUrl": "..."
}
```

**Response:**
```
{
  "otpResponse": { ... }
}
```

---

### 7. Get Transaction by ID
**GET** `/transaction/:id`

**Response:**
```
{
  "transaction": { ... }
}
```

---

## Multistage Payments (OTP/Express Checkout)

Some payment methods (e.g. OMARI, Innbucks) require additional steps such as OTP submission or status polling.

### Flow:
1. **Initiate Payment** using `POST /transaction`.
2. **Check Response:**
   - If `paynow.success` is `true`, follow `instructions` and save `pollUrl`.
   - If OTP is required, Paynow will provide instructions and/or an OTP URL.
3. **Submit OTP (if required):**
   - Use `POST /transaction/otp` with the OTP and OTP URL from Paynow.
4. **Poll Transaction Status:**
   - Use `GET /transaction/status?pollUrl=...` to check if payment is complete.

---

## Error Handling
- All endpoints return errors in the format:
```
{
  "error": "Error message"
}
```

---

## Example Flow Testing

### Ecocash/OneMoney
1. **POST /transaction** with method `ecocash` or `onemoney`.
2. **Follow instructions** in response.
3. **Save pollUrl** and poll status until paid.

### OMARI/Innbucks (Multistage)
1. **POST /transaction** with method `omari` or `innbucks`.
2. **If OTP required, get instructions and otpUrl from response.**
3. **POST /transaction/otp** with OTP and otpUrl.
4. **GET /transaction/status?pollUrl=...** to check payment status.

---

## Notes
- Always save `pollUrl` from Paynow responses for status checks.
- For Ecocash/OneMoney, use `method: "ecocash"` or `"onemoney"`.
- For OMARI/Innbucks, follow instructions and handle OTP if required.
- See [Paynow Node.js Quickstart](https://developers.paynow.co.zw/docs/nodejs_quickstart.html) for more details.

---

## Contact & Support
- For integration issues, contact Paynow support or refer to their [developer documentation](https://developers.paynow.co.zw/docs/quickstart.html).
