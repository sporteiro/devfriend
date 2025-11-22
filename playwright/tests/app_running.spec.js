const { test, expect } = require('@playwright/test');

const APP_URL = process.env.APP_URL || 'http://localhost:88';

test('la app carga correctamente', async ({ page }) => {
  console.log(`Testeando con PlayWright: ${APP_URL}`);
  await page.goto(APP_URL);

  await page.waitForTimeout(1000);
  await expect(page).toHaveTitle(/DevFriend/);

  await page.waitForTimeout(2000);
});
