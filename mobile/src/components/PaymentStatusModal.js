/**
 * Payment Status Modal Component
 * Displays payment status with auto-refresh functionality
 */
import React, { useState, useEffect } from 'react';
import { View, Text, TouchableOpacity, ActivityIndicator } from 'react-native';
import CustomModal from './CustomModal';
import ApiService from '../services/apiService';
import { OTP_CONFIG } from '../constants/config';
import { modalStyles } from '../styles/modalStyles';

const PaymentStatusModal = ({ visible, onClose, transaction, onStatusCheck }) => {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [autoCheck, setAutoCheck] = useState(true);
  const [checkCount, setCheckCount] = useState(0);
  const [timeoutReached, setTimeoutReached] = useState(false);
  const MAX_CHECKS = 5;

  useEffect(() => {
    if (visible && transaction && autoCheck && !timeoutReached) {
      checkStatus();
      const interval = setInterval(() => {
        setCheckCount(prev => {
          const newCount = prev + 1;
          if (newCount >= MAX_CHECKS) {
            setAutoCheck(false);
            setTimeoutReached(true);
            return newCount;
          }
          checkStatus();
          return newCount;
        });
      }, OTP_CONFIG.AUTO_CHECK_INTERVAL);
      return () => clearInterval(interval);
    }
  }, [visible, transaction, autoCheck, timeoutReached]);

  const checkStatus = async () => {
    if (!transaction?.reference) return;

    setLoading(true);
    try {
      const response = await ApiService.checkPaymentStatus(transaction.reference);
      if (response.success) {
        setStatus(response.data);
        
        // Stop auto-checking if payment is completed or failed
        if (response.data.status === 'paid' || response.data.status === 'cancelled') {
          setAutoCheck(false);
        }
      }
    } catch (error) {
      console.error('Status check error:', error);
    } finally {
      setLoading(false);
    }
  };  const getStatusDisplay = () => {
    if (!status?.status) return { text: 'CHECKING...', color: '#6b7280', icon: '⏳' };
    switch (status.status) {
      case 'paid': return { text: 'PAID', color: '#059669', icon: '✓' };
      case 'pending': return { text: 'PENDING', color: '#d97706', icon: '⏳' };
      case 'cancelled': return { text: 'CANCELLED', color: '#dc2626', icon: '✗' };
      default: return { text: 'UNKNOWN', color: '#6b7280', icon: '?' };
    }
  };

  const getModalType = () => {
    return 'info'; // Always use neutral info type for clean look
  };
  return (
    <CustomModal 
      visible={visible} 
      onClose={onClose} 
      title="Payment Status" 
      type={getModalType()}
    >
      {transaction ? (
        <View style={modalStyles.compactStatusContainer}>
          {/* Simplified status display */}
          <View style={modalStyles.compactStatusHeader}>
            <Text style={modalStyles.compactStatusText}>
              {getStatusDisplay().text}
            </Text>
          </View>

          {/* Essential transaction details only */}
          <View style={modalStyles.compactStatusDetails}>
            <View style={modalStyles.compactStatusRow}>
              <Text style={modalStyles.compactLabel}>Reference:</Text>
              <Text style={modalStyles.compactValue}>{transaction.reference || 'N/A'}</Text>
            </View>

            <View style={modalStyles.compactStatusRow}>
              <Text style={modalStyles.compactLabel}>Amount:</Text>
              <Text style={modalStyles.compactValue}>${transaction.amount || '0.00'}</Text>
            </View>
          </View>

          {/* Auto-check indicator - minimal */}
          {autoCheck && !timeoutReached && (
            <View style={modalStyles.compactIndicator}>
              <Text style={modalStyles.compactIndicatorText}>
                Auto-checking... ({checkCount + 1}/{MAX_CHECKS})
              </Text>
            </View>
          )}

          {/* Timeout message */}
          {timeoutReached && (
            <View style={modalStyles.compactTimeoutMessage}>
              <Text style={modalStyles.compactTimeoutText}>
                Auto-check complete. Tap "Check Now" to refresh status.
              </Text>
            </View>
          )}

          {/* Single action button */}
          <TouchableOpacity
            style={modalStyles.compactActionButton}
            onPress={checkStatus}
            disabled={loading}
          >
            <Text style={modalStyles.compactActionText}>
              {loading ? 'Checking...' : 'Check Now'}
            </Text>
          </TouchableOpacity>
        </View>
      ) : (
        <View style={modalStyles.compactStatusContainer}>
          <Text style={modalStyles.modalText}>No transaction data available</Text>
        </View>
      )}
    </CustomModal>
  );
};

export default PaymentStatusModal;
