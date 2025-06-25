import React, { useState } from 'react';
import { SafeAreaView, View, Text, TextInput, TouchableOpacity, StyleSheet, Alert, StatusBar, ScrollView } from 'react-native';
import axios from 'axios';

// Mock login credentials
const MOCK_CREDENTIALS = {
  username: 'admin',
  password: 'password123'
};

// For Android Emulator, use 10.0.2.2 to access host machine's localhost
const API_BASE_URL = 'http://10.0.26.142:5000';
// Alternative: Use your computer's IP address (find with 'ipconfig' command)
// const API_BASE_URL = 'http://192.168.1.100:5000'; // Replace with your actual IP

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
  const [connectionStatus, setConnectionStatus] = useState('Unknown');

  const paymentMethods = [
    { key: 'ecocash', label: 'EcoCash', color: '#10ac84' },
    { key: 'innbucks', label: 'InnBucks', color: '#3742fa' },
  ];

  // Test API connection
  const testConnection = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/health`, { timeout: 5000 });
      setConnectionStatus('Connected ✅');
      Alert.alert('Connection Test', 'Successfully connected to backend!');
    } catch (error) {
      setConnectionStatus('Disconnected ❌');
      Alert.alert(
        'Connection Failed', 
        `Cannot connect to backend at ${API_BASE_URL}\n\nTroubleshooting:\n1. Make sure Flask server is running\n2. Update API_BASE_URL with your computer's IP address\n3. Check firewall settings`
      );
    }
  };

  const handlePayment = async () => {
    if (!phoneNumber || !amount) {
      Alert.alert('Error', 'Please fill in all fields');
      return;
    }

    if (parseFloat(amount) <= 0) {
      Alert.alert('Error', 'Please enter a valid amount');
      return;
    }

    setLoading(true);

    try {
      // First try the test endpoint for debugging
      const response = await axios.post(`${API_BASE_URL}/payment`, {
        phoneNumber,
        amount,
        method: selectedMethod
      });      if (response.data.status === 'success') {
        setLastTransaction(response.data);
        
        // Create a more detailed alert message
        let alertMessage = `Reference: ${response.data.reference}`;
        if (response.data.paynow_reference) {
          alertMessage += `\nPaynow Ref: ${response.data.paynow_reference}`;
        }
        if (response.data.instructions) {
          alertMessage += `\n\nInstructions:\n${response.data.instructions}`;
        }
        
        Alert.alert(
          'Payment Initiated!',
          alertMessage,
          [
            ...(response.data.redirect_url ? [{
              text: 'Open Payment Link',
              onPress: () => {
                // You could use Linking.openURL(response.data.redirect_url) here
                console.log('Redirect URL:', response.data.redirect_url);
              }
            }] : []),
            { 
              text: 'OK', 
              onPress: () => {
                setPhoneNumber('');
                setAmount('');
              }
            }
          ]
        );
      } else {
        Alert.alert('Payment Failed', response.data.message || 'Something went wrong');
      }
    } catch (error) {
      console.error('Payment error:', error);
      Alert.alert(
        'Payment Failed',
        `Network error: ${error.message}\n\nAPI URL: ${API_BASE_URL}\n\nTroubleshooting:\n1. Check if backend is running\n2. Verify IP address\n3. Test API connection first`
      );
    } finally {
      setLoading(false);
    }
  };

  const checkPaymentStatus = async () => {
    if (!lastTransaction) {
      Alert.alert('No Transaction', 'No recent transaction to check');
      return;
    }

    try {
      const response = await axios.get(`${API_BASE_URL}/payment/status/${lastTransaction.reference}`);
      const status = response.data;
      
      Alert.alert(
        'Payment Status',
        `Reference: ${status.reference}\nStatus: ${status.status.toUpperCase()}\nAmount: $${status.amount}\nPaid: ${status.paid ? 'Yes' : 'No'}`
      );
    } catch (error) {
      Alert.alert('Error', 'Failed to check payment status');
    }
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
            <Text style={styles.label}>Amount (USD)</Text>
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
              <Text style={styles.transactionText}>Amount: ${amount}</Text>
              <Text style={styles.transactionText}>Method: {selectedMethod.toUpperCase()}</Text>
            </View>
            <TouchableOpacity style={styles.statusButton} onPress={checkPaymentStatus}>
              <Text style={styles.statusButtonText}>Check Status</Text>
            </TouchableOpacity>
          </View>
        )}
      </ScrollView>
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
  },  scrollView: {
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
  },
  statusButton: {
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
});
