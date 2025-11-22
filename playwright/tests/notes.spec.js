const { test, expect } = require('@playwright/test');

const APP_URL = process.env.APP_URL || 'http://localhost:88';

test('complete notes CRUD operations', async ({ page }) => {
  // Setup dialog handler for delete confirmation
  page.on('dialog', async dialog => {
    await dialog.accept();
  });

  await page.goto(APP_URL);

  const testNote1 = 'Test Note Alpha ' + Date.now();
  const testNote2 = 'Test Note Beta ' + Date.now();
  const searchText = 'UniqueSearchText' + Date.now();

  // TEST 1: Create first note
  console.log('Creating first note...');
  const initialNotes = page.locator('.note-card');
  const initialCount = await initialNotes.count();

  await page.fill('#note-content', testNote1);
  const saveButton = page.locator('button:has-text("Save")');
  await expect(saveButton).not.toBeDisabled();
  await saveButton.click();
  await page.waitForTimeout(1000);

  const notesAfterFirstCreate = page.locator('.note-card');
  const countAfterFirstCreate = await notesAfterFirstCreate.count();
  expect(countAfterFirstCreate).toBe(initialCount + 1);

  const firstNote = page.locator(`.note-card:has-text("${testNote1}")`);
  await expect(firstNote).toBeVisible();

  // TEST 2: Create second note with searchable text
  console.log('Creating second note with search text...');
  await page.fill('#note-content', searchText);
  await expect(saveButton).not.toBeDisabled();
  await saveButton.click();
  await page.waitForTimeout(1000);

  const notesAfterSecondCreate = page.locator('.note-card');
  const countAfterSecondCreate = await notesAfterSecondCreate.count();
  expect(countAfterSecondCreate).toBe(initialCount + 2);

  // TEST 3: Search functionality
  console.log('Testing search...');
  await page.fill('#search-input', searchText);
  await page.waitForTimeout(1000);

  const searchResults = page.locator('.note-card');
  const searchCount = await searchResults.count();

  for (let i = 0; i < searchCount; i++) {
    const card = searchResults.nth(i);
    const content = await card.locator('.note-content').textContent();
    expect(content).toContain(searchText);
  }

  // Clear search
  await page.fill('#search-input', '');
  await page.waitForTimeout(500);

  // TEST 4: Edit first note
  console.log('Testing edit...');
  const editButton = firstNote.locator('.edit-btn');
  await editButton.click();
  await page.waitForTimeout(1000);

  const textarea = page.locator('#note-content');
  const textareaContent = await textarea.inputValue();
  expect(textareaContent).toContain(testNote1);

  const editedText = 'Edited Note ' + Date.now();
  await textarea.fill(editedText);

  const updateButton = page.locator('button:has-text("Update")');
  await expect(updateButton).not.toBeDisabled();
  await updateButton.click();
  await page.waitForTimeout(1000);

  const updatedNote = page.locator(`.note-card:has-text("${editedText}")`);
  await expect(updatedNote).toBeVisible();

  // TEST 5: Cancel edit on second note
  console.log('Testing cancel edit...');
  const secondNote = page.locator(`.note-card:has-text("${searchText}")`);
  const secondEditButton = secondNote.locator('.edit-btn');
  await secondEditButton.click();
  await page.waitForTimeout(1000);

  await textarea.fill('This should not be saved');
  const cancelButton = page.locator('button:has-text("Cancel")');
  await cancelButton.click();
  await page.waitForTimeout(500);

  await expect(saveButton).toBeDisabled();
  await expect(secondNote).toBeVisible();

  // TEST 6: Form validation
  console.log('Testing form validation...');
  await expect(saveButton).toBeDisabled();

  await textarea.fill('Valid content');
  await expect(saveButton).not.toBeDisabled();

  await textarea.fill('   ');
  await expect(saveButton).toBeDisabled();

  await textarea.fill('');
  await expect(saveButton).toBeDisabled();

  // TEST 7: Delete note
  console.log('Testing delete...');
  const notesBeforeDelete = page.locator('.note-card');
  const countBeforeDelete = await notesBeforeDelete.count();

  const deleteButton = secondNote.locator('.delete-btn');
  await deleteButton.click();
  await page.waitForTimeout(1000);

  const notesAfterDelete = page.locator('.note-card');
  const countAfterDelete = await notesAfterDelete.count();
  expect(countAfterDelete).toBe(countBeforeDelete - 1);

  const deletedNote = page.locator(`.note-card:has-text("${searchText}")`);
  await expect(deletedNote).not.toBeVisible();

  console.log('All CRUD operations completed successfully');
});

test('delete cancellation', async ({ page }) => {
  page.on('dialog', async dialog => {
    await dialog.dismiss();
  });

  await page.goto(APP_URL);

  const testNote = 'Note for cancel test ' + Date.now();

  await page.fill('#note-content', testNote);
  await page.click('button:has-text("Save")');
  await page.waitForTimeout(1000);

  const initialNotes = page.locator('.note-card');
  const initialCount = await initialNotes.count();

  const targetNote = page.locator(`.note-card:has-text("${testNote}")`);
  const deleteButton = targetNote.locator('.delete-btn');

  await deleteButton.click();
  await page.waitForTimeout(1000);

  const notesAfterCancel = page.locator('.note-card');
  const countAfterCancel = await notesAfterCancel.count();

  expect(countAfterCancel).toBe(initialCount);
  await expect(targetNote).toBeVisible();

  console.log('Delete cancellation test passed');
});
