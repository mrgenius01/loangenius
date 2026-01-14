const express = require('express');
const router = express.Router();

router.post('/', (req, res) => {
  res.json({ message: 'Webhook received!' });
});

module.exports = router;
