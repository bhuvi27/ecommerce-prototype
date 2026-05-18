const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000/api/v1';

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
export type Order = {
  id: string;
  status: string;
  subtotal: number;
  currency: string;
  items: CartItem[];
  razorpay_order_id?: string;
  razorpay_key_id?: string;
  created_at: string;
};
export type CheckoutResponse = {
  order: Order;
  razorpay_order_id: string;
  razorpay_key_id: string;
  amount: number;
  currency: string;
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
  checkout: (shipping: Record<string, string>, idempotencyKey: string) =>
    api<CheckoutResponse>('/orders/checkout', {
      method: 'POST',
      body: JSON.stringify(shipping),
      idempotencyKey,
    }),
  list: () => api<Order[]>('/orders'),
  get: (id: string) => api<Order>(`/orders/${id}`),
  mockPay: (id: string) => api<Order>(`/orders/${id}/mock-pay`, { method: 'POST' }),
};

export function formatPrice(paise: number): string {
  return `₹${(paise / 100).toFixed(2)}`;
}
