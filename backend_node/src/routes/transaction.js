const Loan = require('../models/loan');
const express = require('express');
const router = express.Router();
const Joi = require('joi');
// POST /api/loan (create a new loan)
router.post('/loan', async (req, res, next) => {
  try {
    const schema = Joi.object({
      userId: Joi.number().integer().required(),
      amount: Joi.number().greater(0).required(),
      status: Joi.string().default('active')
    });
    const { error, value } = schema.validate(req.body);
    if (error) {
      return res.status(400).json({ error: error.details[0].message });
    }
    const loan = await Loan.create({
      userId: value.userId,
      amount: value.amount,
      status: value.status
    });
    console.log('[Loan] Created:', loan.toJSON ? loan.toJSON() : loan);
    res.status(201).json({ loan });
  } catch (err) {
    next(err);
  }
});

const Transaction = require('../models/transaction');
const { payNowMobile, pollPaynowTransaction, submitPaynowOtp } = require('../services/paynowService');
// POST /api/transaction/otp (submit OTP for multistage Paynow payments)
router.post('/otp', async (req, res, next) => {
  try {
    const schema = Joi.object({
      otp: Joi.string().required(),
      otpUrl: Joi.string().uri().required()
    });
    const { error, value } = schema.validate(req.body);
    if (error) {
      return res.status(400).json({ error: error.details[0].message });
    }
    const otpResponse = await submitPaynowOtp({ otp: value.otp, otpUrl: value.otpUrl });
    res.json({ otpResponse });
  } catch (err) {
    next(err);
  }
});

// POST /api/transaction
// POST /api/transaction (create and initiate Paynow mobile payment)
router.post('/', async (req, res, next) => {
  try {
    const schema = Joi.object({
      amount: Joi.number().greater(1).required(),
      type: Joi.string().required(),
      userId: Joi.number().integer().required(),
      phone_number: Joi.string().required(),
      method: Joi.string().required(),
      email: Joi.string().email().optional()
    });
    const { error, value } = schema.validate(req.body);
    if (error) {
      return res.status(400).json({ error: error.details[0].message });
    }



    // Call PayNow API (mobile)
    const paynowResponse = await payNowMobile({
      reference: `txn_${Date.now()}`,
      amount: value.amount,
      phone_number: value.phone_number,
      method: value.method,
      email: value.email
    });

    // Build transaction data with Paynow details
    const transactionData = {
      amount: value.amount,
      type: value.type,
      userId: value.userId,
      phone_number: value.phone_number,
      method: value.method,
      status: paynowResponse.status || (paynowResponse.success === false ? 'failed' : 'pending'),
      reference: paynowResponse.reference || `txn_${Date.now()}`,
      pollUrl: paynowResponse.pollUrl || null,
      instructions: paynowResponse.instructions || null,
      error: paynowResponse.error || null
    };
    const transaction = await Transaction.create(transactionData);
    console.log('[Transaction] Created:', transaction.toJSON ? transaction.toJSON() : transaction);
    console.log('[Paynow] Integration ID:', paynowResponse.reference);

    // Graceful error handling for Paynow
    if (paynowResponse && paynowResponse.success === false) {
      let userMessage = paynowResponse.error || 'Payment failed.';
      if (paynowResponse.error && paynowResponse.error.toLowerCase().includes('no customer found')) {
        userMessage = 'No OMARI customer found for this phone number.';
      } else if (paynowResponse.error && paynowResponse.error.toLowerCase().includes('user not exist')) {
        userMessage = 'No OneMoney customer found for this phone number.';
      }
      return res.status(400).json({
        transaction,
        paynow: paynowResponse,
        error: userMessage
      });
    }
    res.status(201).json({
      transactionId: transaction.id,
      status: transaction.status,
      reference: transaction.reference,
      pollUrl: transaction.pollUrl,
      instructions: transaction.instructions,
      error: transaction.error,
      paynow: paynowResponse
    });
  } catch (err) {
    next(err);
  }
});

// GET /api/transaction/status?pollUrl=...
router.get('/status', async (req, res, next) => {
  try {
    const { pollUrl } = req.query;
    if (!pollUrl) {
      return res.status(400).json({ error: 'pollUrl is required' });
    }
    const status = await pollPaynowTransaction(pollUrl);
    res.json({ status });
  } catch (err) {
    next(err);
  }
});

// GET /api/transaction/:id
router.get('/:id', async (req, res, next) => {
  try {
    const transaction = await Transaction.findByPk(req.params.id);
    if (!transaction) {
      return res.status(404).json({ error: 'Transaction not found' });
    }
    res.json({ transaction });
  } catch (err) {
    next(err);
  }
});

module.exports = router;
