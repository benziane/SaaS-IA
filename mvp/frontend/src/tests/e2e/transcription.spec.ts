/**
 * Transcription E2E Tests - Grade S++
 * End-to-end tests for transcription functionality
 */

import { expect, test } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

/* ========================================================================
   TEST SUITE
   ======================================================================== */

test.describe('Transcription Page', () => {
  test.beforeEach(async ({ page }) => {
    // TODO: Add authentication setup
    await page.goto('/transcription');
  });
  
  /* ========================================================================
     VISUAL TESTS
     ======================================================================== */
  
  test('should display transcription page', async ({ page }) => {
    // Check page title
    await expect(page.getByRole('heading', { name: /youtube transcriptions/i })).toBeVisible();
    
    // Check form elements
    await expect(page.getByLabel(/youtube video url/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /transcribe/i })).toBeVisible();
  });
  
  /* ========================================================================
     ACCESSIBILITY TESTS - Grade S++
     ======================================================================== */
  
  test('should not have accessibility violations', async ({ page }) => {
    const accessibilityScanResults = await new AxeBuilder({ page }).analyze();
    
    expect(accessibilityScanResults.violations).toEqual([]);
  });
  
  /* ========================================================================
     FORM VALIDATION TESTS
     ======================================================================== */
  
  test('should show validation error for empty URL', async ({ page }) => {
    // Click transcribe without filling form
    await page.getByRole('button', { name: /transcribe/i }).click();
    
    // Check for validation error
    await expect(page.getByText(/youtube url is required/i)).toBeVisible();
  });
  
  test('should show validation error for invalid URL', async ({ page }) => {
    // Fill invalid URL
    await page.getByLabel(/youtube video url/i).fill('not-a-url');
    await page.getByRole('button', { name: /transcribe/i }).click();
    
    // Check for validation error
    await expect(page.getByText(/invalid.*url/i)).toBeVisible();
  });
  
  test('should show validation error for non-YouTube URL', async ({ page }) => {
    // Fill non-YouTube URL
    await page.getByLabel(/youtube video url/i).fill('https://example.com');
    await page.getByRole('button', { name: /transcribe/i }).click();
    
    // Check for validation error
    await expect(page.getByText(/invalid youtube url/i)).toBeVisible();
  });
  
  /* ========================================================================
     TABLE TESTS
     ======================================================================== */
  
  test('should display transcriptions table', async ({ page }) => {
    // Check table headers
    await expect(page.getByRole('columnheader', { name: /video url/i })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: /status/i })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: /created/i })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: /confidence/i })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: /actions/i })).toBeVisible();
  });
  
  /* ========================================================================
     RESPONSIVE TESTS
     ======================================================================== */
  
  test('should be responsive on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Check form is still visible and usable
    await expect(page.getByRole('heading', { name: /youtube transcriptions/i })).toBeVisible();
    await expect(page.getByLabel(/youtube video url/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /transcribe/i })).toBeVisible();
  });
});

