import { test, expect } from '@playwright/test';

/**
 * Comprehensive E2E tests for all 17 SaaS-IA pages.
 *
 * Covers:
 *  - Page load smoke tests (no 5xx, not blank, no unhandled error)
 *  - Auth flow (login, register, redirect when unauthenticated)
 *  - Navigation (sidebar, command palette)
 *  - Dashboard (stat cards, quick actions)
 *  - Transcription (form elements)
 *  - YouTube Studio (6 tabs)
 *  - Chat (conversation UI)
 *  - Compare (compare interface)
 *  - Pipelines (pipeline list)
 *  - Knowledge Base (knowledge list)
 *  - AI Agents (agents list)
 *  - Sentiment (sentiment analysis)
 *  - Web Crawler (crawl interface with tabs)
 *  - Costs (cost tracker)
 *  - Modules (module list)
 *  - API Docs (API keys)
 *  - Workspaces (workspace management)
 *  - Profile (profile settings)
 *  - Billing (plan and billing)
 *  - Backend API health
 */

// ---------------------------------------------------------------------------
// All 16 dashboard pages + transcription/debug = 17 authenticated pages
// ---------------------------------------------------------------------------
const PAGES = [
  { path: '/dashboard', title: 'Dashboard', expectText: ['Dashboard', 'Quick Actions'] },
  { path: '/transcription', title: 'Transcription', expectText: ['Transcription'] },
  { path: '/transcription/debug', title: 'Transcription Debug', expectText: ['Debug', 'Test'] },
  { path: '/chat', title: 'Chat', expectText: ['Chat', 'conversation'] },
  { path: '/compare', title: 'Compare', expectText: ['Compare'] },
  { path: '/pipelines', title: 'Pipelines', expectText: ['Pipeline'] },
  { path: '/knowledge', title: 'Knowledge', expectText: ['Knowledge'] },
  { path: '/agents', title: 'Agents', expectText: ['Agent'] },
  { path: '/sentiment', title: 'Sentiment', expectText: ['Sentiment'] },
  { path: '/crawler', title: 'Crawler', expectText: ['Crawler'] },
  { path: '/youtube', title: 'YouTube Studio', expectText: ['YouTube'] },
  { path: '/costs', title: 'Costs', expectText: ['Cost'] },
  { path: '/modules', title: 'Modules', expectText: ['Module'] },
  { path: '/api-docs', title: 'API Docs', expectText: ['API'] },
  { path: '/workspaces', title: 'Workspaces', expectText: ['Workspace'] },
  { path: '/profile', title: 'Profile', expectText: ['Profile'] },
  { path: '/billing', title: 'Billing', expectText: ['Plan', 'Billing'] },
];

// ===================================================================
// 1. PAGE LOAD SMOKE TESTS
// ===================================================================

test.describe('Page Load Tests', () => {
  for (const pg of PAGES) {
    test(`${pg.title} page loads at ${pg.path}`, async ({ page }) => {
      const response = await page.goto(pg.path);

      // Must not return a server error
      expect(response?.status()).toBeLessThan(500);

      // Wait for content to render
      await page.waitForLoadState('networkidle');

      // Page body should not be blank
      const body = await page.textContent('body');
      expect(body).toBeTruthy();
      expect(body!.length).toBeGreaterThan(50);

      // Should not show an unhandled Next.js error overlay
      const errorVisible = await page
        .locator('text=Application error')
        .isVisible()
        .catch(() => false);
      expect(errorVisible).toBeFalsy();
    });
  }
});

// ===================================================================
// 2. AUTH FLOW
// ===================================================================

