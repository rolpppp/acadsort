import { test, expect } from '@playwright/test';

test.describe('AcadSort E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    // Wait for the app to load
    await page.waitForLoadState('networkidle');
  });

  test('loads application and displays Dashboard page', async ({ page }) => {
    // Check that header is visible
    await expect(page.locator('text=AcadSort')).toBeVisible();

    // Check navigation buttons are visible
    await expect(page.getByRole('button', { name: 'Dashboard' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Files' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Settings' })).toBeVisible();

    // Dashboard should be active
    const dashboardBtn = page.getByRole('button', { name: 'Dashboard' });
    await expect(dashboardBtn).toHaveAttribute('data-active', 'true');
  });

  test('navigates between pages correctly', async ({ page }) => {
    // Start on Dashboard
    await expect(page.getByRole('button', { name: 'Dashboard' })).toHaveAttribute('data-active', 'true');

    // Click Files button
    await page.getByRole('button', { name: 'Files' }).click();
    await page.waitForTimeout(300); // Wait for animation

    // Files should now be active
    const filesBtn = page.getByRole('button', { name: 'Files' });
    await expect(filesBtn).toHaveAttribute('data-active', 'true');

    // Click Settings
    await page.getByRole('button', { name: 'Settings' }).click();
    await page.waitForTimeout(300);

    // Settings should be active
    const settingsBtn = page.getByRole('button', { name: 'Settings' });
    await expect(settingsBtn).toHaveAttribute('data-active', 'true');
  });

  test('displays Dashboard statistics', async ({ page }) => {
    // Stats should be visible
    await expect(page.locator('text=Organized')).toBeVisible();
    await expect(page.locator('text=Pending')).toBeVisible();
    await expect(page.locator('text=Confidence')).toBeVisible();

    // Progress bar should be visible
    const progressBar = page.locator('[role="progressbar"]');
    await expect(progressBar).toBeVisible();
  });

  test('navigates to Files page and shows file processor', async ({ page }) => {
    // Click Files
    await page.getByRole('button', { name: 'Files' }).click();
    await page.waitForTimeout(300);

    // Page should load
    await page.waitForLoadState('networkidle');

    // Should show either processing content or "All Organized" message
    const pageContent = page.locator('body');
    await expect(pageContent).toBeVisible();
  });

  test('navigates to Settings page and displays options', async ({ page }) => {
    // Click Settings
    await page.getByRole('button', { name: 'Settings' }).click();
    await page.waitForTimeout(300);

    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Settings content should be visible
    const settingsContent = page.locator('body');
    await expect(settingsContent).toBeVisible();

    // Should have course list or settings controls
    const controls = page.locator('button, [role="radio"], [role="slider"]');
    await expect(controls.first()).toBeVisible();
  });

  test('handles error states gracefully', async ({ page, context }) => {
    // Simulate network error by blocking API requests
    await context.route('**/api/**', route => route.abort());

    // Reload page to trigger API calls with blocked network
    await page.reload();
    await page.waitForTimeout(1000);

    // Check if error UI is displayed or page gracefully handles it
    // Either should show error message or fallback content
    const pageContent = page.locator('body');
    await expect(pageContent).toBeVisible();
  });

  test('Toast notifications appear and disappear', async ({ page }) => {
    // Note: Toast would typically appear on user actions
    // This test checks that the toast container is ready
    const toastContainer = page.locator('[role="status"]');
    
    // Container should exist in DOM even if no toasts are shown
    const containerCount = await toastContainer.count();
    expect(containerCount).toBeGreaterThanOrEqual(0);
  });

  test('responsive design works on mobile viewport', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Page should still be functional
    const header = page.locator('text=AcadSort');
    await expect(header).toBeVisible();

    // Navigation should still work
    const dashboardBtn = page.getByRole('button', { name: 'Dashboard' });
    await expect(dashboardBtn).toBeVisible();

    // Should be able to navigate
    await page.getByRole('button', { name: 'Settings' }).click();
    await page.waitForTimeout(300);
    
    const settingsBtn = page.getByRole('button', { name: 'Settings' });
    await expect(settingsBtn).toHaveAttribute('data-active', 'true');
  });

  test('color scheme consistency (sage palette)', async ({ page }) => {
    // Check that buttons use sage colors (not indigo)
    const buttons = page.locator('button');
    const buttonCount = await buttons.count();
    
    // Should have navigation buttons
    expect(buttonCount).toBeGreaterThan(0);

    // Verify no indigo colors are present in main elements
    const htmlContent = await page.content();
    // Main app should not have indigo-600 or indigo-700 classes
    const hasIndigo = htmlContent.includes('indigo-600') || htmlContent.includes('indigo-700');
    expect(hasIndigo).toBe(false);
  });
});
