'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { v4 as uuidv4 } from 'uuid';
import {
  cart as cartApi,
  orders,
  auth,
  Cart,
  Address,
  formatPrice,
  CheckoutPayload,
} from '@/lib/api';
import { useAuth } from '@/context/AuthContext';

const emptyForm = {
  shipping_name: '',
  shipping_phone: '',
  shipping_line1: '',
  shipping_line2: '',
  shipping_city: '',
  shipping_state: '',
  shipping_pincode: '',
};

/** Flipkart-style checkout: saved address + COD only (no Razorpay popup). */
export default function CheckoutPage() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
  const [cart, setCart] = useState<Cart | null>(null);
  const [addresses, setAddresses] = useState<Address[]>([]);
  const [selectedAddressId, setSelectedAddressId] = useState<string | null>(null);
  const [useNewAddress, setUseNewAddress] = useState(false);
  const [saveAddress, setSaveAddress] = useState(true);
  const [addressLabel, setAddressLabel] = useState('Home');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);
  const [savingAddress, setSavingAddress] = useState(false);
  const [form, setForm] = useState(emptyForm);

  useEffect(() => {
    if (authLoading) return;
    if (!user) {
      router.replace('/login?next=/checkout');
      return;
    }
    setForm((f) => ({ ...f, shipping_name: user.name || '' }));
    cartApi.get().then(setCart).catch((e) => setError(e.message));
    auth.listAddresses().then((addrs) => {
      setAddresses(addrs);
      const def = addrs.find((a) => a.is_default) || addrs[0];
      if (def) {
        setSelectedAddressId(def.id);
        setUseNewAddress(false);
      } else {
        setUseNewAddress(true);
      }
    }).catch(() => setUseNewAddress(true));
  }, [user, authLoading, router]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm((f) => ({ ...f, [e.target.name]: e.target.value }));
  };

  const validateAddress = (): string | null => {
    if (!useNewAddress && selectedAddressId) return null;
    const required: (keyof typeof emptyForm)[] = [
      'shipping_name', 'shipping_phone', 'shipping_line1',
      'shipping_city', 'shipping_state', 'shipping_pincode',
    ];
    for (const key of required) {
      if (!form[key]?.trim()) return 'Please complete delivery address';
    }
    return null;
  };

  const buildPayload = (): CheckoutPayload => {
    const base: CheckoutPayload = { payment_method: 'cod' };
    if (!useNewAddress && selectedAddressId) {
      return { ...base, address_id: selectedAddressId };
    }
    return {
      ...base,
      ...form,
      save_address: saveAddress,
      address_label: addressLabel,
    };
  };

  const placeOrder = async () => {
    if (!cart?.items.length || !user) return;
    const err = validateAddress();
    if (err) {
      setError(err);
      return;
    }
    if (!useNewAddress && !selectedAddressId && addresses.length > 0) {
      setError('Select a delivery address');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');
    try {
      const result = await orders.checkout(buildPayload(), uuidv4());
      if (result.order.status !== 'confirmed') {
        setError('Order was not confirmed. Please try again or contact support.');
        return;
      }
      router.push(`/orders/view?id=${result.order.id}`);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Could not place order');
    } finally {
      setLoading(false);
    }
  };

  const saveAddressOnly = async () => {
    const err = validateAddress();
    if (err) {
      setError(err);
      return;
    }
    setSavingAddress(true);
    setError('');
    try {
      const created = await auth.createAddress({
        label: addressLabel || 'Home',
        line1: form.shipping_line1,
        line2: form.shipping_line2 || undefined,
        city: form.shipping_city,
        state: form.shipping_state,
        pincode: form.shipping_pincode,
        phone: form.shipping_phone,
        is_default: addresses.length === 0,
      });
      const addrs = await auth.listAddresses();
      setAddresses(addrs);
      setSelectedAddressId(created.id);
      setUseNewAddress(false);
      setSuccess('Address saved.');
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to save address');
    } finally {
      setSavingAddress(false);
    }
  };

  const selectedAddr = addresses.find((a) => a.id === selectedAddressId);
  const showAddressForm = useNewAddress || addresses.length === 0;

  if (authLoading || !user) return <p className="page-msg">Please login to continue…</p>;
  if (!cart) return <p className="page-msg">Loading…</p>;
  if (!cart.items.length) {
    return (
      <p className="page-msg">
        Your cart is empty. <Link href="/">Continue shopping</Link>
      </p>
    );
  }

  return (
    <div className="checkout-layout">
      <div className="checkout-main">
        <h1>Checkout</h1>
        <div className="checkout-steps">
          <span className="step active">1. Address</span>
          <span className="step active">2. Payment</span>
        </div>

        {error && <div className="alert alert-error">{error}</div>}
        {success && <div className="alert alert-success">{success}</div>}

        <section className="checkout-section card">
          <h2>Delivery address</h2>
          {addresses.length > 0 && !showAddressForm && (
            <div className="address-list">
              {addresses.map((addr) => (
                <label
                  key={addr.id}
                  className={`address-card ${selectedAddressId === addr.id ? 'selected' : ''}`}
                >
                  <input
                    type="radio"
                    name="address"
                    checked={selectedAddressId === addr.id}
                    onChange={() => {
                      setSelectedAddressId(addr.id);
                      setUseNewAddress(false);
                    }}
                  />
                  <div className="address-body">
                    <div className="address-top">
                      <strong>{addr.label || 'Home'}</strong>
                      {addr.is_default && <span className="badge">Default</span>}
                      {selectedAddressId === addr.id && (
                        <span className="deliver-here">Deliver here</span>
                      )}
                    </div>
                    <p className="address-lines">
                      {addr.line1}{addr.line2 ? `, ${addr.line2}` : ''}<br />
                      {addr.city}, {addr.state} — {addr.pincode}<br />
                      {addr.phone}
                    </p>
                  </div>
                </label>
              ))}
              <button type="button" className="link-btn" onClick={() => setUseNewAddress(true)}>
                + Add a new address
              </button>
            </div>
          )}

          {showAddressForm && (
            <div className="checkout-form">
              {addresses.length > 0 && (
                <button type="button" className="link-btn" onClick={() => setUseNewAddress(false)}>
                  ← Use saved address
                </button>
              )}
              <label>Full name</label>
              <input name="shipping_name" required value={form.shipping_name} onChange={handleChange} />
              <label>Phone</label>
              <input name="shipping_phone" required value={form.shipping_phone} onChange={handleChange} />
              <label>Address line 1</label>
              <input name="shipping_line1" required value={form.shipping_line1} onChange={handleChange} />
              <label>City</label>
              <input name="shipping_city" required value={form.shipping_city} onChange={handleChange} />
              <label>State</label>
              <input name="shipping_state" required value={form.shipping_state} onChange={handleChange} />
              <label>Pincode</label>
              <input name="shipping_pincode" required value={form.shipping_pincode} onChange={handleChange} />
              <label className="checkbox-row">
                <input type="checkbox" checked={saveAddress} onChange={(e) => setSaveAddress(e.target.checked)} />
                Save for next orders
              </label>
              <button type="button" className="btn btn-outline" disabled={savingAddress} onClick={saveAddressOnly}>
                {savingAddress ? 'Saving…' : 'Save address'}
              </button>
            </div>
          )}
        </section>

        <section className="checkout-section card">
          <h2>Payment</h2>
          <div className="pay-option selected cod-only">
            <div>
              <strong>Cash on Delivery (COD)</strong>
              <p>Pay when your order is delivered. No online payment popup.</p>
            </div>
          </div>
        </section>
      </div>

      <aside className="checkout-summary card">
        <h2>Order summary</h2>
        {cart.items.map((item) => (
          <div key={`${item.product_id}-${item.sku_id}`} className="summary-row">
            <span>{item.product_name} × {item.quantity}</span>
            <span>{formatPrice(item.line_total)}</span>
          </div>
        ))}
        <div className="summary-total">
          <span>Amount payable</span>
          <strong>{formatPrice(cart.subtotal)}</strong>
        </div>
        {selectedAddr && !showAddressForm && (
          <p className="summary-addr">
            Deliver to: {selectedAddr.city} — {selectedAddr.pincode}
          </p>
        )}
        <button type="button" className="btn btn-place-order" disabled={loading} onClick={placeOrder}>
          {loading ? 'Placing order…' : 'Place order'}
        </button>
        <p className="summary-note">Cash on delivery · Pay {formatPrice(cart.subtotal)} when you receive the order</p>
      </aside>
    </div>
  );
}
