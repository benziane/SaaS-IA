# E2E Visual Regression Tests

Playwright snapshot-based visual regression tests for the SaaS-IA frontend.

## Overview

Visual tests capture full-page screenshots and compare them against committed baseline `.png` files stored in `e2e/visual.spec.ts-snapshots/`. Any pixel difference beyond the configured threshold (`maxDiffPixelRatio: 0.05`) causes the test to fail.

Baselines **must be committed to git** — CI pulls them from the repo for comparison. Do not add `*.png` to `.gitignore`.

## First-Time Setup (Generating Baselines)

No baseline snapshots exist yet. The first test run will always fail with a "missing snapshot" error. Generate them locally first:

```bash
# From mvp/frontend/
npx playwright test e2e/visual.spec.ts --update-snapshots
```

This writes `.png` files into `e2e/visual.spec.ts-snapshots/`. Commit them:

```bash
git add e2e/visual.spec.ts-snapshots/
git commit -m "chore(e2e): add initial visual regression baselines"
```

## Running Visual Regression Tests

```bash
# Run visual tests only (requires dev server running on port 3002)
npx playwright test e2e/visual.spec.ts

# Run all e2e tests
npx playwright test

# Open interactive UI mode
npx playwright test --ui
```

The dev server starts automatically if not already running (configured via `webServer` in `playwright.config.ts`).

## Updating Baselines After Intentional UI Changes

When a UI change is intentional and the screenshots need to be refreshed:

```bash
# Regenerate all visual baselines
npx playwright test e2e/visual.spec.ts --update-snapshots

# Or regenerate a single snapshot by test name
npx playwright test e2e/visual.spec.ts -g "login page — light mode" --update-snapshots
```

Review the new screenshots before committing them.

## CI / GitHub Actions

The workflow at `.github/workflows/visual-regression.yml` runs automatically on pushes and pull requests to `main` that affect `mvp/frontend/`.

### First CI Run Behavior

If baselines have not been committed yet, the CI run will fail with missing snapshot errors. This is expected. Either:

1. Generate baselines locally and push them (recommended), or
2. Trigger `workflow_dispatch` with `update_snapshots=true` (see below).

### Updating Baselines in CI

To regenerate baselines from CI without checking out locally:

1. Go to **Actions** > **Visual Regression Tests** in GitHub.
2. Click **Run workflow**.
3. Set `update_snapshots` to `true`.
4. Run — the job will regenerate screenshots and auto-commit them back to the branch with the message `chore(ci): update visual regression baselines [skip ci]`.

The second CI run (on the next push) will then compare against the freshly committed baselines and pass.

## Snapshot Location

```
mvp/frontend/e2e/visual.spec.ts-snapshots/
  login-light-chromium-linux.png
  login-dark-chromium-linux.png
  dashboard-redirect-login-chromium-linux.png
  dashboard-or-redirect-chromium-linux.png
```

Note: Playwright appends the browser and OS to the filename (e.g. `-chromium-linux.png`). Baselines generated on macOS or Windows will have different suffixes and **will not match** CI (Linux). Always generate the "official" baselines either on Linux or via the CI `workflow_dispatch` flow above.

## Configuration Reference

| Setting | Value |
|---|---|
| Config file | `playwright.config.ts` |
| Snapshot dir | `e2e/visual.spec.ts-snapshots/` (Playwright default) |
| Base URL | `http://localhost:3002` (or `E2E_BASE_URL` env var) |
| Browser | Chromium only (Desktop Chrome) |
| Diff threshold | `threshold: 0.2`, `maxDiffPixelRatio: 0.05` |
| Animations | Disabled via injected CSS for stable screenshots |
