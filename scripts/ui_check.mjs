import { chromium } from 'playwright';

const API = 'http://localhost:3000/api/v1';
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage();
const log = [];

async function apiLogin(email, password) {
  const res = await fetch(`${API}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password, name: 'UI Test' }),
  });
  let data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const loginRes = await fetch(`${API}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    data = await loginRes.json();
  }
  return data.access_token;
}

try {
  const email = `ui-test-${Date.now()}@example.com`;
  const token = await apiLogin(email, 'Test1234!');
  if (!token) throw new Error('API login failed — is API running on :3000?');

  await page.goto('http://localhost:3001', { waitUntil: 'domcontentloaded' });
  await page.evaluate((t) => localStorage.setItem('access_token', t), token);

  await page.goto('http://localhost:3001/account/addresses', { waitUntil: 'networkidle', timeout: 20000 });
  log.push(['addresses url', page.url()]);
  log.push(['Add & save address btn', await page.getByRole('button', { name: /Add & save address/i }).count()]);

  await page.goto('http://localhost:3001/checkout', { waitUntil: 'networkidle', timeout: 20000 });
  log.push(['checkout url', page.url()]);
  log.push(['test payment banner', await page.locator('.test-pay-banner').count()]);

  const addNew = await page.getByText('+ Add new address').count();
  log.push(['has Add new address option', addNew]);
  if (addNew) {
    await page.getByText('+ Add new address').click();
    await page.waitForTimeout(500);
  }
  log.push(['Save address button', await page.getByRole('button', { name: /^Save address$/i }).count()]);
  log.push(['Place order & pay button', await page.getByRole('button', { name: /Place order & pay/i }).count()]);

  const bodyText = await page.locator('body').innerText();
  log.push(['page mentions Save address', bodyText.includes('Save address') ? 'yes' : 'no']);
  log.push(['page mentions test mode', /Test mode|no real money/i.test(bodyText) ? 'yes' : 'no']);
} catch (e) {
  log.push(['error', String(e)]);
}

await browser.close();
for (const row of log) console.log(row.join(': '));
