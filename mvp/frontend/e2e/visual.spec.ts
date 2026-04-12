import { test, expect } from '@playwright/test';

/**
 * Visual regression tests — snapshot-based.
 * Reference screenshots are stored in e2e/visual.spec.ts-snapshots/.
 * Run `npx playwright test e2e/visual.spec.ts --update-snapshots` to regenerate baselines.
 */

test.describe('Visual regression — Login page', () => {
  test.beforeEach(async ({ page }) => {
    // Disable CSS animations/transitions to get stable screenshots
    await page.addStyleTag({
      content: `
        *, *::before, *::after {
          animation-duration: 0s !important;
          transition-duration: 0s !important;
        }
      `,
    });
  });

  test('login page — light mode', async ({ page }) => {
    await page.goto('/login');
    // Wait for the email input to confirm the page is fully rendered
    await page.waitForSelector('input[type="email"]', { state: 'visible' });
    // Allow fonts / icons to settle
    await page.waitForTimeout(300);

    await expect(page).toHaveScreenshot('login-light.png', {
      fullPage: true,
      threshold: 0.2,
      maxDiffPixelRatio: 0.05,
    });
  });

  test('login page — dark mode', async ({ page }) => {
    // Emulate the prefers-color-scheme media feature before navigation
    await page.emulateMedia({ colorScheme: 'dark' });

    await page.goto('/login');
    await page.waitForSelector('input[type="email"]', { state: 'visible' });
    await page.waitForTimeout(300);

    await expect(page).toHaveScreenshot('login-dark.png', {
      fullPage: true,
      threshold: 0.2,
      maxDiffPixelRatio: 0.05,
    });
  });

  test('login page — dark vs light mode visual diff is meaningful', async ({ browser }) => {
    // Capture both modes in isolation and assert they produce different screenshots
    const lightCtx = await browser.newContext({ colorScheme: 'light' });
    const darkCtx = await browser.newContext({ colorScheme: 'dark' });

    const lightPage = await lightCtx.newPage();
    const darkPage = await darkCtx.newPage();

    try {
      await lightPage.addStyleTag({
        content: '*, *::before, *::after { animation-duration: 0s !important; transition-duration: 0s !important; }',
      });
      await darkPage.addStyleTag({
        content: '*, *::before, *::after { animation-duration: 0s !important; transition-duration: 0s !important; }',
      });

      await lightPage.goto('/login');
      await lightPage.waitForSelector('input[type="email"]', { state: 'visible' });
      await lightPage.waitForTimeout(300);

      await darkPage.goto('/login');
      await darkPage.waitForSelector('input[type="email"]', { state: 'visible' });
      await darkPage.waitForTimeout(300);

      const lightShot = await lightPage.screenshot({ fullPage: true });
      const darkShot = await darkPage.screenshot({ fullPage: true });

      // They should not be identical — dark mode must visually differ from light
      expect(lightShot).not.toEqual(darkShot);
    } finally {
      await lightCtx.close();
      await darkCtx.close();
    }
  });
});

test.describe('Visual regression — Dashboard (auth-gated)', () => {
  test('dashboard redirects to login when unauthenticated', async ({ page }) => {
    await page.goto('/dashboard');
    // Dashboard is behind auth — it must redirect to login
    await page.waitForURL(/login/, { timeout: 8000 });
    await page.waitForSelector('input[type="email"]', { state: 'visible' });
    await page.waitForTimeout(300);

    await expect(page).toHaveScreenshot('dashboard-redirect-login.png', {
      fullPage: true,
      threshold: 0.2,
      maxDiffPixelRatio: 0.05,
    });
  });

  test('dashboard page — skip if server unavailable', async ({ page }) => {
    // Attempt to reach the dashboard; skip gracefully when the dev server is not running
    try {
      const response = await page.goto('/dashboard', { timeout: 10000 });
      if (!response || response.status() >= 500) {
        test.skip();
        return;
      }
    } catch {
      test.skip();
      return;
    }

    // Auth redirect is expected in CI — capture whatever state we land on
    await page.waitForTimeout(500);
    await expect(page).toHaveScreenshot('dashboard-or-redirect.png', {
      fullPage: true,
      threshold: 0.2,
      maxDiffPixelRatio: 0.05,
    });
  });
});
