// Example payment service (stub)
async function processPayment(paymentData) {
  // Integrate with payment gateway
  // For now, just log
  console.log('Processing payment:', paymentData);
  return { status: 'success' };
}

module.exports = { processPayment };
