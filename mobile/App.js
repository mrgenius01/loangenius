import React, { useState, useEffect } from 'react';
import { SafeAreaView, View, Text, TextInput, TouchableOpacity, StyleSheet, Alert, StatusBar, ScrollView, Modal, Animated, Dimensions, ActivityIndicator, Linking } from 'react-native';
import axios from 'axios';

// Mock login credentials
const MOCK_CREDENTIALS = {
  username: 'admin',
  password: 'password123'
};

// Production backend URL - deployed on Render
// const API_BASE_URL = 'https://loangenius.onrender.com';
// For local development, use:
const API_BASE_URL = 'http://192.168.137.1:5000';

const { width, height } = Dimensions.get('window');

// Custom Modal Component
const CustomModal = ({ visible, onClose, title, children, type = 'info' }) => {
  const [fadeAnim] = useState(new Animated.Value(0));
  const [scaleAnim] = useState(new Animated.Value(0.3));

  useEffect(() => {
    if (visible) {
      Animated.parallel([
        Animated.timing(fadeAnim, {
          toValue: 1,
          duration: 300,
          useNativeDriver: true,
        }),
        Animated.spring(scaleAnim, {
          toValue: 1,
          tension: 100,
          friction: 8,
          useNativeDriver: true,
        }),
      ]).start();
    } else {
      Animated.parallel([
        Animated.timing(fadeAnim, {
          toValue: 0,
          duration: 200,
          useNativeDriver: true,
        }),
        Animated.timing(scaleAnim, {
          toValue: 0.3,
          duration: 200,
          useNativeDriver: true,
        }),
      ]).start();
    }
  }, [visible]);

  const getModalColor = () => {
    switch (type) {
      case 'success': return '#10b981';
      case 'error': return '#ef4444';
      case 'warning': return '#f59e0b';
      case 'info': return '#3b82f6';
      default: return '#3b82f6';
    }
  };

  const getModalIcon = () => {
    switch (type) {
      case 'success': return '✅';
      case 'error': return '❌';
      case 'warning': return '⚠️';
      case 'info': return 'ℹ️';
      default: return 'ℹ️';
    }
  };

  return (
    <Modal transparent visible={visible} animationType="none">
      <Animated.View style={[styles.modalOverlay, { opacity: fadeAnim }]}>
        <Animated.View
          style={[
            styles.modalContent,
            {
              transform: [{ scale: scaleAnim }],
              borderTopColor: getModalColor()
            }
          ]}
        >
          <View style={[styles.modalHeader, { backgroundColor: getModalColor() }]}>
            <Text style={styles.modalIcon}>{getModalIcon()}</Text>
            <Text style={styles.modalTitle}>{title}</Text>
          </View>
          <View style={styles.modalBody}>
            {children}
          </View>
          <TouchableOpacity style={[styles.modalCloseButton, { backgroundColor: getModalColor() }]} onPress={onClose}>
            <Text style={styles.modalCloseText}>Close</Text>
          </TouchableOpacity>
        </Animated.View>
      </Animated.View>
    </Modal>
  );
};

