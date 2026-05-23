import { RAZORPAY_KEY_ID } from '@/lib/api';

/** Shown only when user picks "Pay online" in test mode. */
export function TestPaymentBanner() {
  if (!RAZORPAY_KEY_ID || !RAZORPAY_KEY_ID.startsWith('rzp_test_')) return null;
  return (
    <div className="alert test-pay-banner">
      <strong>Test mode — no real money.</strong>
      <p>For online payment, use <strong>UPI only</strong> in the popup (avoids international card errors):</p>
      <ul>
        <li><strong>UPI ID:</strong> <code>success@razorpay</code> — no OTP to your phone</li>
        <li><strong>Indian test card (if card shown):</strong> 5267 3181 8797 5449 · CVV 123 · future expiry</li>
      </ul>
      <p className="test-pay-note">
        Do <strong>not</strong> use your real UPI or card — that sends OTP to your number.
        Prefer <strong>Cash on Delivery</strong> below to place orders without Razorpay.
      </p>
    </div>
  );
}
