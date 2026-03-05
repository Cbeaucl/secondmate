import { test, expect } from '@playwright/test';

test('measure typing performance in sql editor with large datagrid', async ({ page }) => {
  // Navigate to the app
  await page.goto('http://localhost:5173');

  // Find the run button and wait for it to be ready
  const runButton = page.locator('button', { hasText: 'Run' });

  // By default, the query is "SELECT * FROM user.sales.transactions LIMIT 100;"
  // Change the default query to something that returns a lot of rows (1000 rows)
  const editorInput = page.locator('.monaco-editor textarea');
  await editorInput.press('ControlOrMeta+A');
  await editorInput.press('Backspace');
  await editorInput.type('SELECT * FROM user.ipgeo LIMIT 1000;');

  // Click run and wait for the query to finish
  // This will render the DataGrid with 1000 rows
  await runButton.click();

  // Wait for the rows to appear in the DataGrid, wait for at least 100 rows to make sure it's rendered
  await expect(page.locator('span', { hasText: '1000 rows retrieved' })).toBeVisible({ timeout: 15000 });
  await expect(page.locator('tbody tr').first()).toBeVisible({ timeout: 15000 });

  // Let the DOM settle
  await page.waitForTimeout(500);

  // Measure the time it takes to type a 50-character string, repeatedly 3 times
  for (let i = 0; i < 3; i++) {
    const startTime = Date.now();
    await editorInput.type('SELECT * FROM very_long_table_name_to_test_typing_speed;', { delay: 10 });
    const endTime = Date.now();
    const typingTime = endTime - startTime;
    console.log(`Typing run ${i + 1} took ${typingTime}ms`);
    // clear the input
    await editorInput.press('ControlOrMeta+A');
    await editorInput.press('Backspace');
  }
});