// Payment Status Modal Component
const PaymentStatusModal = ({ visible, onClose, transaction, onStatusCheck }) => {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [autoCheck, setAutoCheck] = useState(true);

  useEffect(() => {
    if (visible && transaction && autoCheck) {
      checkStatus();
      const interval = setInterval(checkStatus, 5000); // Check every 5 seconds
      return () => clearInterval(interval);
    }
  }, [visible, transaction, autoCheck]);

  const checkStatus = async () => {
    if (!transaction) return;

    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE_URL}/payment/status/${transaction.reference}`);
      setStatus(response.data);

      // Stop auto-checking if payment is completed or failed
      if (response.data.status === 'paid' || response.data.status === 'cancelled') {
        setAutoCheck(false);
      }
    } catch (error) {
      console.error('Status check error:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = () => {
    if (!status) return '#6b7280';
    switch (status.status) {
      case 'paid': return '#10b981';
      case 'pending': return '#f59e0b';
      case 'cancelled': return '#ef4444';
      default: return '#6b7280';
    }
  };

  const getStatusIcon = () => {
    if (!status) return '⏳';
    switch (status.status) {
      case 'paid': return '✅';
      case 'pending': return '⏳';
      case 'cancelled': return '❌';
      default: return '❓';
    }
  };

  return (
    <CustomModal visible={visible} onClose={onClose} title="Payment Status" type={status?.status === 'paid' ? 'success' : status?.status === 'cancelled' ? 'error' : 'info'}>
      {transaction && (
        <View style={styles.statusContainer}>
          <View style={styles.statusHeader}>
            <Text style={[styles.statusIcon, { color: getStatusColor() }]}>
              {getStatusIcon()}
            </Text>
            <Text style={[styles.statusText, { color: getStatusColor() }]}>
              {status ? status.status.toUpperCase() : 'CHECKING...'}
            </Text>
          </View>

          <View style={styles.statusDetails}>
            <View style={styles.statusRow}>
              <Text style={styles.statusLabel}>Reference:</Text>
              <Text style={styles.statusValue}>{transaction.reference}</Text>
            </View>

            {transaction.paynow_reference && (
              <View style={styles.statusRow}>
                <Text style={styles.statusLabel}>Paynow Reference:</Text>
                <Text style={styles.statusValue}>{transaction.paynow_reference}</Text>
              </View>
            )}

            <View style={styles.statusRow}>
              <Text style={styles.statusLabel}>Amount:</Text>
              <Text style={styles.statusValue}>${transaction.amount}</Text>
            </View>

            {status && (
              <>
                <View style={styles.statusRow}>
                  <Text style={styles.statusLabel}>Status:</Text>
                  <Text style={[styles.statusValue, { color: getStatusColor(), fontWeight: 'bold' }]}>
                    {status.status.toUpperCase()}
                  </Text>
                </View>

                <View style={styles.statusRow}>
                  <Text style={styles.statusLabel}>Paid:</Text>
                  <Text style={[styles.statusValue, { color: status.paid ? '#10b981' : '#ef4444', fontWeight: 'bold' }]}>
                    {status.paid ? 'YES' : 'NO'}
                  </Text>
                </View>
              </>
            )}
          </View>

          {transaction.instructions && (
            <View style={styles.instructionsContainer}>
              <Text style={styles.instructionsTitle}>Instructions:</Text>
              <Text style={styles.instructionsText}>{transaction.instructions}</Text>
            </View>
          )}

          <View style={styles.statusActions}>
            <TouchableOpacity
              style={[styles.statusButton, { backgroundColor: '#3b82f6' }]}
              onPress={checkStatus}
              disabled={loading}
            >
              {loading ? (
                <ActivityIndicator size="small" color="#ffffff" />
              ) : (
                <Text style={styles.statusButtonText}>Refresh Status</Text>
              )}
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.statusButton, { backgroundColor: autoCheck ? '#ef4444' : '#10b981' }]}
              onPress={() => setAutoCheck(!autoCheck)}
            >
              <Text style={styles.statusButtonText}>
                {autoCheck ? 'Stop Auto-Check' : 'Start Auto-Check'}
              </Text>

            </TouchableOpacity>
          </View>

          {autoCheck && (
            <View style={styles.autoCheckIndicator}>
              <ActivityIndicator size="small" color="#3b82f6" />
              <Text style={styles.autoCheckText}>Auto-checking every 5 seconds...</Text>
            </View>
          )}
        </View>
      )}    </CustomModal>
  );
};

// OMari OTP Modal Component
const OtpModal = ({ visible, onClose, transaction, onOtpSuccess }) => {
  const [otpCode, setOtpCode] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [otpError, setOtpError] = useState('');
  const [attempts, setAttempts] = useState(0);
  const [showOtpInput, setShowOtpInput] = useState(false);
  const [otpSent, setOtpSent] = useState(false);
  const [sendingOtp, setSendingOtp] = useState(false);
  const maxAttempts = 5;

  useEffect(() => {
    if (visible) {
      // Reset state when modal opens
      setOtpCode('');
      setOtpError('');
      setAttempts(0);
      setSubmitting(false);
      setShowOtpInput(false);
      setOtpSent(false);
      setSendingOtp(false);
    }
  }, [visible]);

  const sendOtp = async () => {
    if (!transaction?.reference) {
      setOtpError('Transaction reference not found');
      return;
    }

    setSendingOtp(true);
    setOtpError('');

    try {
      // Initiate OTP request - this will trigger the OTP to be sent to the user's phone
      const response = await axios.post(`${API_BASE_URL}/payment/otp/request`, {
        reference: transaction.reference
      });

      if (response.data.status === 'success') {
        setOtpSent(true);
        setShowOtpInput(true);
        Alert.alert(
          'OTP Sent!',
          'An OTP has been sent to your phone. Please enter it below to complete the payment.',
          [{ text: 'OK' }]
        );
      } else {
        setOtpError(response.data.message || 'Failed to send OTP');
      }
    } catch (error) {
      let errorMessage = 'Failed to send OTP';
      if (error.response && error.response.data) {
        errorMessage = error.response.data.error || error.response.data.message || errorMessage;
      }
      setOtpError(errorMessage);
      console.error('OTP request error:', error);
    } finally {
      setSendingOtp(false);
    }
  };

  const submitOtp = async () => {
    if (!otpCode || otpCode.length !== 6) {
      setOtpError('Please enter a valid 6-digit OTP');
      return;
    }

    setSubmitting(true);
    setOtpError('');

    try {
      const response = await axios.post(`${API_BASE_URL}/payment/otp`, {
        reference: transaction.reference,
        otp: otpCode
      });

      if (response.data.status === 'success') {
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
      }
    } catch (error) {
      const newAttempts = attempts + 1;
      setAttempts(newAttempts);
      
      let errorMessage = 'Failed to submit OTP';
      if (error.response && error.response.data) {
        errorMessage = error.response.data.error || error.response.data.message || errorMessage;
      }
      
      if (newAttempts >= maxAttempts) {
        setOtpError(`Maximum attempts reached (${maxAttempts}). Transaction cancelled. Please start a new payment.`);
      } else {
        const remainingAttempts = maxAttempts - newAttempts;
        setOtpError(`${errorMessage}. ${remainingAttempts} attempts remaining.`);
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <CustomModal visible={visible} onClose={onClose} title="OMari Payment" type="info">
      {transaction && (
        <View style={styles.otpContainer}>
          <View style={styles.otpHeader}>
            <Text style={styles.otpIcon}>💳</Text>
            <Text style={styles.otpTitle}>Complete OMari Payment</Text>
          </View>

          <View style={styles.otpDetails}>
            <View style={styles.statusRow}>
              <Text style={styles.statusLabel}>Reference:</Text>
              <Text style={styles.statusValue}>{transaction.reference}</Text>
            </View>
            <View style={styles.statusRow}>
              <Text style={styles.statusLabel}>Amount:</Text>
              <Text style={styles.statusValue}>${transaction.amount}</Text>
            </View>
            <View style={styles.statusRow}>
              <Text style={styles.statusLabel}>Phone:</Text>
              <Text style={styles.statusValue}>{transaction.phone_number}</Text>
            </View>
          </View>

          {!otpSent ? (
            <View style={styles.otpInstructions}>
              <Text style={styles.instructionsTitle}>Payment Steps:</Text>
              <Text style={styles.instructionsText}>
                1. Click "Send OTP" to initiate the OMari payment{'\n'}
                2. You will receive an OTP on your phone{'\n'}
                3. Enter the OTP below to complete the payment{'\n'}
                4. Payment status will update automatically
              </Text>
            </View>
          ) : (
            <View style={styles.otpInstructions}>
              <Text style={styles.instructionsTitle}>Enter OTP:</Text>
              <Text style={styles.instructionsText}>
                Enter the 6-digit OTP sent to your phone to complete the payment.
              </Text>
            </View>
          )}

          <View style={styles.otpActions}>
            {!otpSent ? (
              <TouchableOpacity
                style={[styles.statusButton, { backgroundColor: sendingOtp ? '#95a5a6' : '#e74c3c' }]}
                onPress={sendOtp}
                disabled={sendingOtp}
              >
                {sendingOtp ? (
                  <ActivityIndicator color="white" size="small" />
                ) : (
                  <Text style={styles.statusButtonText}>Send OTP</Text>
                )}
              </TouchableOpacity>
            ) : (
              <View style={styles.otpInputSection}>
                <View style={styles.otpInputContainer}>
                  <TextInput
                    style={styles.otpInput}
                    value={otpCode}
                    onChangeText={setOtpCode}
                    placeholder="Enter 6-digit OTP"
                    keyboardType="numeric"
                    maxLength={6}
                    editable={!submitting && attempts < maxAttempts}
                  />
                </View>
                
                {otpError ? (
                  <Text style={styles.otpErrorText}>{otpError}</Text>
                ) : null}

                <View style={styles.otpButtonContainer}>
                  <TouchableOpacity
                    style={[styles.statusButton, { 
                      backgroundColor: submitting || attempts >= maxAttempts ? '#95a5a6' : '#10b981',
                      marginRight: 10,
                      flex: 1
                    }]}
                    onPress={submitOtp}
                    disabled={submitting || attempts >= maxAttempts}
                  >
                    {submitting ? (
                      <ActivityIndicator color="white" size="small" />
                    ) : (
                      <Text style={styles.statusButtonText}>Submit OTP</Text>
                    )}
                  </TouchableOpacity>

                  <TouchableOpacity
                    style={[styles.statusButton, { 
                      backgroundColor: sendingOtp ? '#95a5a6' : '#3498db',
                      flex: 1
                    }]}
                    onPress={sendOtp}
                    disabled={sendingOtp}
                  >
                    {sendingOtp ? (
                      <ActivityIndicator color="white" size="small" />
                    ) : (
                      <Text style={styles.statusButtonText}>Resend OTP</Text>
                    )}
                  </TouchableOpacity>
                </View>
              </View>
            )}
          </View>

          {attempts > 0 && attempts < maxAttempts && (
            <View style={styles.attemptsContainer}>
              <Text style={styles.attemptsText}>
                Attempts: {attempts}/{maxAttempts}
              </Text>
            </View>
          )}
        </View>
      )}
    </CustomModal>
  );
};

const LoginScreen = ({ onLogin }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    if (!username || !password) {
      Alert.alert('Error', 'Please enter both username and password');
      return;
    }

    setLoading(true);

    // Simulate API call delay
    setTimeout(() => {
      if (username === MOCK_CREDENTIALS.username && password === MOCK_CREDENTIALS.password) {
        Alert.alert('Success', 'Login successful!', [
          { text: 'OK', onPress: () => onLogin() }
        ]);
      } else {
        Alert.alert('Error', 'Invalid username or password');
      }
      setLoading(false);
    }, 1000);
  };

  return (
    <SafeAreaView style={styles.loginContainer}>
      <StatusBar barStyle="light-content" backgroundColor="#1e3a8a" />
      <View style={styles.loginContent}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.appTitle}>LoanPay</Text>
          <Text style={styles.subtitle}>Secure Loan Repayment</Text>
        </View>

        {/* Login Form */}
        <View style={styles.loginForm}>
          <Text style={styles.welcomeText}>Welcome Back</Text>
          <Text style={styles.loginSubtext}>Sign in to continue</Text>

          <View style={styles.inputGroup}>
            <Text style={styles.inputLabel}>Username</Text>
            <TextInput
              style={styles.input}
              value={username}
              onChangeText={setUsername}
              placeholder="Enter your username"
              placeholderTextColor="#9ca3af"
              autoCapitalize="none"
            />
          </View>

          <View style={styles.inputGroup}>
            <Text style={styles.inputLabel}>Password</Text>
            <TextInput
              style={styles.input}
              value={password}
              onChangeText={setPassword}
              placeholder="Enter your password"
              placeholderTextColor="#9ca3af"
              secureTextEntry
            />
          </View>

          <TouchableOpacity
            style={[styles.loginButton, loading && styles.loginButtonDisabled]}
            onPress={handleLogin}
            disabled={loading}
          >
            <Text style={styles.loginButtonText}>
              {loading ? 'Signing In...' : 'Sign In'}
            </Text>
          </TouchableOpacity>

          {/* Demo Credentials */}
          <View style={styles.demoCredentials}>
            <Text style={styles.demoTitle}>Demo Credentials:</Text>
            <Text style={styles.demoText}>Username: admin</Text>
            <Text style={styles.demoText}>Password: password123</Text>
          </View>
        </View>
      </View>
    </SafeAreaView>
  );
};

const DashboardScreen = ({ onLogout }) => {
  const [phoneNumber, setPhoneNumber] = useState('');
  const [amount, setAmount] = useState('');
  const [selectedMethod, setSelectedMethod] = useState('ecocash');
  const [loading, setLoading] = useState(false);
  const [lastTransaction, setLastTransaction] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('Unknown'); const [showStatusModal, setShowStatusModal] = useState(false);
  const [showSuccessModal, setShowSuccessModal] = useState(false);
  const [showErrorModal, setShowErrorModal] = useState(false);
  const [showOtpModal, setShowOtpModal] = useState(false);
  const [modalMessage, setModalMessage] = useState('');

  const paymentMethods = [
    { key: 'ecocash', label: 'EcoCash', color: '#10ac84' },
    { key: 'innbucks', label: 'InnBucks', color: '#3742fa' },
    { key: 'omari', label: 'OMari', color: '#3956fa' }
  ];
  // Test API connection
  const testConnection = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/health`, { timeout: 5000 });
      setConnectionStatus('Connected ✅');
      setModalMessage('Successfully connected to backend!');
      setShowSuccessModal(true);
    } catch (error) {
      setConnectionStatus('Disconnected ❌');
      setModalMessage(`Cannot connect to backend at ${API_BASE_URL}\n\nTroubleshooting:\n1. Make sure Flask server is running\n2. Update API_BASE_URL with your computer's IP address\n3. Check firewall settings`);
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
      // Use real payment endpoint for production
      const response = await axios.post(`${API_BASE_URL}/payment`, {
        phoneNumber,
        amount,
        method: selectedMethod
      }); if (response.data.status === 'success') {
        const transactionData = {
          ...response.data,
          amount: amount,
          method: selectedMethod
        };
        setLastTransaction(transactionData);
        // Clear form
        setPhoneNumber('');
        setAmount('');

        // Show appropriate modal based on payment method
        if (selectedMethod === 'omari' && (response.data.remoteotpurl || response.data.redirect_url)) {
          // Show OTP modal for OMari payments
          setShowOtpModal(true);
        } else {
          // Show status modal for other payment methods
          setShowStatusModal(true);
        }
      } else {
        setModalMessage(response.data.message || 'Something went wrong');
        setShowErrorModal(true);
      }
    } catch (error) {
      console.error('Payment error:', error);
      setModalMessage(`Network error: ${error.message}\n\nAPI URL: ${API_BASE_URL}\n\nTroubleshooting:\n1. Check if backend is running\n2. Verify IP address\n3. Test API connection first`);
      setShowErrorModal(true);
    } finally {
      setLoading(false);
    }
  }; const checkPaymentStatus = () => {
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

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="dark-content" backgroundColor="#f8fafc" />
      <ScrollView style={styles.scrollView}>
        {/* Header */}
        <View style={styles.dashboardHeader}>
          <View style={styles.headerLeft}>
            <Text style={styles.title}>Dashboard</Text>
            <Text style={styles.headerSubtext}>Make your loan repayment</Text>
            <Text style={styles.connectionStatus}>Status: {connectionStatus}</Text>
          </View>
          <View style={styles.headerRight}>
            <TouchableOpacity style={styles.testButton} onPress={testConnection}>
              <Text style={styles.testButtonText}>Test API</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.logoutButton} onPress={onLogout}>
              <Text style={styles.logoutButtonText}>Logout</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Payment Card */}
        <View style={styles.paymentCard}>
          <Text style={styles.cardTitle}>Make a Payment</Text>

          <View style={styles.formGroup}>
            <Text style={styles.label}>Phone Number</Text>
            <TextInput
              style={styles.paymentInput}
              placeholder="e.g., 0771234567"
              keyboardType="phone-pad"
              value={phoneNumber}
              onChangeText={setPhoneNumber}
            />
          </View>

          <View style={styles.formGroup}>
            <Text style={styles.label}>Amount (ZWL)</Text>
            <TextInput
              style={styles.paymentInput}
              placeholder="e.g., 50.00"
              keyboardType="numeric"
              value={amount}
              onChangeText={setAmount}
            />
          </View>

          <View style={styles.formGroup}>
            <Text style={styles.label}>Payment Method</Text>
            <View style={styles.methodContainer}>
              {paymentMethods.map((method) => (
                <TouchableOpacity
                  key={method.key}
                  style={[
                    styles.methodButton,
                    selectedMethod === method.key && { backgroundColor: method.color }
                  ]}
                  onPress={() => setSelectedMethod(method.key)}
                >
                  <Text style={[
                    styles.methodText,
                    selectedMethod === method.key && styles.methodTextSelected
                  ]}>
                    {method.label}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>

          <TouchableOpacity
            style={[styles.payButton, loading && styles.payButtonDisabled]}
            onPress={handlePayment}
            disabled={loading}
          >
            <Text style={styles.payButtonText}>
              {loading ? 'Processing...' : 'Pay Now'}
            </Text>
          </TouchableOpacity>
        </View>

        {/* Recent Transaction */}

        {lastTransaction && (
          <View style={styles.transactionCard}>
            <Text style={styles.cardTitle}>Recent Transaction</Text>
            <View style={styles.transactionInfo}>
              <Text style={styles.transactionText}>Reference: {lastTransaction.reference}</Text>
              <Text style={styles.transactionText}>Amount: ${lastTransaction.amount}</Text>
              <Text style={styles.transactionText}>Method: {lastTransaction.method.toUpperCase()}</Text>
            </View>
            <TouchableOpacity style={styles.statusButton} onPress={checkPaymentStatus}>
              <Text style={styles.statusButtonText}>Check Status</Text>
            </TouchableOpacity>
          </View>
        )}
      </ScrollView>

      {/* Custom Modals */}
      <CustomModal
        visible={showSuccessModal}
        onClose={() => setShowSuccessModal(false)}
        title="Success"
        type="success"
      >
        <Text style={styles.modalText}>{modalMessage}</Text>
      </CustomModal>

      <CustomModal
        visible={showErrorModal}
        onClose={() => setShowErrorModal(false)}
        title="Error"
        type="error"
      >
        <Text style={styles.modalText}>{modalMessage}</Text>
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
      />
    </SafeAreaView>
  );
};

export default function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  const handleLogin = () => setIsLoggedIn(true);
  const handleLogout = () => setIsLoggedIn(false);

  return isLoggedIn ? (
    <DashboardScreen onLogout={handleLogout} />
  ) : (
    <LoginScreen onLogin={handleLogin} />
  );
}