test.describe('Auth Flow', () => {
  test('login page loads with email and password fields', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('networkidle');

    // Email field
    await expect(page.locator('input[type="email"]')).toBeVisible();

    // Password field
    await expect(page.locator('#password')).toBeVisible();

    // Submit button
    await expect(page.locator('button[type="submit"]')).toBeVisible();

    // Page header text
    await expect(page.locator('text=Welcome to SaaS-IA')).toBeVisible();

    // Register link
    await expect(page.locator('text=Create an account')).toBeVisible();
  });

  test('login page has remember me checkbox', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('networkidle');

    await expect(page.locator('text=Remember me')).toBeVisible();
    await expect(page.locator('text=Forgot Password?')).toBeVisible();
  });

  test('login page has password visibility toggle', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('networkidle');

    const toggleBtn = page.locator('button[aria-label="Show password"]');
    await expect(toggleBtn).toBeVisible();

    // Click to show password
    await toggleBtn.click();
    await expect(page.locator('#password')).toHaveAttribute('type', 'text');

    // Click to hide
    const hideBtn = page.locator('button[aria-label="Hide password"]');
    await hideBtn.click();
    await expect(page.locator('#password')).toHaveAttribute('type', 'password');
  });

  test('register page loads with all form fields', async ({ page }) => {
    await page.goto('/register');
    await page.waitForLoadState('networkidle');

    // Header
    await expect(page.locator('text=Create Account')).toBeVisible();

    // Email input
    await expect(page.locator('input[type="email"]')).toBeVisible();

    // Password inputs
    await expect(page.locator('#password')).toBeVisible();
    await expect(page.locator('#confirmPassword')).toBeVisible();

    // Terms checkbox
    await expect(page.locator('text=Terms & Conditions')).toBeVisible();

    // Submit button (should be disabled by default -- terms not accepted)
    const submitBtn = page.locator('button[type="submit"]');
    await expect(submitBtn).toBeVisible();
    await expect(submitBtn).toBeDisabled();

    // Login link
    await expect(page.locator('text=Sign in instead')).toBeVisible();
  });

  test('register submit button enables after accepting terms', async ({ page }) => {
    await page.goto('/register');
    await page.waitForLoadState('networkidle');

    const submitBtn = page.locator('button[type="submit"]');
    await expect(submitBtn).toBeDisabled();

    // Accept terms
    await page.locator('input[aria-label="Accept terms and conditions"]').check();
    await expect(submitBtn).toBeEnabled();
  });

  test('unauthenticated user redirected to login', async ({ page }) => {
    // Clear any auth state
    await page.context().clearCookies();
    await page.evaluate(() => localStorage.clear());

    await page.goto('/dashboard');
    await page.waitForURL('**/login**', { timeout: 10000 });
  });
});

// ===================================================================
// 3. NAVIGATION
// ===================================================================

test.describe('Navigation', () => {
  test('sidebar menu is visible on dashboard', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // Should have a navigation region
    const nav = page.locator('nav, [class*="nav"], [role="navigation"]');
    await expect(nav.first()).toBeVisible();
  });

  test('sidebar contains links to all major modules', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    const body = await page.textContent('body');

    // Check that key navigation labels are present
    const expectedLabels = [
      'Dashboard',
      'Transcription',
      'Chat',
      'Compare',
      'Pipelines',
      'Knowledge',
      'Agents',
      'Sentiment',
      'Crawler',
      'Modules',
      'Workspaces',
      'Profile',
      'Billing',
    ];

    for (const label of expectedLabels) {
      expect(body).toContain(label);
    }
  });

  test('command palette opens with Ctrl+K', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    await page.keyboard.press('Control+k');

    // Command palette / search dialog should appear
    const dialog = page.locator('[role="dialog"], [class*="Dialog"]');
    await expect(dialog.first()).toBeVisible({ timeout: 3000 });
  });
});

// ===================================================================
// 4. DASHBOARD
// ===================================================================

test.describe('Dashboard', () => {
  test('shows welcome banner', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    const body = await page.textContent('body');
    // Welcome banner should contain a greeting
    const hasGreeting =
      body!.includes('Good morning') ||
      body!.includes('Good afternoon') ||
      body!.includes('Good evening');
    expect(hasGreeting).toBeTruthy();
  });

  test('shows stat cards', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // Should show cards (MUI Card components)
    const cards = page.locator('[class*="MuiCard-root"]');
    const count = await cards.count();
    expect(count).toBeGreaterThan(2);
  });

  test('shows quick actions section', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    await expect(page.locator('text=Quick Actions')).toBeVisible();

    // Quick action labels
    const body = await page.textContent('body');
    expect(body).toContain('Transcribe');
    expect(body).toContain('Chat AI');
    expect(body).toContain('Pipeline');
    expect(body).toContain('Knowledge');
  });

  test('shows active modules section', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    await expect(page.locator('text=Active Modules')).toBeVisible();
  });

  test('shows platform usage charts', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    await expect(page.locator('text=Platform Usage')).toBeVisible();
    await expect(page.locator('text=Weekly Activity')).toBeVisible();
    await expect(page.locator('text=Status Distribution')).toBeVisible();
  });

  test('shows recent activity feed', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    await expect(page.locator('text=Recent Activity')).toBeVisible();
  });
});

// ===================================================================
// 5. TRANSCRIPTION
// ===================================================================

test.describe('Transcription', () => {
  test('shows transcription form with URL/upload inputs', async ({ page }) => {
    await page.goto('/transcription');
    await page.waitForLoadState('networkidle');

    // Should have input fields (URL / text / file)
    const inputs = page.locator('input[type="text"], input[type="url"], textarea');
    const count = await inputs.count();
    expect(count).toBeGreaterThan(0);
  });

  test('shows transcription tabs', async ({ page }) => {
    await page.goto('/transcription');
    await page.waitForLoadState('networkidle');

    const tabs = page.locator('[role="tab"]');
    const count = await tabs.count();
    expect(count).toBeGreaterThanOrEqual(2);
  });

  test('page title is visible', async ({ page }) => {
    await page.goto('/transcription');
    await page.waitForLoadState('networkidle');

    const body = await page.textContent('body');
    expect(body).toContain('Transcription');
  });
});

