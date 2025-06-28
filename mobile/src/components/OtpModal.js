/**
 * OMari OTP Modal Component
 * Handles OTP request and submission for OMari payments
 */
import React, { useState, useEffect } from 'react';
import { View, Text, TouchableOpacity, TextInput, ActivityIndicator, Alert } from 'react-native';
import CustomModal from './CustomModal';
import ApiService from '../services/apiService';
import { OTP_CONFIG } from '../constants/config';
import { modalStyles } from '../styles/modalStyles';

const OtpModal = ({ visible, onClose, transaction, onOtpSuccess }) => {
  const [otpCode, setOtpCode] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [otpError, setOtpError] = useState('');
  const [attempts, setAttempts] = useState(0);
  const [otpSent, setOtpSent] = useState(false);
  const [sendingOtp, setSendingOtp] = useState(false);
  useEffect(() => {
    if (visible && transaction) {
      // Reset state when modal opens
      resetState();
      // Automatically send OTP for OMari payments
      if (transaction.method === 'omari') {
        sendOtp();
      }
    }
  }, [visible, transaction]);

  const resetState = () => {
    setOtpCode('');
    setOtpError('');
    setAttempts(0);
    setSubmitting(false);
    setOtpSent(false);
    setSendingOtp(false);
  };

  const sendOtp = async () => {
    if (!transaction?.reference) {
      setOtpError('Transaction reference not found');
      return;
    }

    setSendingOtp(true);
    setOtpError('');

    try {
      const response = await ApiService.requestOtp(transaction.reference);      if (response.success) {
        setOtpSent(true);
        // Don't show alert - just set the state
      } else {
        setOtpError(response.error || 'Failed to send OTP');
        // Still allow OTP input in case user wants to try manual entry
        setOtpSent(true);
      }
    } catch (error) {
      setOtpError('Failed to send OTP');
      console.error('OTP request error:', error);
    } finally {
      setSendingOtp(false);
    }
  };

  const submitOtp = async () => {
    if (!otpCode || otpCode.length !== OTP_CONFIG.CODE_LENGTH) {
      setOtpError(`Please enter a valid ${OTP_CONFIG.CODE_LENGTH}-digit OTP`);
      return;
    }

    setSubmitting(true);
    setOtpError('');

    try {
      const response = await ApiService.submitOtp(transaction.reference, otpCode);

      if (response.success) {
        Alert.alert(
          'OTP Submitted Successfully!',
          `Payment Status: ${response.data.payment_status}\n\nYour payment is being processed.`,
          [
            {
              text: 'Check Status',
              onPress: () => {
                onClose();
                if (onOtpSuccess) {
                  onOtpSuccess();
                }
              }
            }
          ]
        );
        return;
      } else {
        throw new Error(response.error);
      }
    } catch (error) {
      const newAttempts = attempts + 1;
      setAttempts(newAttempts);
      
      const errorMessage = error.message || 'Failed to submit OTP';
      
      if (newAttempts >= OTP_CONFIG.MAX_ATTEMPTS) {
        setOtpError(`Maximum attempts reached (${OTP_CONFIG.MAX_ATTEMPTS}). Transaction cancelled. Please start a new payment.`);
      } else {
        const remainingAttempts = OTP_CONFIG.MAX_ATTEMPTS - newAttempts;
        setOtpError(`${errorMessage}. ${remainingAttempts} attempts remaining.`);
      }
    } finally {
      setSubmitting(false);
    }
  };

  const renderTransactionDetails = () => (
    <View style={modalStyles.otpDetails}>
      <View style={modalStyles.statusRow}>
        <Text style={modalStyles.statusLabel}>Reference:</Text>
        <Text style={modalStyles.statusValue}>{transaction?.reference || 'N/A'}</Text>
      </View>
      <View style={modalStyles.statusRow}>
        <Text style={modalStyles.statusLabel}>Amount:</Text>
        <Text style={modalStyles.statusValue}>${transaction?.amount || '0.00'}</Text>
      </View>
      <View style={modalStyles.statusRow}>
        <Text style={modalStyles.statusLabel}>Phone:</Text>
        <Text style={modalStyles.statusValue}>{transaction?.phone_number || 'N/A'}</Text>
      </View>
    </View>
  );
  const renderInstructions = () => (
    <View style={modalStyles.otpInstructions}>
      <Text style={modalStyles.instructionsTitle}>
        Enter OTP to Complete Payment
      </Text>
      <Text style={modalStyles.instructionsText}>
        {!otpSent 
          ? 'Sending OTP to your phone number...'
          : 'Enter the 6-digit OTP sent to your phone to complete the payment.'
        }
      </Text>
    </View>
  );

  const renderOtpInput = () => (
    <View style={modalStyles.otpInputSection}>
      <View style={modalStyles.otpInputContainer}>
        <TextInput
          style={modalStyles.otpInput}
          value={otpCode}
          onChangeText={setOtpCode}
          placeholder={`Enter ${OTP_CONFIG.CODE_LENGTH}-digit OTP`}
          keyboardType="numeric"
          maxLength={OTP_CONFIG.CODE_LENGTH}
          editable={!submitting && attempts < OTP_CONFIG.MAX_ATTEMPTS}
        />
      </View>
      
      {otpError ? (
        <Text style={modalStyles.otpErrorText}>{otpError}</Text>
      ) : null}

      <View style={modalStyles.otpButtonContainer}>
        <TouchableOpacity
          style={[modalStyles.statusButton, { 
            backgroundColor: submitting || attempts >= OTP_CONFIG.MAX_ATTEMPTS ? '#95a5a6' : '#10b981',
            marginRight: 10,
            flex: 1
          }]}
          onPress={submitOtp}
          disabled={submitting || attempts >= OTP_CONFIG.MAX_ATTEMPTS}
        >
          {submitting ? (
            <ActivityIndicator color="white" size="small" />
          ) : (
            <Text style={modalStyles.statusButtonText}>Submit OTP</Text>
          )}
        </TouchableOpacity>

        <TouchableOpacity
          style={[modalStyles.statusButton, { 
            backgroundColor: sendingOtp ? '#95a5a6' : '#3498db',
            flex: 1
          }]}
          onPress={sendOtp}
          disabled={sendingOtp}
        >
          {sendingOtp ? (
            <ActivityIndicator color="white" size="small" />
          ) : (
            <Text style={modalStyles.statusButtonText}>Resend OTP</Text>
          )}
        </TouchableOpacity>
      </View>
    </View>
  );

  const renderSendOtpButton = () => (
    <TouchableOpacity
      style={[modalStyles.statusButton, { backgroundColor: sendingOtp ? '#95a5a6' : '#e74c3c' }]}
      onPress={sendOtp}
      disabled={sendingOtp}
    >
      {sendingOtp ? (
        <ActivityIndicator color="white" size="small" />
      ) : (
        <Text style={modalStyles.statusButtonText}>Send OTP</Text>
      )}
    </TouchableOpacity>
  );

  return (
    <CustomModal visible={visible} onClose={onClose} title="OMari Payment" type="info">
      {transaction ? (
        <View style={modalStyles.otpContainer}>
          <View style={modalStyles.otpHeader}>
            <Text style={modalStyles.otpIcon}>💳</Text>
            <Text style={modalStyles.otpTitle}>Complete OMari Payment</Text>
          </View>

          {renderTransactionDetails()}
          {renderInstructions()}          <View style={modalStyles.otpActions}>
            {/* Always show OTP input - simplified flow */}
            {renderOtpInput()}
          </View>

          {attempts > 0 && attempts < OTP_CONFIG.MAX_ATTEMPTS && (
            <View style={modalStyles.attemptsContainer}>
              <Text style={modalStyles.attemptsText}>
                Attempts: {attempts}/{OTP_CONFIG.MAX_ATTEMPTS}
              </Text>
            </View>
          )}
        </View>
      ) : (
        <View style={modalStyles.otpContainer}>
          <Text style={modalStyles.modalText}>No transaction data available</Text>
        </View>
      )}
    </CustomModal>
  );
};

export default OtpModal;
