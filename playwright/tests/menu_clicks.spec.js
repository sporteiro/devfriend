const { test, expect } = require('@playwright/test');

const APP_URL = process.env.APP_URL || 'http://localhost:88';

test('navegación por el menú verifica títulos', async ({ page }) => {
  await page.goto(APP_URL);

  // Mapeo de elementos del menú con los títulos esperados
  const menuItems = [
    { text: 'Notes', expectedTitle: 'Notes' },
    { text: 'Email', expectedTitle: 'Email' },
    { text: 'Repository', expectedTitle: 'Repository' },
    { text: 'Messages', expectedTitle: 'Messages' },
    { text: 'Credentials', expectedTitle: 'Credentials' }
  ];

  for (const { text, expectedTitle } of menuItems) {
    // Hacer click en el elemento del menú
    const menuItem = page.locator(`a:has-text("${text}")`);
    await menuItem.click();

    // Esperar a que la página cargue
    await page.waitForTimeout(500);

    // Verificar que el título sea el correcto
    const title = page.locator('.content-header h1');
    await expect(title).toHaveText(expectedTitle);

    console.log(`✓ Navegación a "${text}" - Título "${expectedTitle}" verificado`);
  }
});
