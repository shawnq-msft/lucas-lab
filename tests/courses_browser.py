"""Chromium acceptance. Serve repository root; override base via LAB_URL."""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
from test_courses import URLS

BASE = os.environ.get('LAB_URL', 'http://127.0.0.1:8786/').rstrip('/') + '/courses/'
checks = []
def check(name, value):
    assert value, name
    checks.append(name)

with sync_playwright() as p:
    cached = sorted((Path.home() / '.cache/ms-playwright').glob('*/chrome-linux64/chrome'))
    browser = p.chromium.launch(
        executable_path=str(cached[-1]) if cached else None,
        args=['--no-sandbox'],
    )
    page = browser.new_page(viewport={'width': 1440, 'height': 1000})
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    response = page.goto(BASE)
    check('course URL returns 200', response.status == 200)
    check('six visible cards', page.locator('.course-card:visible').count() == 6)
    for key, url in URLS.items():
        link = page.locator(f'#{key} a.original-link')
        check(f'exact external URL {key}', link.get_attribute('href') == url)
        check(f'new tab {key}', link.get_attribute('target') == '_blank')
    page.locator('#category').select_option('hardware')
    check('hardware filter', page.locator('.course-card:visible').count() == 3)
    page.locator('#difficulty').select_option('2')
    check('combined filters', page.locator('.course-card:visible').count() == 1 and page.locator('#esp32').is_visible())
    page.locator('#category').select_option('outdoor')
    check('empty state', page.locator('.course-card:visible').count() == 0 and page.locator('#empty').is_visible())
    check('live count', '0 / 6' in page.locator('#result-count').inner_text())
    page.locator('#reset-filters').focus(); page.keyboard.press('Enter')
    check('keyboard reset', page.locator('.course-card:visible').count() == 6)
    page.locator('#category').focus(); page.keyboard.press('h'); page.keyboard.press('Enter')
    check('native filter keyboard focus', page.locator('#category').evaluate('(el) => el === document.activeElement'))
    page.locator('#category').select_option('outdoor')
    page.emulate_media(media='print')
    check('print includes filtered-out cards', page.locator('.course-card:visible').count() == 6)
    check('print hides controls', not page.locator('#filters').is_visible())
    check('print retains prompts', all(page.locator(f'#{key} .prompts').is_visible() for key in URLS))
    page.emulate_media(media='screen')
    check('screen filter restored after print', page.locator('.course-card:visible').count() == 1)
    page.locator('a[href="#esp32"]').first.click()
    check('route reveals filtered destination', page.locator('#esp32').is_visible() and page.locator('.course-card:visible').count() == 6)
    expected = {
        'all': {'all': 6, '1': 4, '2': 1, '3': 1},
        'hardware': {'all': 3, '1': 2, '2': 1, '3': 0},
        'network': {'all': 2, '1': 1, '2': 0, '3': 1},
        'outdoor': {'all': 1, '1': 1, '2': 0, '3': 0},
    }
    for category, levels in expected.items():
        for difficulty, count in levels.items():
            page.locator('#category').select_option(category)
            page.locator('#difficulty').select_option(difficulty)
            check(f'filter matrix {category}/{difficulty}', page.locator('.course-card:visible').count() == count)
    page.locator('#reset-filters').click()
    page.locator('#category').focus(); page.keyboard.press('ArrowDown'); page.keyboard.press('Enter')
    check('keyboard changes native category filter', page.locator('#category').input_value() == 'hardware' and page.locator('.course-card:visible').count() == 3)
    page.locator('#reset-filters').click()
    page.goto(BASE)
    page.keyboard.press('Tab'); page.keyboard.press('Enter')
    check('skip link keyboard navigation', page.evaluate('location.hash') == '#catalog')
    page.emulate_media(reduced_motion='reduce')
    check('reduced motion disables smooth scrolling', page.evaluate('getComputedStyle(document.documentElement).scrollBehavior') == 'auto')
    for width in (320, 390, 768, 1440):
        page.set_viewport_size({'width': width, 'height': 900})
        check(f'no horizontal overflow {width}', page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
        check(f'cards fit {width}', page.locator('.course-card').evaluate_all('(cards) => cards.every(c => c.getBoundingClientRect().right <= innerWidth)'))
    check('no runtime errors', not errors)
    context = browser.new_context(java_script_enabled=False, viewport={'width': 390, 'height': 844})
    fallback = context.new_page(); fallback.goto(BASE)
    check('no-JS six cards', fallback.locator('.course-card:visible').count() == 6)
    check('no-JS controls hidden', not fallback.locator('#filters').is_visible())
    for key, url in URLS.items():
        check(f'no-JS original link {key}', fallback.locator(f'#{key} a.original-link').get_attribute('href') == url)
    fallback.emulate_media(media='print')
    check('no-JS print six cards', fallback.locator('.course-card:visible').count() == 6)
    browser.close()
print(f'{len(checks)} course browser checks passed: ' + ', '.join(checks))
