/**
 * API service for handling backend communication
 */
import axios from 'axios';
import { API_CONFIG } from '../constants/config';

class ApiService {
  constructor() {
    this.baseURL = API_CONFIG.BASE_URL;
    this.timeout = API_CONFIG.TIMEOUT;
    
    // Create axios instance with default config
    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: this.timeout,
      headers: {
        'Content-Type': 'application/json'
      }
    });
  }

  /**
   * Test API connectivity
   */
  async testConnection() {
    try {
      const response = await this.client.get('/health');
      return { success: true, data: response.data };
    } catch (error) {
      return { 
        success: false, 
        error: error.message,
        details: `Cannot connect to backend at ${this.baseURL}`
      };
    }
  }

  /**
   * Create a payment
   */
  async createPayment(phoneNumber, amount, method) {
    try {
      const response = await this.client.post('/payment', {
        phoneNumber,
        amount,
        method
      });
      return { success: true, data: response.data };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.message || error.message,
        details: error.response?.data
      };
    }
  }

  /**
   * Check payment status
   */
  async checkPaymentStatus(reference) {
    try {
      const response = await this.client.get(`/payment/status/${reference}`);
      return { success: true, data: response.data };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.message || error.message
      };
    }
  }

  /**
   * Request OTP for OMari payment
   */
  async requestOtp(reference) {
    try {
      const response = await this.client.post('/payment/otp/request', {
        reference
      });
      return { success: true, data: response.data };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.error || error.response?.data?.message || error.message
      };
    }
  }

  /**
   * Submit OTP for OMari payment
   */
  async submitOtp(reference, otp) {
    try {
      const response = await this.client.post('/payment/otp', {
        reference,
        otp
      });
      return { success: true, data: response.data };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.error || error.response?.data?.message || error.message
      };
    }
  }
}

// Export singleton instance
export default new ApiService();