// ===================================================================
// 6. TRANSCRIPTION DEBUG
// ===================================================================

test.describe('Transcription Debug', () => {
  test('debug page loads', async ({ page }) => {
    const response = await page.goto('/transcription/debug');
    expect(response?.status()).toBeLessThan(500);

    await page.waitForLoadState('networkidle');

    const body = await page.textContent('body');
    expect(body!.length).toBeGreaterThan(50);
  });
});

// ===================================================================
// 7. YOUTUBE STUDIO
// ===================================================================

test.describe('YouTube Studio', () => {
  test('shows page title and description', async ({ page }) => {
    await page.goto('/youtube');
    await page.waitForLoadState('networkidle');

    await expect(page.locator('text=YouTube Studio')).toBeVisible();
    await expect(page.locator('text=Smart transcription')).toBeVisible();
  });

  test('shows 6 tabs', async ({ page }) => {
    await page.goto('/youtube');
    await page.waitForLoadState('networkidle');

    const tabs = page.locator('[role="tab"]');
    const count = await tabs.count();
    expect(count).toBe(6);

    // Verify tab labels
    await expect(tabs.nth(0)).toContainText('Smart Transcribe');
    await expect(tabs.nth(1)).toContainText('Metadata');
    await expect(tabs.nth(2)).toContainText('Playlist Bulk');
    await expect(tabs.nth(3)).toContainText('Auto-Chapter');
    await expect(tabs.nth(4)).toContainText('Live Stream');
    await expect(tabs.nth(5)).toContainText('Video Analysis');
  });

  test('has URL input and language selector', async ({ page }) => {
    await page.goto('/youtube');
    await page.waitForLoadState('networkidle');

    // URL input
    const urlInput = page.locator('input').filter({ hasText: '' }).first();
    await expect(urlInput).toBeVisible();

    // Language selector with options
    const body = await page.textContent('body');
    expect(body).toContain('Language');
    expect(body).toContain('Auto-detect');
  });

  test('Smart Transcribe tab shows description and button', async ({ page }) => {
    await page.goto('/youtube');
    await page.waitForLoadState('networkidle');

    // Default tab (Smart Transcribe)
    await expect(page.locator('text=Automatically uses the best provider')).toBeVisible();

    const btn = page.locator('button:has-text("Smart Transcribe")');
    await expect(btn).toBeVisible();
    // Button disabled when no URL
    await expect(btn).toBeDisabled();
  });

  test('tab switching works', async ({ page }) => {
    await page.goto('/youtube');
    await page.waitForLoadState('networkidle');

    // Click Metadata tab
    await page.locator('[role="tab"]:has-text("Metadata")').click();
    await expect(page.locator('button:has-text("Extract Metadata")')).toBeVisible();

    // Click Playlist tab
    await page.locator('[role="tab"]:has-text("Playlist Bulk")').click();
    await expect(page.locator('button:has-text("Transcribe Playlist")')).toBeVisible();

    // Click Auto-Chapter tab
    await page.locator('[role="tab"]:has-text("Auto-Chapter")').click();
    await expect(page.locator('button:has-text("Auto-Chapter")')).toBeVisible();

    // Click Live Stream tab
    await page.locator('[role="tab"]:has-text("Live Stream")').click();
    await expect(page.locator('button:has-text("Check Status")')).toBeVisible();
    await expect(page.locator('button:has-text("Capture Stream")')).toBeVisible();

    // Click Video Analysis tab
    await page.locator('[role="tab"]:has-text("Video Analysis")').click();
    await expect(page.locator('button:has-text("Analyze Video Frames")')).toBeVisible();
  });
});

// ===================================================================
// 8. CHAT
// ===================================================================

test.describe('Chat', () => {
  test('chat page loads with conversation interface', async ({ page }) => {
    await page.goto('/chat');
    await page.waitForLoadState('networkidle');

    const body = await page.textContent('body');
    // Should contain chat-related text
    const hasChatContent =
      body!.includes('Chat') ||
      body!.includes('conversation') ||
      body!.includes('Conversation') ||
      body!.includes('message');
    expect(hasChatContent).toBeTruthy();
  });
});

// ===================================================================
// 9. COMPARE
// ===================================================================

test.describe('Compare', () => {
  test('compare page loads', async ({ page }) => {
    await page.goto('/compare');
    await page.waitForLoadState('networkidle');

    const body = await page.textContent('body');
    expect(body).toContain('Compare');
  });
});

