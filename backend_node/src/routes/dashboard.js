// Add more route files as needed for dashboard, payment, webhook, etc.
const express = require('express');
const router = express.Router();

router.get('/', (req, res) => {
  res.json({ message: 'Dashboard route works!' });
});

module.exports = router;
