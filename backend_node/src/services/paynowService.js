const { Paynow } = require('paynow');

const paynow = new Paynow(
  process.env.PAYNOW_INTEGRATION_ID,
  process.env.PAYNOW_INTEGRATION_KEY
);
paynow.resultUrl = process.env.PAYNOW_RESULT_URL;
paynow.returnUrl = process.env.PAYNOW_RETURN_URL;

async function payNowMobile({ reference, amount, phone_number, method, email }) {
  console.log(`[PayNow] Integration ID: ${process.env.PAYNOW_INTEGRATION_ID}`);
  let payment = paynow.createPayment(reference, email || undefined);
  payment.add('Loan Repayment', amount);
  try {
    const response = await paynow.sendMobile(payment, phone_number, method);
    return response;
  } catch (err) {
    console.error('[PayNow] Error:', err);
    return { success: false, error: err.message };
  }
}

async function pollPaynowTransaction(pollUrl) {
  try {
    const status = await paynow.pollTransaction(pollUrl);
    return status;
  } catch (err) {
    console.error('[PayNow] Poll Error:', err);
    return { error: err.message };
  }
}

// OTP submission for multistage payments (e.g. OMARI, Innbucks)
const axios = require('axios');

async function submitPaynowOtp({ otp, otpUrl }) {
  try {
    // Paynow expects a POST to the OTP URL with the OTP value
    const response = await axios.post(otpUrl, { otp });
    return response.data;
  } catch (err) {
    console.error('[PayNow] OTP Error:', err);
    return { error: err.message };
  }
}

module.exports = { payNowMobile, pollPaynowTransaction, submitPaynowOtp };
