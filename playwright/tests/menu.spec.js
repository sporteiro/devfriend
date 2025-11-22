const { test, expect } = require('@playwright/test');

const APP_URL = process.env.APP_URL || 'http://localhost:88';

test('la app carga correctamente', async ({ page }) => {
  console.log(`Testeando con PlayWright: ${APP_URL}`);
  await page.goto(APP_URL);

  await page.waitForTimeout(1000);
  await expect(page).toHaveTitle(/DevFriend/);

  await page.waitForTimeout(2000);
});

test('verificar elementos del menú después de carga exitosa', async ({ page }) => {
  // Primero ejecutar el test de carga
  console.log(`Testeando con PlayWright: ${APP_URL}`);
  await page.goto(APP_URL);

  await page.waitForTimeout(1000);
  await expect(page).toHaveTitle(/DevFriend/);

  await page.waitForTimeout(2000);

  // Ahora verificar elementos del menú
  const menuItems = ['Notes', 'Email', 'Repository', 'Messages', 'Credentials'];

  for (const itemText of menuItems) {
    const menuItem = page.locator(`a:has-text("${itemText}")`);
    await expect(menuItem).toBeVisible();
    console.log(`✓ Elemento del menú "${itemText}" encontrado`);
  }

  // Verificar que el botón de Sign In existe
  const signInButton = page.locator('button:has-text("Sign In")');
  await expect(signInButton).toBeVisible();
  console.log('✓ Botón "Sign In" encontrado');

  // Verificar que hay al menos una nota en la lista
  const noteCards = page.locator('.note-card');
  await expect(noteCards.first()).toBeVisible();
  const noteCount = await noteCards.count();
  console.log(`✓ Se encontraron ${noteCount} notas en la lista`);
});
