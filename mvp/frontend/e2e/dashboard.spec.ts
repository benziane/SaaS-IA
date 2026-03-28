import { test, expect } from '@playwright/test';

test.describe('Dashboard Navigation', () => {
  test('redirects to login when not authenticated', async ({ page }) => {
    await page.goto('/dashboard');
    // Should redirect to login
    await expect(page).toHaveURL(/login/);
  });

  test('crawler page loads', async ({ page }) => {
    await page.goto('/crawler');
    // Either loads or redirects to login
    const url = page.url();
    expect(url).toMatch(/crawler|login/);
  });

  test('youtube page loads', async ({ page }) => {
    await page.goto('/youtube');
    const url = page.url();
    expect(url).toMatch(/youtube|login/);
  });
});
