const express = require('express');
const router = express.Router();

const authRoutes = require('./auth');
const customerRoutes = require('./customer');
const dashboardRoutes = require('./dashboard');
const loanDashboardRoutes = require('./loanDashboard');
const paymentRoutes = require('./payment');
const transactionRoutes = require('./transaction');
const webhookRoutes = require('./webhook');

router.use('/auth', authRoutes);
router.use('/customer', customerRoutes);
router.use('/dashboard', dashboardRoutes);
router.use('/loan-dashboard', loanDashboardRoutes);
router.use('/payment', paymentRoutes);
router.use('/transaction', transactionRoutes);
router.use('/webhook', webhookRoutes);

module.exports = router;
