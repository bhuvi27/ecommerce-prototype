'use client';

import { Address } from '@/lib/api';

type Props = {
  addresses: Address[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  onAddNew: () => void;
  loading?: boolean;
  error?: string;
  onRetry?: () => void;
};

export function AddressSelector({
  addresses,
  selectedId,
  onSelect,
  onAddNew,
  loading,
  error,
  onRetry,
}: Props) {
  if (loading) {
    return <p className="page-msg">Loading your saved addresses…</p>;
  }

  if (error) {
    return (
      <div className="alert alert-error">
        {error}
        {onRetry && (
          <button type="button" className="link-btn" style={{ marginTop: '0.5rem' }} onClick={onRetry}>
            Try again
          </button>
        )}
      </div>
    );
  }

  if (addresses.length === 0) {
    return (
      <p className="address-empty-hint">
        No saved address yet. Add one below — it will be saved for your next order.
      </p>
    );
  }

  return (
    <div className="address-list flipkart-addresses">
      <p className="section-hint">
        {addresses.length} saved address{addresses.length > 1 ? 'es' : ''} — tap to select
      </p>
      {addresses.map((addr) => {
        const id = String(addr.id);
        const selected = selectedId === id;
        return (
          <button
            key={id}
            type="button"
            className={`address-card address-card-btn ${selected ? 'selected' : ''}`}
            onClick={() => onSelect(id)}
          >
            <div className="address-body">
              <div className="address-top">
                <strong>{addr.label || 'Home'}</strong>
                {addr.is_default && <span className="badge">Default</span>}
                {selected && <span className="deliver-here">Deliver here</span>}
              </div>
              <p className="address-lines">
                {addr.line1}
                {addr.line2 ? `, ${addr.line2}` : ''}
                <br />
                {addr.city}, {addr.state} — {addr.pincode}
                <br />
                Phone: {addr.phone}
              </p>
            </div>
          </button>
        );
      })}
      <button type="button" className="address-card address-card-add" onClick={onAddNew}>
        <span className="add-icon">+</span>
        <span>Add a new address</span>
      </button>
    </div>
  );
}
