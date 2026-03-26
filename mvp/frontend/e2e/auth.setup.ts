import { test as setup } from '@playwright/test';
import path from 'path';

const authFile = path.join(__dirname, '..', '.playwright', 'auth.json');

setup('authenticate', async ({ page }) => {
  // Navigate to login
  await page.goto('/login');

  // Fill login form
  await page.fill('input[name="email"], input[type="email"]', 'demo@saas-ia.com');
  await page.fill('input[name="password"], input[type="password"]', 'Demo123!');

  // Submit
  await page.click('button[type="submit"]');

  // Wait for redirect to dashboard
  await page.waitForURL('**/dashboard', { timeout: 15000 });

  // Save auth state
  await page.context().storageState({ path: authFile });
});
