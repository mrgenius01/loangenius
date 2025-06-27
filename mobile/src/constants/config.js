/**
 * Application configuration constants
 */

// Mock login credentials for demo
export const MOCK_CREDENTIALS = {
  username: 'admin',
  password: 'password123'
};

// API Configuration
export const API_CONFIG = {
  // Production backend URL - deployed on Render
  PRODUCTION_URL: 'https://loangenius.onrender.com',
  // For local development
  DEVELOPMENT_URL: 'http://192.168.137.1:5000',
  // Current environment
  BASE_URL: 'http://192.168.137.1:5000', // Switch between PRODUCTION_URL and DEVELOPMENT_URL
  TIMEOUT: 5000
};

// Payment methods configuration
export const PAYMENT_METHODS = [
  { key: 'ecocash', label: 'EcoCash', color: '#10ac84' },
  { key: 'innbucks', label: 'InnBucks', color: '#3742fa' },
  { key: 'omari', label: 'OMari', color: '#3956fa' }
];

// OTP Configuration
export const OTP_CONFIG = {
  MAX_ATTEMPTS: 5,
  CODE_LENGTH: 6,
  AUTO_CHECK_INTERVAL: 5000 // 5 seconds
};
