import { chromium } from 'playwright';

const API = 'http://localhost:3000/api/v1';
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage();
const log = [];

async function getToken() {
  const email = `cod-ui-${Date.now()}@example.com`;
  let res = await fetch(`${API}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password: 'Test1234!', name: 'COD UI' }),
  });
  let data = await res.json();
  if (!data.access_token) {
    res = await fetch(`${API}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password: 'Test1234!' }),
    });
    data = await res.json();
  }
  return data.access_token;
}

try {
  const token = await getToken();
  if (!token) throw new Error('API not running on :3000');

  const prod = await (await fetch(`${API}/catalog/products/coconut-oil`)).json();
  const pid = prod.id;
  const sku = prod.skus[0].id;

  await fetch(`${API}/cart/items`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
    body: JSON.stringify({ product_id: pid, sku_id: sku, quantity: 1 }),
  });

  await fetch(`${API}/auth/addresses`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
    body: JSON.stringify({
      label: 'Home', line1: '12 MG Road', city: 'Mumbai', state: 'MH',
      pincode: '400001', phone: '9876543210', is_default: true,
    }),
  });

  await page.goto('http://localhost:3001', { waitUntil: 'domcontentloaded' });
  await page.evaluate((t) => localStorage.setItem('access_token', t), token);
  await page.goto('http://localhost:3001/checkout', { waitUntil: 'networkidle', timeout: 20000 });

  log.push(['url', page.url()]);
  log.push(['has Pay online option', await page.getByText('Pay online').count()]);
  log.push(['has Place order btn', await page.getByRole('button', { name: /^Place order$/i }).count()]);
  log.push(['has COD text', await page.getByText(/Cash on Delivery/i).count()]);

  await page.getByRole('button', { name: /^Place order$/i }).click();
  await page.waitForURL(/\/orders\/view/, { timeout: 15000 });
  log.push(['after click url', page.url()]);

  const body = await page.locator('body').innerText();
  log.push(['order confirmed on page', /confirmed|Thank you/i.test(body) ? 'yes' : 'no']);
  log.push(['razorpay popup text on page', body.includes('No appropriate payment') ? 'BAD' : 'ok']);
} catch (e) {
  log.push(['error', String(e)]);
}

await browser.close();
for (const row of log) console.log(row.join(': '));
