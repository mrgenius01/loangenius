const express = require('express');
const router = express.Router();
const Joi = require('joi');
const User = require('../models/user');

// POST /api/auth/register
router.post('/register', async (req, res, next) => {
  try {
    const schema = Joi.object({
      username: Joi.string().required(),
      password: Joi.string().min(6).required(),
      email: Joi.string().email().required()
    });
    const { error, value } = schema.validate(req.body);
    if (error) {
      return res.status(400).json({ error: error.details[0].message });
    }
    const user = await User.create(value);
    res.status(201).json({ user });
  } catch (err) {
    if (err.name === 'SequelizeUniqueConstraintError') {
      return res.status(409).json({ error: 'User already exists' });
    }
    next(err);
  }
});

// POST /api/auth/login
router.post('/login', async (req, res, next) => {
  try {
    const schema = Joi.object({
      username: Joi.string().required(),
      password: Joi.string().required()
    });
    const { error, value } = schema.validate(req.body);
    if (error) {
      return res.status(400).json({ error: error.details[0].message });
    }
    const user = await User.findOne({ where: { username: value.username } });
    if (!user) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }
    // TODO: Add password hash check
    res.json({ user });
  } catch (err) {
    next(err);
  }
});

module.exports = router;
