const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000/api/v1';
export const RAZORPAY_KEY_ID = process.env.NEXT_PUBLIC_RAZORPAY_KEY_ID || '';

export type Category = { id: string; slug: string; name: string; description?: string };
export type ProductSku = { id: string; label: string; price: number; currency: string };
export type Product = {
  id: string;
  slug: string;
  name: string;
  description?: string;
  category_slug: string;
  image_url?: string;
  skus: ProductSku[];
};
export type CartItem = {
  product_id: string;
  sku_id: string;
  product_name: string;
  unit_price: number;
  quantity: number;
  image_url?: string;
  line_total: number;
};
export type Cart = { cart_id: string; items: CartItem[]; subtotal: number; item_count: number };
export type User = { id: string; email: string; name?: string; role: string };
export type Address = {
  id: string;
  label: string | null;
  line1: string;
  line2: string | null;
  city: string;
  state: string;
  pincode: string;
  phone: string;
  is_default: boolean;
};
export type Order = {
  id: string;
  status: string;
  subtotal: number;
  currency: string;
  items: CartItem[];
  payment_method?: string;
  razorpay_order_id?: string;
  razorpay_key_id?: string;
  created_at: string;
};
export type CheckoutResponse = {
  order: Order;
  payment_method: string;
  razorpay_order_id?: string;
  razorpay_key_id?: string;
  amount: number;
  currency: string;
};

export type PaymentMethod = 'cod' | 'online';

export type CheckoutPayload = {
  payment_method?: PaymentMethod;
  address_id?: string;
  save_address?: boolean;
  address_label?: string;
  shipping_name?: string;
  shipping_phone?: string;
  shipping_line1?: string;
  shipping_line2?: string;
  shipping_city?: string;
  shipping_state?: string;
  shipping_pincode?: string;
};

function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('access_token');
}

export async function api<T>(
  path: string,
  options: RequestInit & { idempotencyKey?: string } = {},
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };
  const token = getToken();
  if (token) headers['Authorization'] = `Bearer ${token}`;
  if (options.idempotencyKey) headers['Idempotency-Key'] = options.idempotencyKey;

  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
    credentials: 'include',
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    const detail = err.detail;
    const msg = typeof detail === 'string' ? detail : Array.isArray(detail) ? detail.map((d: { msg?: string }) => d.msg).join(', ') : JSON.stringify(err);
    throw new Error(msg || res.statusText);
  }
  return res.json();
}

export const catalog = {
  categories: () => api<Category[]>('/catalog/categories'),
  products: (category?: string) =>
    api<{ items: Product[]; next_cursor?: string }>(
      `/catalog/products${category ? `?category=${category}` : ''}`,
    ),
  product: (slug: string) => api<Product>(`/catalog/products/${slug}`),
};

export const auth = {
  register: (email: string, password: string, name?: string) =>
    api<{ access_token: string; user: User }>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, name }),
    }),
  login: (email: string, password: string) =>
    api<{ access_token: string; user: User }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),
  me: () => api<User>('/auth/me'),
  updateProfile: (name: string) =>
    api<User>('/auth/me', { method: 'PATCH', body: JSON.stringify({ name }) }),
  listAddresses: () => api<Address[]>('/auth/addresses'),
  createAddress: (body: Omit<Address, 'id' | 'is_default'> & { is_default?: boolean }) =>
    api<Address>('/auth/addresses', { method: 'POST', body: JSON.stringify(body) }),
};

export const cart = {
  get: () => api<Cart>('/cart'),
  add: (product_id: string, sku_id: string, quantity: number) =>
    api<Cart>('/cart/items', {
      method: 'POST',
      body: JSON.stringify({ product_id, sku_id, quantity }),
    }),
  remove: (productId: string, skuId: string) =>
    api<Cart>(`/cart/items/${productId}/${skuId}`, { method: 'DELETE' }),
};

export const orders = {
  checkout: (payload: CheckoutPayload, idempotencyKey: string) =>
    api<CheckoutResponse>('/orders/checkout', {
      method: 'POST',
      body: JSON.stringify(payload),
      idempotencyKey,
    }),
  list: () => api<Order[]>('/orders'),
  get: (id: string) => api<Order>(`/orders/${id}`),
  mockPay: (id: string) => api<Order>(`/orders/${id}/mock-pay`, { method: 'POST' }),
};

export const payments = {
  verify: (body: {
    razorpay_order_id: string;
    razorpay_payment_id: string;
    razorpay_signature: string;
  }) =>
    api<{ order_id: string; status: string }>('/payments/verify', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
};

export function formatPrice(paise: number): string {
  return `₹${(paise / 100).toFixed(2)}`;
}

export function addressToShipping(name: string, addr: Address) {
  return {
    address_id: addr.id,
    shipping_name: name,
    shipping_phone: addr.phone,
    shipping_line1: addr.line1,
    shipping_line2: addr.line2 || '',
    shipping_city: addr.city,
    shipping_state: addr.state,
    shipping_pincode: addr.pincode,
  };
}
