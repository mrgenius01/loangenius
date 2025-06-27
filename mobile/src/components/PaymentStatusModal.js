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

  useEffect(() => {
    if (visible && transaction && autoCheck) {
      checkStatus();
      const interval = setInterval(checkStatus, OTP_CONFIG.AUTO_CHECK_INTERVAL);
      return () => clearInterval(interval);
    }
  }, [visible, transaction, autoCheck]);

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
  };

  const getStatusColor = () => {
    if (!status?.status) return '#6b7280';
    switch (status.status) {
      case 'paid': return '#10b981';
      case 'pending': return '#f59e0b';
      case 'cancelled': return '#ef4444';
      default: return '#6b7280';
    }
  };

  const getStatusIcon = () => {
    if (!status?.status) return '⏳';
    switch (status.status) {
      case 'paid': return '✅';
      case 'pending': return '⏳';
      case 'cancelled': return '❌';
      default: return '❓';
    }
  };

  const getModalType = () => {
    if (!status?.status) return 'info';
    return status.status === 'paid' ? 'success' : status.status === 'cancelled' ? 'error' : 'info';
  };

  return (
    <CustomModal 
      visible={visible} 
      onClose={onClose} 
      title="Payment Status" 
      type={getModalType()}
    >
      {transaction ? (
        <View style={modalStyles.statusContainer}>
          <View style={modalStyles.statusHeader}>
            <Text style={[modalStyles.statusIcon, { color: getStatusColor() }]}>
              {getStatusIcon()}
            </Text>
            <Text style={[modalStyles.statusText, { color: getStatusColor() }]}>
              {(status?.status) ? status.status.toUpperCase() : 'CHECKING...'}
            </Text>
          </View>

          <View style={modalStyles.statusDetails}>
            <View style={modalStyles.statusRow}>
              <Text style={modalStyles.statusLabel}>Reference:</Text>
              <Text style={modalStyles.statusValue}>{transaction.reference || 'N/A'}</Text>
            </View>

            {transaction.paynow_reference && (
              <View style={modalStyles.statusRow}>
                <Text style={modalStyles.statusLabel}>Paynow Reference:</Text>
                <Text style={modalStyles.statusValue}>{transaction.paynow_reference}</Text>
              </View>
            )}

            <View style={modalStyles.statusRow}>
              <Text style={modalStyles.statusLabel}>Amount:</Text>
              <Text style={modalStyles.statusValue}>${transaction.amount || '0.00'}</Text>
            </View>

            {status && (
              <>
                <View style={modalStyles.statusRow}>
                  <Text style={modalStyles.statusLabel}>Status:</Text>
                  <Text style={[modalStyles.statusValue, { color: getStatusColor(), fontWeight: 'bold' }]}>
                    {(status?.status) ? status.status.toUpperCase() : 'UNKNOWN'}
                  </Text>
                </View>

                <View style={modalStyles.statusRow}>
                  <Text style={modalStyles.statusLabel}>Paid:</Text>
                  <Text style={[modalStyles.statusValue, { color: (status?.paid) ? '#10b981' : '#ef4444', fontWeight: 'bold' }]}>
                    {(status?.paid) ? 'YES' : 'NO'}
                  </Text>
                </View>
              </>
            )}
          </View>

          {transaction.instructions && (
            <View style={modalStyles.instructionsContainer}>
              <Text style={modalStyles.instructionsTitle}>Instructions:</Text>
              <Text style={modalStyles.instructionsText}>{transaction.instructions}</Text>
            </View>
          )}

          <View style={modalStyles.statusActions}>
            <TouchableOpacity
              style={[modalStyles.statusButton, { backgroundColor: '#3b82f6' }]}
              onPress={checkStatus}
              disabled={loading}
            >
              {loading ? (
                <ActivityIndicator size="small" color="#ffffff" />
              ) : (
                <Text style={modalStyles.statusButtonText}>Refresh Status</Text>
              )}
            </TouchableOpacity>
            
            <TouchableOpacity
              style={[modalStyles.statusButton, { backgroundColor: autoCheck ? '#ef4444' : '#10b981' }]}
              onPress={() => setAutoCheck(!autoCheck)}
            >
              <Text style={modalStyles.statusButtonText}>
                {autoCheck ? 'Stop Auto-Check' : 'Start Auto-Check'}
              </Text>
            </TouchableOpacity>
          </View>

          {autoCheck && (
            <View style={modalStyles.autoCheckIndicator}>
              <ActivityIndicator size="small" color="#3b82f6" />
              <Text style={modalStyles.autoCheckText}>Auto-checking every 5 seconds...</Text>
            </View>
          )}
        </View>
      ) : (
        <View style={modalStyles.statusContainer}>
          <Text style={modalStyles.modalText}>No transaction data available</Text>
        </View>
      )}
    </CustomModal>
  );
};

export default PaymentStatusModal;