const styles = StyleSheet.create({
  // Login Screen Styles
  loginContainer: {
    flex: 1,
    backgroundColor: '#1e3a8a',
  },
  loginContent: {
    flex: 1,
    justifyContent: 'center',
    paddingHorizontal: 24,
  },
  header: {
    alignItems: 'center',
    marginBottom: 48,
  },
  appTitle: {
    fontSize: 36,
    fontWeight: 'bold',
    color: '#ffffff',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#cbd5e1',
  },
  loginForm: {
    backgroundColor: '#ffffff',
    borderRadius: 20,
    padding: 32,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.1,
    shadowRadius: 20,
    elevation: 8,
  },
  welcomeText: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1f2937',
    textAlign: 'center',
    marginBottom: 8,
  },
  loginSubtext: {
    fontSize: 16,
    color: '#6b7280',
    textAlign: 'center',
    marginBottom: 32,
  },
  inputGroup: {
    marginBottom: 20,
  },
  inputLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 8,
  },
  input: {
    backgroundColor: '#f9fafb',
    borderWidth: 1,
    borderColor: '#e5e7eb',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 14,
    fontSize: 16,
    color: '#1f2937',
  },
  loginButton: {
    backgroundColor: '#1e3a8a',
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: 'center',
    marginTop: 8,
  },
  loginButtonDisabled: {
    backgroundColor: '#9ca3af',
  },
  loginButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
  },
  demoCredentials: {
    marginTop: 24,
    padding: 16,
    backgroundColor: '#f3f4f6',
    borderRadius: 8,
  },
  demoTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 4,
  },
  demoText: {
    fontSize: 13,
    color: '#6b7280',
  },

  // Dashboard Screen Styles
  container: {
    flex: 1,
    backgroundColor: '#f8fafc',
  }, scrollView: {
    flex: 1,
  },
  dashboardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    paddingHorizontal: 20,
    paddingVertical: 24,
    backgroundColor: '#ffffff',
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  headerLeft: {
    flex: 1,
  },
  headerRight: {
    alignItems: 'flex-end',
    gap: 8,
  },
  connectionStatus: {
    fontSize: 12,
    color: '#6b7280',
    marginTop: 2,
  },
  testButton: {
    backgroundColor: '#3b82f6',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
  },
  testButtonText: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: '600',
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#1f2937',
  },
  headerSubtext: {
    fontSize: 14,
    color: '#6b7280',
    marginTop: 4,
  },
  logoutButton: {
    backgroundColor: '#ef4444',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
  },
  logoutButtonText: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '600',
  },
  paymentCard: {
    backgroundColor: '#ffffff',
    marginHorizontal: 20,
    marginTop: 20,
    borderRadius: 16,
    padding: 24,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
  },
  cardTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1f2937',
    marginBottom: 20,
  },
  formGroup: {
    marginBottom: 20,
  },
  label: {
    fontSize: 16,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 8,
  },
  paymentInput: {
    backgroundColor: '#f9fafb',
    borderWidth: 1,
    borderColor: '#e5e7eb',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 14,
    fontSize: 16,
    color: '#1f2937',
  },
  methodContainer: {
    flexDirection: 'row',
    gap: 12,
  },
  methodButton: {
    flex: 1,
    backgroundColor: '#f3f4f6',
    paddingVertical: 14,
    paddingHorizontal: 20,
    borderRadius: 12,
    alignItems: 'center',
  },
  methodText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#6b7280',
  },
  methodTextSelected: {
    color: '#ffffff',
  },
  payButton: {
    backgroundColor: '#1e3a8a',
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: 'center',
    marginTop: 8,
  },
  payButtonDisabled: {
    backgroundColor: '#9ca3af',
  },
  payButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
  },
  transactionCard: {
    backgroundColor: '#ffffff',
    marginHorizontal: 20,
    marginTop: 16,
    marginBottom: 20,
    borderRadius: 16,
    padding: 24,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
  },
  transactionInfo: {
    marginBottom: 16,
  },
  transactionText: {
    fontSize: 14,
    color: '#6b7280',
    marginBottom: 4,
  }, statusButton: {
    backgroundColor: '#10b981',
    borderRadius: 8,
    paddingVertical: 12,
    alignItems: 'center',
  },
  statusButtonText: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '600',
  },

  // Modal Styles
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  modalContent: {
    backgroundColor: '#ffffff',
    borderRadius: 20,
    width: '100%',
    maxWidth: 400,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.25,
    shadowRadius: 25,
    elevation: 10,
    borderTopWidth: 4,
  },
  modalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
  },
  modalIcon: {
    fontSize: 24,
    marginRight: 12,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#ffffff',
    flex: 1,
  },
  modalBody: {
    padding: 20,
  },
  modalText: {
    fontSize: 16,
    color: '#374151',
    lineHeight: 24,
  },
  modalCloseButton: {
    marginHorizontal: 20,
    marginBottom: 20,
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: 'center',
  },
  modalCloseText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
  },

  // Status Modal Styles
  statusContainer: {
    alignItems: 'center',
  },
  statusHeader: {
    alignItems: 'center',
    marginBottom: 20,
  },
  statusIcon: {
    fontSize: 48,
    marginBottom: 8,
  },
  statusText: {
    fontSize: 20,
    fontWeight: 'bold',
  },
  statusDetails: {
    width: '100%',
    marginBottom: 20,
  },
  statusRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#f3f4f6',
  },
  statusLabel: {
    fontSize: 14,
    color: '#6b7280',
    fontWeight: '500',
  },
  statusValue: {
    fontSize: 14,
    color: '#1f2937',
    fontWeight: '600',
    textAlign: 'right',
    flex: 1,
    marginLeft: 10,
  },
  instructionsContainer: {
    backgroundColor: '#f8fafc',
    padding: 16,
    borderRadius: 12,
    marginBottom: 20,
    width: '100%',
  },
  instructionsTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#374151',
    marginBottom: 8,
  },
  instructionsText: {
    fontSize: 13,
    color: '#6b7280',
    lineHeight: 18,
  },
  statusActions: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 16,
    width: '100%',
  },
  statusButton: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 44,
  },
  statusButtonText: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '600',
  },
  autoCheckIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#e5e7eb',
    width: '100%',
  }, autoCheckText: {
    fontSize: 12,
    color: '#6b7280',
    marginLeft: 8,
  },

  // OTP Modal Styles
  otpContainer: {
    alignItems: 'center',
  },
  otpHeader: {
    alignItems: 'center',
    marginBottom: 20,
  },
  otpIcon: {
    fontSize: 48,
    marginBottom: 8,
  },
  otpTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1f2937',
  },
  otpDetails: {
    width: '100%',
    marginBottom: 20,
  },
  otpInstructions: {
    backgroundColor: '#f8fafc',
    padding: 16,
    borderRadius: 12,
    marginBottom: 20,
    width: '100%',
  }, otpActions: {
    width: '100%',
  },
  otpCompletedActions: {
    width: '100%',
    alignItems: 'center',
  },
  otpCompletedInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
    paddingVertical: 12,
    paddingHorizontal: 16,
    backgroundColor: '#f0f9ff',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#0ea5e9',
  },
  otpCompletedIcon: {
    fontSize: 20,
    marginRight: 8,
  },
  otpCompletedText: {
    fontSize: 14,
    color: '#0369a1',
    fontWeight: '600',
  },

  // OTP Input Styles
  otpInputSection: {
    width: '100%',
    alignItems: 'center',
  },
  otpInputContainer: {
    width: '100%',
    marginBottom: 15,
  },
  otpInput: {
    borderWidth: 2,
    borderColor: '#3498db',
    borderRadius: 12,
    padding: 15,
    fontSize: 18,
    textAlign: 'center',
    letterSpacing: 2,
    fontWeight: 'bold',
    backgroundColor: '#f8f9fa',
  },
  otpErrorText: {
    color: '#e74c3c',
    fontSize: 14,
    textAlign: 'center',
    marginBottom: 10,
    paddingHorizontal: 10,
  },
  otpButtonContainer: {
    flexDirection: 'row',
    width: '100%',
    justifyContent: 'space-between',
  },
  attemptsContainer: {
    marginTop: 10,
    padding: 8,
    backgroundColor: '#fff3cd',
    borderRadius: 8,
    borderLeftWidth: 4,
    borderLeftColor: '#ffc107',
  },
  attemptsText: {
    color: '#856404',
    fontSize: 12,
    textAlign: 'center',
    fontWeight: '500',
  },
});