// ===================================================================
// 10. PIPELINES
// ===================================================================

test.describe('Pipelines', () => {
  test('pipelines page loads', async ({ page }) => {
    await page.goto('/pipelines');
    await page.waitForLoadState('networkidle');

    const body = await page.textContent('body');
    expect(body).toContain('Pipeline');
  });
});

// ===================================================================
// 11. KNOWLEDGE BASE
// ===================================================================

test.describe('Knowledge Base', () => {
  test('knowledge page loads', async ({ page }) => {
    await page.goto('/knowledge');
    await page.waitForLoadState('networkidle');

    const body = await page.textContent('body');
    expect(body).toContain('Knowledge');
  });
});

// ===================================================================
// 12. AI AGENTS
// ===================================================================

test.describe('AI Agents', () => {
  test('agents page loads', async ({ page }) => {
    await page.goto('/agents');
    await page.waitForLoadState('networkidle');

    const body = await page.textContent('body');
    expect(body).toContain('Agent');
  });
});

// ===================================================================
// 13. SENTIMENT
// ===================================================================

test.describe('Sentiment', () => {
  test('sentiment page loads', async ({ page }) => {
    await page.goto('/sentiment');
    await page.waitForLoadState('networkidle');

    const body = await page.textContent('body');
    expect(body).toContain('Sentiment');
  });
});

// ===================================================================
// 14. WEB CRAWLER
// ===================================================================

test.describe('Web Crawler', () => {
  test('crawler page loads with tabs', async ({ page }) => {
    await page.goto('/crawler');
    await page.waitForLoadState('networkidle');

    const body = await page.textContent('body');
    expect(body).toContain('Crawler');

    // Should have tabs
    const tabs = page.locator('[role="tab"]');
    const count = await tabs.count();
    expect(count).toBeGreaterThanOrEqual(2);
  });

  test('crawler has URL input', async ({ page }) => {
    await page.goto('/crawler');
    await page.waitForLoadState('networkidle');

    const inputs = page.locator('input[type="text"], input[type="url"]');
    const count = await inputs.count();
    expect(count).toBeGreaterThan(0);
  });
});

// ===================================================================
// 15. COST TRACKER
// ===================================================================

test.describe('Cost Tracker', () => {
  test('costs page loads', async ({ page }) => {
    await page.goto('/costs');
    await page.waitForLoadState('networkidle');

    const body = await page.textContent('body');
    expect(body).toContain('Cost');
  });
});

// ===================================================================
// 16. MODULES
// ===================================================================

test.describe('Modules', () => {
  test('modules page loads', async ({ page }) => {
    await page.goto('/modules');
    await page.waitForLoadState('networkidle');

    const body = await page.textContent('body');
    expect(body).toContain('Module');
  });
});

// ===================================================================
// 17. API DOCS
// ===================================================================

test.describe('API Docs', () => {
  test('api-docs page loads', async ({ page }) => {
    await page.goto('/api-docs');
    await page.waitForLoadState('networkidle');

    const body = await page.textContent('body');
    expect(body).toContain('API');
  });
});

// ===================================================================
// 18. WORKSPACES
// ===================================================================

test.describe('Workspaces', () => {
  test('workspaces page loads', async ({ page }) => {
    await page.goto('/workspaces');
    await page.waitForLoadState('networkidle');

    const body = await page.textContent('body');
    expect(body).toContain('Workspace');
  });
});

// ===================================================================
// 19. PROFILE
// ===================================================================

test.describe('Profile', () => {
  test('profile page loads', async ({ page }) => {
    await page.goto('/profile');
    await page.waitForLoadState('networkidle');

    const body = await page.textContent('body');
    expect(body).toContain('Profile');
  });
});

// ===================================================================
// 20. BILLING
// ===================================================================

test.describe('Billing', () => {
  test('billing page loads', async ({ page }) => {
    await page.goto('/billing');
    await page.waitForLoadState('networkidle');

    const body = await page.textContent('body');
    const hasBillingContent = body!.includes('Plan') || body!.includes('Billing');
    expect(hasBillingContent).toBeTruthy();
  });
});

// ===================================================================
// 21. BACKEND API HEALTH
// ===================================================================

test.describe('API Response', () => {
  test('health endpoint responds', async ({ request }) => {
    const response = await request.get('http://localhost:8004/health');
    expect(response.ok()).toBeTruthy();
  });

  test('modules endpoint responds', async ({ request }) => {
    const response = await request.get('http://localhost:8004/api/modules');
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(Array.isArray(data)).toBeTruthy();
    expect(data.length).toBeGreaterThan(5);
  });
});
