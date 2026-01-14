const express = require('express');
const router = express.Router();
const Transaction = require('../models/transaction');
const { pollPaynowTransaction } = require('../services/paynowService');

// Paynow server-to-server callback for payment result
router.post('/result', async (req, res) => {
  try {
    // Paynow sends data as form-urlencoded
    const { reference, pollurl, status } = req.body;
    if (!reference && !pollurl) {
      return res.status(400).json({ error: 'Missing reference or pollurl' });
    }

    // Find transaction by reference or pollUrl
    let transaction = null;
    if (reference) {
      transaction = await Transaction.findOne({ where: { reference } });
    }
    if (!transaction && pollurl) {
      transaction = await Transaction.findOne({ where: { pollUrl: pollurl } });
    }
    if (!transaction) {
      return res.status(404).json({ error: 'Transaction not found' });
    }

    // Poll Paynow for latest status (recommended)
    let paynowStatus = null;
    if (transaction.pollUrl) {
      paynowStatus = await pollPaynowTransaction(transaction.pollUrl);
    }

    // Update transaction status and error fields
    transaction.status = (paynowStatus && paynowStatus.status) || status || transaction.status;
    if (paynowStatus && paynowStatus.error) {
      transaction.error = paynowStatus.error;
    }
    await transaction.save();

    // Respond to Paynow
    res.status(200).send('OK');
  } catch (err) {
    console.error('[Paynow Result Webhook] Error:', err);
    res.status(500).json({ error: 'Internal server error' });
  }
});

module.exports = router;
