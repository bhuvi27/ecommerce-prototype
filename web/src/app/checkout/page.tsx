'use client';

import { useCallback, useEffect, useState } from 'react';
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
  dispatchCartUpdated,
} from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import { AddressSelector } from '@/components/AddressSelector';

const emptyForm = {
  shipping_name: '',
  shipping_phone: '',
  shipping_line1: '',
  shipping_line2: '',
  shipping_city: '',
  shipping_state: '',
  shipping_pincode: '',
};

export default function CheckoutPage() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
  const [cart, setCart] = useState<Cart | null>(null);
  const [addresses, setAddresses] = useState<Address[]>([]);
  const [addressesLoading, setAddressesLoading] = useState(true);
  const [addressesError, setAddressesError] = useState('');
  const [selectedAddressId, setSelectedAddressId] = useState<string | null>(null);
  const [showNewAddressForm, setShowNewAddressForm] = useState(false);
  const [saveAddress, setSaveAddress] = useState(true);
  const [addressLabel, setAddressLabel] = useState('Home');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);
  const [savingAddress, setSavingAddress] = useState(false);
  const [form, setForm] = useState(emptyForm);

  const loadAddresses = useCallback(async () => {
    setAddressesLoading(true);
    setAddressesError('');
    try {
      const addrs = await auth.listAddresses();
      const normalized = addrs.map((a) => ({ ...a, id: String(a.id) }));
      setAddresses(normalized);
      const def = normalized.find((a) => a.is_default) || normalized[0];
      if (def) {
        setSelectedAddressId(def.id);
        setShowNewAddressForm(false);
      } else {
        setShowNewAddressForm(true);
      }
    } catch (e: unknown) {
      setAddresses([]);
      setAddressesError(
        e instanceof Error
          ? e.message
          : 'Could not load saved addresses. Check you are logged in and the API is running.',
      );
      setShowNewAddressForm(true);
    } finally {
      setAddressesLoading(false);
    }
  }, []);

  useEffect(() => {
    if (authLoading) return;
    if (!user) {
      router.replace('/login?next=/checkout');
      return;
    }
    setForm((f) => ({ ...f, shipping_name: user.name || '' }));
    cartApi.get().then(setCart).catch((e) => setError(e.message));
    loadAddresses();
  }, [user, authLoading, router, loadAddresses]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm((f) => ({ ...f, [e.target.name]: e.target.value }));
  };

  const validateNewAddressForm = (): string | null => {
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
    if (!showNewAddressForm && selectedAddressId) {
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

    if (showNewAddressForm || addresses.length === 0) {
      const err = validateNewAddressForm();
      if (err) {
        setError(err);
        return;
      }
    } else if (!selectedAddressId) {
      setError('Please select a delivery address');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');
    try {
      const result = await orders.checkout(buildPayload(), uuidv4());
      if (result.order.status !== 'confirmed') {
        setError('Order was not confirmed. Please try again.');
        return;
      }
      dispatchCartUpdated();
      router.push(`/orders/view?id=${result.order.id}`);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Could not place order');
    } finally {
      setLoading(false);
    }
  };

  const saveAddressOnly = async () => {
    const err = validateNewAddressForm();
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
        line2: form.shipping_line2 || null,
        city: form.shipping_city,
        state: form.shipping_state,
        pincode: form.shipping_pincode,
        phone: form.shipping_phone,
        is_default: addresses.length === 0,
      });
      await loadAddresses();
      setSelectedAddressId(String(created.id));
      setShowNewAddressForm(false);
      setSuccess('Address saved. Select it above and place your order.');
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to save address');
    } finally {
      setSavingAddress(false);
    }
  };

  const selectSavedAddress = (id: string) => {
    setSelectedAddressId(id);
    setShowNewAddressForm(false);
    setError('');
  };

  const selectedAddr = addresses.find((a) => a.id === selectedAddressId);

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
          <span className="step active">1. Select address</span>
          <span className="step active">2. Payment</span>
        </div>

        {error && <div className="alert alert-error">{error}</div>}
        {success && <div className="alert alert-success">{success}</div>}

        <section className="checkout-section card">
          <h2>Select delivery address</h2>

          <AddressSelector
            addresses={addresses}
            selectedId={selectedAddressId}
            onSelect={selectSavedAddress}
            onAddNew={() => {
              setShowNewAddressForm(true);
              setError('');
            }}
            loading={addressesLoading}
            error={addressesError}
            onRetry={loadAddresses}
          />

          {showNewAddressForm && (
            <div className="checkout-form new-address-panel">
              <h3 className="form-section-title">
                {addresses.length > 0 ? 'Add new address' : 'Enter delivery address'}
              </h3>
              {addresses.length > 0 && (
                <button
                  type="button"
                  className="link-btn"
                  onClick={() => {
                    setShowNewAddressForm(false);
                    if (!selectedAddressId && addresses[0]) {
                      setSelectedAddressId(addresses[0].id);
                    }
                  }}
                >
                  ← Back to saved addresses
                </button>
              )}
              <label>Label (Home, Work…)</label>
              <input value={addressLabel} onChange={(e) => setAddressLabel(e.target.value)} placeholder="Home" />
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
                Save this address for next orders
              </label>
              <div className="checkout-actions">
                <button type="button" className="btn btn-outline" disabled={savingAddress} onClick={saveAddressOnly}>
                  {savingAddress ? 'Saving…' : 'Save address'}
                </button>
              </div>
            </div>
          )}
        </section>

        <section className="checkout-section card">
          <h2>Payment</h2>
          <div className="pay-option selected cod-only">
            <div>
              <strong>Cash on Delivery (COD)</strong>
              <p>Pay when your order is delivered.</p>
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

        {selectedAddr && !showNewAddressForm && (
          <div className="summary-selected-address">
            <p className="summary-selected-label">Delivering to</p>
            <p className="summary-selected-text">
              <strong>{selectedAddr.label || 'Home'}</strong>
              <br />
              {selectedAddr.line1}, {selectedAddr.city} — {selectedAddr.pincode}
              <br />
              {selectedAddr.phone}
            </p>
          </div>
        )}

        <button type="button" className="btn btn-place-order" disabled={loading || addressesLoading} onClick={placeOrder}>
          {loading ? 'Placing order…' : 'Place order'}
        </button>
        <p className="summary-note">Cash on delivery</p>
        <p className="checkout-footer-links">
          <Link href="/account/addresses">Manage addresses</Link>
        </p>
      </aside>
    </div>
  );
}
