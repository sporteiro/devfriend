const { test, expect } = require('@playwright/test');

const APP_URL = process.env.APP_URL || 'http://localhost:88';

test.describe('Dark Mode Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(APP_URL);
  });

  test('complete dark mode functionality', async ({ page }) => {
    const appContainer = page.locator('.app-container');
    const darkModeToggle = page.locator('.dark-mode-toggle');

    // Check initial state
    const initialClass = await appContainer.getAttribute('class');
    console.log('Initial class:', initialClass);

    const isInitiallyDark = initialClass.includes('dark');
    console.log('Initial dark mode:', isInitiallyDark);

    // Toggle dark mode
    await darkModeToggle.click();
    await page.waitForTimeout(500);

    // Check state after first toggle
    const classAfterFirstToggle = await appContainer.getAttribute('class');
    const isDarkAfterFirstToggle = classAfterFirstToggle.includes('dark');
    console.log('After first toggle - Dark mode:', isDarkAfterFirstToggle);

    // Toggle again
    await darkModeToggle.click();
    await page.waitForTimeout(500);

    // Check state after second toggle
    const classAfterSecondToggle = await appContainer.getAttribute('class');
    const isDarkAfterSecondToggle = classAfterSecondToggle.includes('dark');
    console.log('After second toggle - Dark mode:', isDarkAfterSecondToggle);

    // Test multiple cycles
    for (let i = 0; i < 3; i++) {
      await darkModeToggle.click();
      await page.waitForTimeout(200);
      const currentClass = await appContainer.getAttribute('class');
      const isDark = currentClass.includes('dark');
      console.log(`Cycle ${i + 1}: Dark mode = ${isDark}`);
    }

    // Test with note operations
    const finalClassBeforeNote = await appContainer.getAttribute('class');
    const isDarkBeforeNote = finalClassBeforeNote.includes('dark');

    await page.fill('#note-content', 'Test note in current theme');
    await page.click('button:has-text("Save")');
    await page.waitForTimeout(1000);

    // Verify theme persists after note creation
    const classAfterNote = await appContainer.getAttribute('class');
    const isDarkAfterNote = classAfterNote.includes('dark');
    expect(isDarkAfterNote).toBe(isDarkBeforeNote);

    // Test navigation persistence
    const menuItems = ['Email', 'Repository', 'Messages', 'Credentials'];

    for (const menuItem of menuItems) {
      const menuLink = page.locator(`a:has-text("${menuItem}")`);
      if (await menuLink.isVisible()) {
        const classBeforeNav = await appContainer.getAttribute('class');
        const isDarkBeforeNav = classBeforeNav.includes('dark');

        await menuLink.click();
        await page.waitForTimeout(500);

        const classAfterNav = await appContainer.getAttribute('class');
        const isDarkAfterNav = classAfterNav.includes('dark');

        expect(isDarkAfterNav).toBe(isDarkBeforeNav);
        console.log(`Theme persisted on ${menuItem}: ${isDarkAfterNav}`);

        // Go back to Notes
        await page.locator('a:has-text("Notes")').click();
        await page.waitForTimeout(500);
      }
    }

    // Verify toggle button accessibility
    const ariaLabel = await darkModeToggle.getAttribute('aria-label');
    const title = await darkModeToggle.getAttribute('title');
    expect(ariaLabel).toBeTruthy();
    expect(title).toBeTruthy();

    console.log('All dark mode tests completed successfully');
  });
});
