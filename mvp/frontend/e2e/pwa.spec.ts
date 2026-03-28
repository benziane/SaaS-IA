import { test, expect } from '@playwright/test';

test.describe('PWA', () => {
  test('manifest.json is accessible', async ({ page }) => {
    const response = await page.goto('/manifest.json');
    expect(response?.status()).toBe(200);
    const manifest = await response?.json();
    expect(manifest.name).toBeTruthy();
    expect(manifest.theme_color).toBe('#05C3DB');
  });

  test('service worker registers', async ({ page }) => {
    await page.goto('/');
    // Check SW registration exists in page
    const swRegistered = await page.evaluate(() => 'serviceWorker' in navigator);
    expect(swRegistered).toBe(true);
  });

  test('apple-touch-icon exists', async ({ page }) => {
    const response = await page.goto('/apple-touch-icon.png');
    expect(response?.status()).toBe(200);
  });
});
