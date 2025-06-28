/**
 * Modal component styles
 */
import { StyleSheet } from 'react-native';

export const modalStyles = StyleSheet.create({
  // Base Modal Styles
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
  },
  autoCheckText: {
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
  },
  otpActions: {
    width: '100%',
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
  otpInput: {    borderWidth: 2,
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

  // Compact Payment Status Modal Styles
  compactStatusContainer: {
    paddingVertical: 10,
  },
  compactStatusHeader: {
    alignItems: 'center',
    marginBottom: 15,
    paddingBottom: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  compactStatusText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#374151',
    textAlign: 'center',
  },
  compactStatusDetails: {
    marginBottom: 15,
  },
  compactStatusRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 6,
  },
  compactLabel: {
    fontSize: 14,
    color: '#6b7280',
    fontWeight: '500',
  },
  compactValue: {
    fontSize: 14,
    color: '#1f2937',
    fontWeight: '600',
  },
  compactIndicator: {
    alignItems: 'center',
    marginBottom: 15,
    paddingVertical: 8,
    backgroundColor: '#f3f4f6',
    borderRadius: 8,
  },
  compactIndicatorText: {
    fontSize: 12,
    color: '#6b7280',
    fontStyle: 'italic',
  },
  compactTimeoutMessage: {
    alignItems: 'center',
    marginBottom: 15,
    paddingVertical: 8,
    backgroundColor: '#fef3c7',
    borderRadius: 8,
  },
  compactTimeoutText: {
    fontSize: 12,
    color: '#92400e',
    textAlign: 'center',
  },
  compactActionButton: {
    backgroundColor: '#6b7280',
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  compactActionText: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '600',
  },
});
