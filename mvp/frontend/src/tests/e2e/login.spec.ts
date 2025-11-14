/**
 * Login E2E Tests - Grade S++
 * End-to-end tests for login functionality
 */

import { expect, test } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

/* ========================================================================
   TEST SUITE
   ======================================================================== */

test.describe('Login Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
  });
  
  /* ========================================================================
     VISUAL TESTS
     ======================================================================== */
  
  test('should display login form', async ({ page }) => {
    // Check page title
    await expect(page).toHaveTitle(/Login/);
    
    // Check form elements
    await expect(page.getByRole('heading', { name: /welcome to saas-ia/i })).toBeVisible();
    await expect(page.getByLabel(/email/i)).toBeVisible();
    await expect(page.getByLabel(/password/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /sign in/i })).toBeVisible();
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
  
  test('should show validation errors for empty fields', async ({ page }) => {
    // Click sign in without filling form
    await page.getByRole('button', { name: /sign in/i }).click();
    
    // Check for validation errors
    await expect(page.getByText(/email is required/i)).toBeVisible();
    await expect(page.getByText(/password is required/i)).toBeVisible();
  });
  
  test('should show error for invalid email', async ({ page }) => {
    // Fill invalid email
    await page.getByLabel(/email/i).fill('invalid-email');
    await page.getByLabel(/password/i).click(); // Trigger blur
    
    // Check for validation error
    await expect(page.getByText(/invalid email/i)).toBeVisible();
  });
  
  test('should show error for short password', async ({ page }) => {
    // Fill short password
    await page.getByLabel(/email/i).fill('test@example.com');
    await page.getByLabel(/password/i).fill('short');
    await page.getByLabel(/email/i).click(); // Trigger blur
    
    // Check for validation error
    await expect(page.getByText(/password must be at least/i)).toBeVisible();
  });
  
  /* ========================================================================
     FUNCTIONALITY TESTS
     ======================================================================== */
  
  test('should toggle password visibility', async ({ page }) => {
    const passwordInput = page.getByLabel(/^password$/i);
    const toggleButton = page.getByLabel(/show password/i);
    
    // Password should be hidden by default
    await expect(passwordInput).toHaveAttribute('type', 'password');
    
    // Click toggle button
    await toggleButton.click();
    
    // Password should be visible
    await expect(passwordInput).toHaveAttribute('type', 'text');
    
    // Click toggle button again
    await toggleButton.click();
    
    // Password should be hidden again
    await expect(passwordInput).toHaveAttribute('type', 'password');
  });
  
  test('should navigate to register page', async ({ page }) => {
    // Click create account link
    await page.getByRole('link', { name: /create an account/i }).click();
    
    // Should navigate to register page
    await expect(page).toHaveURL(/\/register/);
  });
  
  /* ========================================================================
     KEYBOARD NAVIGATION TESTS - Grade S++
     ======================================================================== */
  
  test('should support keyboard navigation', async ({ page }) => {
    // Tab through form elements
    await page.keyboard.press('Tab'); // Email
    await expect(page.getByLabel(/email/i)).toBeFocused();
    
    await page.keyboard.press('Tab'); // Password
    await expect(page.getByLabel(/^password$/i)).toBeFocused();
    
    await page.keyboard.press('Tab'); // Remember me checkbox
    await page.keyboard.press('Tab'); // Forgot password link
    await page.keyboard.press('Tab'); // Sign in button
    await expect(page.getByRole('button', { name: /sign in/i })).toBeFocused();
  });
  
  /* ========================================================================
     RESPONSIVE TESTS
     ======================================================================== */
  
  test('should be responsive on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Check form is still visible and usable
    await expect(page.getByRole('heading', { name: /welcome to saas-ia/i })).toBeVisible();
    await expect(page.getByLabel(/email/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /sign in/i })).toBeVisible();
  });
});

