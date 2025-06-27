/**
 * Login Screen Component
 * Handles user authentication
 */
import React, { useState } from 'react';
import { SafeAreaView, View, Text, TextInput, TouchableOpacity, StatusBar, Alert } from 'react-native';
import { MOCK_CREDENTIALS } from '../constants/config';
import { loginStyles } from '../styles/loginStyles';

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
    <SafeAreaView style={loginStyles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#1e3a8a" />
      <View style={loginStyles.content}>
        {/* Header */}
        <View style={loginStyles.header}>
          <Text style={loginStyles.appTitle}>LoanPay</Text>
          <Text style={loginStyles.subtitle}>Secure Loan Repayment</Text>
        </View>

        {/* Login Form */}
        <View style={loginStyles.form}>
          <Text style={loginStyles.welcomeText}>Welcome Back</Text>
          <Text style={loginStyles.loginSubtext}>Sign in to continue</Text>

          <View style={loginStyles.inputGroup}>
            <Text style={loginStyles.inputLabel}>Username</Text>
            <TextInput
              style={loginStyles.input}
              value={username}
              onChangeText={setUsername}
              placeholder="Enter your username"
              placeholderTextColor="#9ca3af"
              autoCapitalize="none"
            />
          </View>

          <View style={loginStyles.inputGroup}>
            <Text style={loginStyles.inputLabel}>Password</Text>
            <TextInput
              style={loginStyles.input}
              value={password}
              onChangeText={setPassword}
              placeholder="Enter your password"
              placeholderTextColor="#9ca3af"
              secureTextEntry
            />
          </View>

          <TouchableOpacity
            style={[loginStyles.loginButton, loading && loginStyles.loginButtonDisabled]}
            onPress={handleLogin}
            disabled={loading}
          >
            <Text style={loginStyles.loginButtonText}>
              {loading ? 'Signing In...' : 'Sign In'}
            </Text>
          </TouchableOpacity>

          {/* Demo Credentials */}
          <View style={loginStyles.demoCredentials}>
            <Text style={loginStyles.demoTitle}>Demo Credentials:</Text>
            <Text style={loginStyles.demoText}>Username: {MOCK_CREDENTIALS.username}</Text>
            <Text style={loginStyles.demoText}>Password: {MOCK_CREDENTIALS.password}</Text>
          </View>
        </View>
      </View>
    </SafeAreaView>
  );
};

export default LoginScreen;
