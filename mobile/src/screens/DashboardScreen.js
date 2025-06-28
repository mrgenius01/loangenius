/**
 * Dashboard Screen Component
 * Main screen for making payments and viewing transaction status
 */
import React, { useState } from 'react';
import { SafeAreaView, View, Text, TextInput, TouchableOpacity, StatusBar, ScrollView } from 'react-native';
import CustomModal from '../components/CustomModal';
import PaymentStatusModal from '../components/PaymentStatusModal';
import OtpModal from '../components/OtpModal';
import ApiService from '../services/apiService';
import { PAYMENT_METHODS } from '../constants/config';
import { dashboardStyles } from '../styles/dashboardStyles';

const DashboardScreen = ({ onLogout }) => {
  const [phoneNumber, setPhoneNumber] = useState('');
  const [amount, setAmount] = useState('');
  const [selectedMethod, setSelectedMethod] = useState('ecocash');
  const [loading, setLoading] = useState(false);
  const [lastTransaction, setLastTransaction] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('Unknown');

  const [showStatusModal, setShowStatusModal] = useState(false);
  const [showSuccessModal, setShowSuccessModal] = useState(false);
  const [showErrorModal, setShowErrorModal] = useState(false);
  const [showOtpModal, setShowOtpModal] = useState(false);
  const [modalMessage, setModalMessage] = useState('');

  // Test API connection
  const testConnection = async () => {
    try {
      const response = await ApiService.testConnection();
      if (response.success) {
        setConnectionStatus('Connected ✅');
        setModalMessage('Successfully connected to backend!');
        setShowSuccessModal(true);
      } else {
        setConnectionStatus('Disconnected ❌');
        setModalMessage(`${response.details}\n\nTroubleshooting:\n1. Make sure Flask server is running\n2. Update API_BASE_URL with your computer's IP address\n3. Check firewall settings`);
        setShowErrorModal(true);
      }
    } catch (error) {
      setConnectionStatus('Disconnected ❌');
      setModalMessage('Unexpected error occurred while testing connection');
      setShowErrorModal(true);
    }
  };

  const handlePayment = async () => {
    if (!phoneNumber || !amount) {
      setModalMessage('Please fill in all fields');
      setShowErrorModal(true);
      return;
    }

    if (parseFloat(amount) <= 0) {
      setModalMessage('Please enter a valid amount');
      setShowErrorModal(true);
      return;
    }

    setLoading(true);
    try {
      const response = await ApiService.createPayment(phoneNumber, amount, selectedMethod);

      if (response.success && response.data.status === 'success') {        const transactionData = {
          ...response.data,
          amount: amount,
          method: selectedMethod,
          phone_number: phoneNumber
        };
        setLastTransaction(transactionData);
        
        // Clear form
        setPhoneNumber('');
        setAmount('');

        // Show appropriate modal based on payment method
        if (selectedMethod === 'omari') {
          // For OMari, immediately show OTP modal
          setShowOtpModal(true);
        } else {
          // For other methods, show status modal
          setShowStatusModal(true);
        }
      } else {
        setModalMessage(response.data?.message || response.error || 'Something went wrong');
        setShowErrorModal(true);
      }
    } catch (error) {
      console.error('Payment error:', error);
      setModalMessage(`Network error: ${error.message}\n\nTroubleshooting:\n1. Check if backend is running\n2. Verify IP address\n3. Test API connection first`);
      setShowErrorModal(true);
    } finally {
      setLoading(false);
    }
  };

  const checkPaymentStatus = () => {
    if (!lastTransaction) {
      setModalMessage('No recent transaction to check');
      setShowErrorModal(true);
      return;
    }
    setShowStatusModal(true);
  };

  const handleOtpComplete = () => {
    setShowOtpModal(false);
    setShowStatusModal(true);
  };

  const renderHeader = () => (
    <View style={dashboardStyles.header}>
      <View style={dashboardStyles.headerLeft}>
        <Text style={dashboardStyles.title}>Dashboard</Text>
        <Text style={dashboardStyles.headerSubtext}>Make your loan repayment</Text>
        <Text style={dashboardStyles.connectionStatus}>Status: {connectionStatus}</Text>
      </View>
      <View style={dashboardStyles.headerRight}>
        <TouchableOpacity style={dashboardStyles.testButton} onPress={testConnection}>
          <Text style={dashboardStyles.testButtonText}>Test API</Text>
        </TouchableOpacity>
        <TouchableOpacity style={dashboardStyles.logoutButton} onPress={onLogout}>
          <Text style={dashboardStyles.logoutButtonText}>Logout</Text>
        </TouchableOpacity>
      </View>
    </View>
  );

  const renderPaymentForm = () => (
    <View style={dashboardStyles.paymentCard}>
      <Text style={dashboardStyles.cardTitle}>Make a Payment</Text>

      <View style={dashboardStyles.formGroup}>
        <Text style={dashboardStyles.label}>Phone Number</Text>
        <TextInput
          style={dashboardStyles.paymentInput}
          placeholder="e.g., 0771234567"
          keyboardType="phone-pad"
          value={phoneNumber}
          onChangeText={setPhoneNumber}
        />
      </View>

      <View style={dashboardStyles.formGroup}>
        <Text style={dashboardStyles.label}>Amount (ZWL)</Text>
        <TextInput
          style={dashboardStyles.paymentInput}
          placeholder="e.g., 50.00"
          keyboardType="numeric"
          value={amount}
          onChangeText={setAmount}
        />
      </View>

      <View style={dashboardStyles.formGroup}>
        <Text style={dashboardStyles.label}>Payment Method</Text>
        <View style={dashboardStyles.methodContainer}>
          {PAYMENT_METHODS.map((method) => (
            <TouchableOpacity
              key={method.key}
              style={[
                dashboardStyles.methodButton,
                selectedMethod === method.key && { backgroundColor: method.color }
              ]}
              onPress={() => setSelectedMethod(method.key)}
            >
              <Text style={[
                dashboardStyles.methodText,
                selectedMethod === method.key && dashboardStyles.methodTextSelected
              ]}>
                {method.label}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      <TouchableOpacity
        style={[dashboardStyles.payButton, loading && dashboardStyles.payButtonDisabled]}
        onPress={handlePayment}
        disabled={loading}
      >
        <Text style={dashboardStyles.payButtonText}>
          {loading ? 'Processing...' : 'Pay Now'}
        </Text>
      </TouchableOpacity>
    </View>
  );

  const renderRecentTransaction = () => {
    if (!lastTransaction) return null;

    return (
      <View style={dashboardStyles.transactionCard}>
        <Text style={dashboardStyles.cardTitle}>Recent Transaction</Text>
        <View style={dashboardStyles.transactionInfo}>
          <Text style={dashboardStyles.transactionText}>Reference: {lastTransaction.reference}</Text>
          <Text style={dashboardStyles.transactionText}>Amount: ${lastTransaction.amount}</Text>
          <Text style={dashboardStyles.transactionText}>Method: {lastTransaction.method.toUpperCase()}</Text>
        </View>
        <TouchableOpacity style={dashboardStyles.statusButton} onPress={checkPaymentStatus}>
          <Text style={dashboardStyles.statusButtonText}>Check Status</Text>
        </TouchableOpacity>
      </View>
    );
  };

  return (
    <SafeAreaView style={dashboardStyles.container}>
      <StatusBar barStyle="dark-content" backgroundColor="#f8fafc" />
      <ScrollView style={dashboardStyles.scrollView}>
        {renderHeader()}
        {renderPaymentForm()}
        {renderRecentTransaction()}
      </ScrollView>

      {/* Custom Modals */}
      <CustomModal
        visible={showSuccessModal}
        onClose={() => setShowSuccessModal(false)}
        title="Success"
        type="success"
      >
        <Text style={dashboardStyles.modalText}>{modalMessage}</Text>
      </CustomModal>

      <CustomModal
        visible={showErrorModal}
        onClose={() => setShowErrorModal(false)}
        title="Error"
        type="error"
      >
        <Text style={dashboardStyles.modalText}>{modalMessage}</Text>
      </CustomModal>

      <PaymentStatusModal
        visible={showStatusModal}
        onClose={() => setShowStatusModal(false)}
        transaction={lastTransaction}
      />

      <OtpModal
        visible={showOtpModal}
        onClose={() => setShowOtpModal(false)}
        transaction={lastTransaction}
        onOtpSuccess={handleOtpComplete}
      />
    </SafeAreaView>
  );
};

export default DashboardScreen;
