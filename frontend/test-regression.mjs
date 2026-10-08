import puppeteer from 'puppeteer';

(async () => {
  console.log('Starting regression test...');
  const browser = await puppeteer.launch({ headless: 'new' });
  const page = await browser.newPage();

  try {
    // 1. Start application fresh
    console.log('Navigating to http://localhost:3001/');
    await page.goto('http://localhost:3001/');
    await page.waitForSelector('input[name="name"]');

    // 2. Select Candidate and Full Stack Developer
    await page.type('input[name="name"]', 'KARTHICK');
    await page.type('input[name="role"]', 'Full Stack Developer');
    await page.keyboard.press('Enter');
    
    // 3. Upload Resume
    const fileInput = await page.$('input[type="file"]');
    await fileInput.uploadFile('E:\\interview\\meadia\\Dinesh_Resume.pdf');
    console.log('Uploaded resume, waiting for analysis...');

    // Wait for "Preview Match Analysis" to appear or the target
    await page.waitForFunction(() => {
      const el = document.body.innerText;
      return el.includes('Target:') && el.includes('Full Stack Developer');
    }, { timeout: 30000 });
    
    console.log('✅ PASS: Initial analysis shows Target: Full Stack Developer');

    // 6. Change dropdown to Frontend Developer
    console.log('Changing role to Frontend Developer...');
    const roleInput = await page.$('input[name="role"]');
    await roleInput.click({ clickCount: 3 });
    await roleInput.type('Frontend Developer');
    await page.keyboard.press('Enter');

    // 7. IMMEDIATELY check UI
    // It should NO LONGER say "Target: Full Stack Developer"
    await page.waitForTimeout(1000); // Wait for debounce (500ms) and UI update
    
    const pageText = await page.evaluate(() => document.body.innerText);
    if (!pageText.includes('Target: Full Stack Developer')) {
      console.log('✅ PASS: Stale Full Stack Developer result disappeared!');
    } else {
      console.log('❌ FAIL: Stale Full Stack Developer result is STILL visible!');
      throw new Error("Stale result visible");
    }

    // 8. Wait for re-analysis
    console.log('Waiting for Frontend Developer re-analysis...');
    await page.waitForFunction(() => {
      return document.body.innerText.includes('Target: Frontend Developer');
    }, { timeout: 30000 });
    
    console.log('✅ PASS: Re-analysis completed, Target: Frontend Developer shown.');

    // 9. Open Match Breakdown
    await page.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('button'));
      const btn = btns.find(b => b.innerText.includes('Preview Match Analysis') || b.innerText.includes('View Match Breakdown'));
      if (btn) btn.click();
    });
    
    await page.waitForFunction(() => {
      return document.body.innerText.includes('KARTHICK') && 
             document.body.innerText.includes('Role: Frontend Developer');
    }, { timeout: 5000 });
    
    console.log('✅ PASS: Modal shows Candidate: KARTHICK and Role: Frontend Developer.');
    
    console.log('\nAll regression steps PASSED!');
  } catch (err) {
    console.error('Test failed:', err);
  } finally {
    await browser.close();
  }
})();
