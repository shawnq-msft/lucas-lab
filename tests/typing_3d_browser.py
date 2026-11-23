"""Exercise the actual public entry and every 3D mission (local or Pages)."""
import os
from playwright.sync_api import sync_playwright

base = os.environ.get('LAB_URL', 'http://127.0.0.1:8786/').rstrip('/') + '/'
with sync_playwright() as pw:
    browser = pw.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'])
    page = browser.new_page(viewport={'width': 960, 'height': 760})
    errors = []
    page.on('pageerror', lambda exc: errors.append(str(exc)))
    page.goto(base)
    page.locator('a[href="typing/3d/"]').click(timeout=5000)
    assert page.url.rstrip('/') == base + 'typing/3d'
    cards = page.locator('[data-scene]')
    assert cards.count() == 6
    for i in range(6):
        cards.nth(i).click()
        page.wait_for_function('document.querySelector("canvas").dataset.meshes > 10')
        word = page.locator('#word').inner_text()
        assert word
        entry = page.locator('#entry')
        entry.press_sequentially('~')
        assert not entry.input_value()
        entry.press_sequentially(word)
        page.wait_for_function('document.querySelector("#count").textContent === "1"')
        assert page.locator('#note').inner_text() == page.locator('#action').inner_text()
        page.locator('#back').click()
    page.set_viewport_size({'width': 390, 'height': 844})
    cards.first.click()
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    page.locator('#back').click()
    page.get_by_role('link', name='经典版与排行榜').click()
    assert page.locator('[data-mission]').count() == 6
    assert not errors, errors
    browser.close()
print('PASS: homepage → 3D, six WebGL missions, wrong keys + word completions, mobile width, classic return')
