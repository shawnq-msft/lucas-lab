"""Exercise the published summary as a reader, locally or at SITE_BASE."""
import functools
import http.server
import os
import threading
from pathlib import Path
from playwright.sync_api import sync_playwright

root = Path(__file__).resolve().parents[1]
base = os.environ.get('SITE_BASE')
server = None
if not base:
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(root))
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f'http://127.0.0.1:{server.server_port}/'
errors = []
try:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for width, height in [(1440, 1000), (390, 844)]:
            page = browser.new_page(viewport={'width': width, 'height': height}, device_scale_factor=1)
            page.on('pageerror', lambda e: errors.append(str(e)))
            response = page.goto(base, wait_until='networkidle')
            assert response.status == 200
            page.locator('a[href="school-admissions/"]').click()
            page.wait_for_load_state('networkidle')
            assert '小升初选校参考' in page.title()
            assert page.locator('[data-school]').count() == 6
            assert page.locator('details').evaluate('(e)=>e.open') is False
            page.locator('summary').click()
            assert page.locator('details').evaluate('(e)=>e.open') is True
            page.locator('nav a[href="#schools"]').click()
            assert page.url.endswith('#schools')
            assert page.locator('#schools').evaluate('(e)=>Math.abs(e.getBoundingClientRect().top)<100')
            assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'), 'horizontal overflow'
            assert not page.locator('img:not([alt])').count()
            out = os.environ.get('SCREENSHOT_DIR')
            if out:
                Path(out).mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(Path(out) / f'school-summary-{width}.png'), full_page=True)
            assert page.locator('#sources li').count() == 12
            page.locator('.page-end a').click()
            page.wait_for_load_state('networkidle')
            assert page.title().startswith('Lucas Lab')
            assert page.locator('h1').is_visible()
            assert page.locator('.entry-link[href="school-admissions/"]').count() == 1
            print(f'PASS summary navigation, details, citations and overflow at {width}x{height}')
            page.close()
        browser.close()
    assert not errors, errors
finally:
    if server: server.shutdown()
