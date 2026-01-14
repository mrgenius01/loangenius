// Example notification service (stub)
async function sendNotification(userId, message) {
  // Integrate with email/SMS/push provider
  // For now, just log
  console.log(`Notify user ${userId}: ${message}`);
}

module.exports = { sendNotification };
