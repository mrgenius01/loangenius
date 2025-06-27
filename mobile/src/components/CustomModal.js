/**
 * Reusable custom modal component with animations
 */
import React, { useState, useEffect } from 'react';
import { Modal, View, Text, TouchableOpacity, Animated } from 'react-native';
import { modalStyles } from '../styles/modalStyles';

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
      <Animated.View style={[modalStyles.modalOverlay, { opacity: fadeAnim }]}>
        <Animated.View
          style={[
            modalStyles.modalContent,
            {
              transform: [{ scale: scaleAnim }],
              borderTopColor: getModalColor()
            }
          ]}
        >
          <View style={[modalStyles.modalHeader, { backgroundColor: getModalColor() }]}>
            <Text style={modalStyles.modalIcon}>{getModalIcon()}</Text>
            <Text style={modalStyles.modalTitle}>{title || 'Information'}</Text>
          </View>
          <View style={modalStyles.modalBody}>
            {children}
          </View>
          <TouchableOpacity 
            style={[modalStyles.modalCloseButton, { backgroundColor: getModalColor() }]} 
            onPress={onClose}
          >
            <Text style={modalStyles.modalCloseText}>Close</Text>
          </TouchableOpacity>
        </Animated.View>
      </Animated.View>
    </Modal>
  );
};

export default CustomModal;
