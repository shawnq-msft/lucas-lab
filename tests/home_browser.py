"""Explore homepage acceptance. Run against local HTTP or LAB_URL on Pages."""
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = os.environ.get('LAB_URL', 'http://127.0.0.1:8786/').rstrip('/') + '/'
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'verification'
EXPECTED = {'practice/', 'algorithms/', 'tokamak/', 'typing/', 'computer/', 'mali/', 'creative/', 'camp101/', 'school-admissions/', 'robotics/', 'courses/'}
COUNTS = {'all': 11, 'code': 4, 'science': 3, 'contests': 3, 'family': 1}

with sync_playwright() as p:
    cached = sorted((Path.home() / '.cache/ms-playwright').glob('*/chrome-linux64/chrome'))
    launch = {'args': ['--no-sandbox']}
    if cached:
        launch['executable_path'] = str(cached[-1])
    browser = p.chromium.launch(**launch)
    context = browser.new_context(viewport={'width': 1440, 'height': 1000})
    page = context.new_page()
    errors, failures = [], []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.on('response', lambda response: failures.append((response.status, response.url)) if response.status >= 400 else None)
    page.goto(BASE)
    page.wait_for_function("document.querySelector('#search').disabled === false")
    assert page.locator('.entry:visible').count() == 11
    original = page.locator('.entry-link').evaluate_all('(links) => links.map(link => link.getAttribute("href"))')
    assert len(original) == 11 and set(original) == EXPECTED
    for category, count in COUNTS.items():
        button = page.locator(f'[data-filter="{category}"]')
        button.click()
        assert button.get_attribute('aria-pressed') == 'true'
        assert page.locator('.entry:visible').count() == count, category
        if category != 'all':
            assert page.locator(f'.entry:not([data-category="{category}"]):visible').count() == 0
        assert f'{count} / 11' in page.locator('#resultCount').inner_text()
        assert button.locator('[data-count]').inner_text() == str(count)
    page.locator('#resetFilters').click()
    page.locator('#search').fill('ｐＹｔｈｏｎ')
    assert page.locator('.entry:visible').count() >= 1
    page.locator('#resetFilters').click()
    page.locator('[data-filter="science"]').click()
    page.locator('#search').fill('机器人 RL')
    assert page.locator('.entry:visible').count() == 1
    assert page.locator('.entry:visible .entry-link').get_attribute('href') == 'robotics/'
    page.locator('[data-filter="code"]').click()
    assert page.locator('.entry:visible').count() == 0
    assert page.locator('#emptyState').is_visible()
    page.locator('#showAll').click()
    assert page.locator('.entry:visible').count() == 11
    assert page.locator('#search').input_value() == ''
    assert page.locator('#search').evaluate('el => el === document.activeElement')
    page.locator('#search').fill('zz没有这个探索zz')
    assert page.locator('.entry:visible').count() == 0
    page.locator('#resetFilters').click()
    page.locator('[data-filter="family"]').focus()
    page.keyboard.press('Space')
    assert page.locator('.entry:visible').count() == 1
    page.locator('[data-filter="science"]').focus()
    page.keyboard.press('Enter')
    assert page.locator('.entry:visible').count() == 3
    page.locator('#resetFilters').click()
    assert page.locator('.entry-link').evaluate_all('(links) => links.map(link => link.getAttribute("href"))') == original
    # Check every unchanged destination; do not claim these requests exercise app runtimes.
    for href in original:
        response = context.request.get(BASE + href)
        assert response.status == 200, (href, response.status)
    images = page.locator('.entry img')
    assert images.count() == 6
    for image in images.all():
        image.scroll_into_view_if_needed()
        image.evaluate('img => img.loading = "eager"')
        image.evaluate('img => img.decode()')
        assert image.evaluate('img => img.naturalWidth === 1200 && img.naturalHeight === 800')
    for details in page.locator('.entry details').all():
        details.locator('summary').focus()
        page.keyboard.press('Enter')
        assert details.get_attribute('open') is not None
    measurements = []
    for width in [320, 390, 768, 1024, 1440]:
        page.set_viewport_size({'width': width, 'height': 1000})
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), width
        assert page.locator('.entry:visible').count() == 11
        assert page.locator('.entry').evaluate_all('(cards) => cards.every(card => card.getClientRects().length === 1)'), width
        for card in page.locator('.entry').all():
            assert card.evaluate('el => el.scrollWidth <= el.clientWidth + 1'), (width, card.inner_text())
        columns = page.locator('.catalog').evaluate('el => getComputedStyle(el).columnCount')
        assert int(columns) == (1 if width < 641 else 2 if width <= 1100 else 3), (width, columns)
        measurements.append({'width': width, 'columns': int(columns), 'cards': 11, 'overflow': False})
    for details in page.locator('.entry details').all():
        details.evaluate('el => el.open = false')
    OUT.mkdir(exist_ok=True)
    for name, width, height in [('desktop', 1440, 1000), ('mobile', 390, 844), ('narrow', 320, 844)]:
        page.set_viewport_size({'width': width, 'height': height})
        page.evaluate('document.activeElement?.blur(); window.scrollTo(0, 0)')
        if name == 'mobile':
            heading = page.locator('.entry h2').first.bounding_box()
            assert heading['y'] + heading['height'] <= height, 'Show a complete first activity title in the mobile viewport'
        page.screenshot(path=str(OUT / f'home-{name}.png'), full_page=True)
        page.screenshot(path=str(OUT / f'home-{name}-top.png'))
        for control in page.locator('.filters button, input, .entry summary, .entry-link').all():
            assert control.bounding_box()['height'] >= 44, (name, control.inner_text())
    page.emulate_media(reduced_motion='reduce')
    assert page.evaluate('matchMedia("(prefers-reduced-motion: reduce)").matches')
    assert page.locator('.entry, button, input').evaluate_all('(els) => els.every(el => { const s = getComputedStyle(el); return s.animationName === "none" && s.transitionDuration === "0s"; })')
    page.locator('[data-filter="science"]').click()
    page.emulate_media(media='print')
    assert page.locator('.entry:visible').count() == 11
    assert page.locator('.browse').is_hidden()
    assert page.locator('.entry details p').evaluate_all('(els) => els.every(el => el.checkVisibility())'), 'Print includes closed details content'
    page.set_viewport_size({'width': 1440, 'height': 1000})
    page.evaluate('''() => {
      window.printChecks = [];
      addEventListener('beforeprint', () => printChecks.push([...document.querySelectorAll('.entry details p')].every(el => el.checkVisibility())));
      addEventListener('afterprint', () => printChecks.push([...document.querySelectorAll('.entry details')].every(el => !el.open)));
    }''')
    page.pdf(path=str(OUT / 'home-print.pdf'), format='A4', print_background=True)
    assert page.evaluate('window.printChecks') == [True, True], 'Print expands all details, then restores screen state'
    assert not errors, errors
    assert not failures, failures
    assert context.cookies() == []
    assert page.evaluate('localStorage.length') == 0
    context.close()
    # Tab reaches the skip link and Enter moves focus into the catalog.
    context = browser.new_context()
    page = context.new_page()
    page.goto(BASE)
    page.keyboard.press('Tab')
    assert page.locator('.skip-link').evaluate('el => document.activeElement === el')
    page.keyboard.press('Enter')
    assert page.locator('#catalog').evaluate('el => document.activeElement === el')
    context.close()
    context = browser.new_context(java_script_enabled=False, viewport={'width': 390, 'height': 844})
    page = context.new_page()
    page.goto(BASE)
    assert page.locator('.entry:visible').count() == 11
    assert page.locator('noscript').is_visible()
    assert page.locator('[data-filter="all"]').is_disabled()
    assert page.locator('#search').is_disabled()
    assert page.locator('.entry-link').count() == 11
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    page.screenshot(path=str(OUT / 'home-no-js.png'))
    page.emulate_media(media='print')
    assert page.locator('.entry:visible').count() == 11
    assert page.locator('.entry details p').evaluate_all('(els) => els.every(el => el.checkVisibility())')
    context.close()
    browser.close()
    (OUT / 'home-acceptance.json').write_text(json.dumps({'base': BASE, 'destinations': sorted(EXPECTED), 'counts': COUNTS, 'decoded_images': 6, 'viewports': measurements, 'checks': ['combined-search', 'empty/reset', 'keyboard', 'expanded-details', 'reduced-motion', 'print-all', 'no-JS', 'no-storage-writes'], 'console_errors': errors, 'http_failures': failures}, ensure_ascii=False, indent=2))
print('Homepage acceptance passed: all 11 links; counts 11/4/3/3/1; combined search/reset/empty; keyboard; 6 decoded images; 320/390/768/1024/1440; print; reduced motion; no-JS; no storage writes.')
