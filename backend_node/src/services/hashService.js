// Add more service files as needed, e.g., authService, paymentService
// Example: Hashing service for passwords
const bcrypt = require('bcrypt');

async function hashPassword(password) {
  return await bcrypt.hash(password, 10);
}

async function comparePassword(password, hash) {
  return await bcrypt.compare(password, hash);
}

module.exports = { hashPassword, comparePassword };
