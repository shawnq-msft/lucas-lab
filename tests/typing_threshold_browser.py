"""Real keystrokes verify speed-gated sentences, never injected model state."""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
BASE=os.environ.get('LAB_URL','http://127.0.0.1:8786/').rstrip('/')+'/typing/'
checks=0
with sync_playwright() as pw:
    chrome=next((Path.home()/'.cache/ms-playwright').glob('*/chrome-linux64/chrome'))
    browser=pw.chromium.launch(executable_path=str(chrome),args=['--no-sandbox'])
    for scene in ['supply','defense','assault']:
        page=browser.new_page();page.clock.install()
        # Repeatable short targets; only RNG is fixed, never scores or game state.
        page.add_init_script('crypto.getRandomValues = a => { a.fill(0); return a; }')
        page.goto(BASE)
        page.locator('#speed').fill('5');page.locator('#speed').dispatch_event('input')
        page.locator(f'[data-mission="{scene}"]').click();field=page.locator('#entry')
        for _ in range(3):
            target=page.locator('#target').get_attribute('data-text')
            assert ' ' not in target and not page.locator('.vehicle.formation').count(),(scene,target)
            for ch in target:
                field.press_sequentially(ch);page.clock.run_for(2500)
        assert int(page.locator('#completed').inner_text())==3
        assert ' ' not in page.locator('#target').get_attribute('data-text')
        checks+=1
        page.locator('#restart').click()
        for _ in range(3):field.press_sequentially(page.locator('#target').get_attribute('data-text'))
        assert page.locator('.vehicle.formation').count()>0 if scene=='defense' else ' ' in page.locator('#target').get_attribute('data-text')
        checks+=1;page.close()
    browser.close()
print(f'{checks} speed-threshold browser checks passed (slow word-only and fast phrase unlock in all scenes)')
