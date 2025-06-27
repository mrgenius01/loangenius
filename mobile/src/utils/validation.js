/**
 * Validation utility functions
 */

/**
 * Validate phone number format
 * @param {string} phoneNumber - Phone number to validate
 * @returns {boolean} - True if valid
 */
export const validatePhoneNumber = (phoneNumber) => {
  if (!phoneNumber) return false;
  
  // Remove spaces and special characters
  const cleaned = phoneNumber.replace(/[\s\-\(\)]/g, '');
  
  // Check if it's a valid Zimbabwean phone number format
  const phoneRegex = /^(0|\+263)[0-9]{9}$/;
  return phoneRegex.test(cleaned);
};

/**
 * Validate amount
 * @param {string} amount - Amount to validate
 * @returns {boolean} - True if valid
 */
export const validateAmount = (amount) => {
  if (!amount) return false;
  
  const numAmount = parseFloat(amount);
  return !isNaN(numAmount) && numAmount > 0;
};

/**
 * Format amount to 2 decimal places
 * @param {string|number} amount - Amount to format
 * @returns {string} - Formatted amount
 */
export const formatAmount = (amount) => {
  const numAmount = parseFloat(amount);
  if (isNaN(numAmount)) return '0.00';
  return numAmount.toFixed(2);
};

/**
 * Format phone number for display
 * @param {string} phoneNumber - Phone number to format
 * @returns {string} - Formatted phone number
 */
export const formatPhoneNumber = (phoneNumber) => {
  if (!phoneNumber) return '';
  
  // Remove all non-digit characters
  const digits = phoneNumber.replace(/\D/g, '');
  
  // Format as Zimbabwe number
  if (digits.length >= 10) {
    return `${digits.slice(0, 3)} ${digits.slice(3, 6)} ${digits.slice(6)}`;
  }
  
  return phoneNumber;
};

/**
 * Generate a safe display name for sensitive data
 * @param {string} text - Text to mask
 * @param {number} visibleChars - Number of characters to show at start and end
 * @returns {string} - Masked text
 */
export const maskSensitiveData = (text, visibleChars = 3) => {
  if (!text || text.length <= visibleChars * 2) return text;
  
  const start = text.slice(0, visibleChars);
  const end = text.slice(-visibleChars);
  const middle = '*'.repeat(text.length - visibleChars * 2);
  
  return `${start}${middle}${end}`;
};
