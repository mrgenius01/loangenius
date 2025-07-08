/**
 * Main App Component - Modularized LoanPay Mobile Application
 * Entry point for the mobile loan repayment application
 */
import React, { useState } from 'react';
import LoginScreen from './src/screens/LoginScreen';
import DashboardScreen from './src/screens/DashboardScreen';

const App = () => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  const handleLogin = () => setIsLoggedIn(true);
  const handleLogout = () => setIsLoggedIn(false);

  return isLoggedIn ? (
    <DashboardScreen onLogout={handleLogout} />
  ) : (
    <LoginScreen onLogin={handleLogin} />
  );
};

export default App;
