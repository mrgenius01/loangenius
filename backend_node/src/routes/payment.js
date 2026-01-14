const express = require('express');
const router = express.Router();

router.get('/', (req, res) => {
  res.json({ message: 'Payment route works!' });
});

module.exports = router;
