"""Real Chromium speedometer acceptance. No injected game state or scores.
Run: uv run --with playwright python tests/typing_speed_browser.py
"""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = os.environ.get('LAB_URL', 'http://127.0.0.1:8786/').rstrip('/') + '/typing/'
checks = []

def check(name, condition):
    assert condition, name
    checks.append(name)

with sync_playwright() as pw:
    chrome = next((Path.home() / '.cache/ms-playwright').glob('*/chrome-linux64/chrome'))
    browser = pw.chromium.launch(executable_path=str(chrome), args=['--no-sandbox'])
    page = browser.new_page(viewport={'width': 1280, 'height': 1000})
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.clock.install()
    page.goto(BASE)
    page.locator('#speech').uncheck()
    page.locator('#effects').uncheck()
    field = page.locator('#entry')
    gauge = page.locator('#speedGauge')

    def start(scene):
        if page.locator('#back').is_visible():
            page.locator('#back').click()
        page.locator('#speed').fill('60')
        page.locator(f'[data-mission="{scene}"]').click()

    def hit():
        text = page.locator('#target').get_attribute('data-text')
        field.press_sequentially(text[len(field.input_value())])

    def raw():
        return float(gauge.get_attribute('data-hpm'))

    for scene in ['supply', 'defense', 'assault']:
        start(scene)
        check(scene + ' visible gauge', gauge.is_visible())
        check(scene + ' actual zero not configured speed', raw() == 0 and page.locator('#hpm').inner_text() == '0')
        check(scene + ' units and threshold', 'HITS/MIN' in gauge.inner_text() and '30' in page.locator('#speedThreshold').inner_text())
        field.press('~')  # starts real mission timer; wrong keys never earn hits
        page.clock.run_for(6000)
        hit()
        before = page.locator('#speedNeedle').get_attribute('style')
        page.clock.run_for(64)
        moving = float(page.locator('#hpm').inner_text())
        check(scene + ' real input raw average', 9 < raw() < 11)
        check(scene + ' interpolated visible value', 0 < moving < raw())
        check(scene + ' moving indicator', before != page.locator('#speedNeedle').get_attribute('style'))
        page.clock.run_for(900)
        check(scene + ' settles to actual speed', abs(float(page.locator('#hpm').inner_text()) - raw()) <= 1)
        old_count = page.locator('#correctCount').inner_text()
        prefix = field.input_value()
        field.press('~')
        check(scene + ' wrong key does not advance or earn hits', old_count == page.locator('#correctCount').inner_text() and prefix == field.input_value())
        while int(page.locator('#correctCount').inner_text()) < 18:
            hit()
        page.clock.run_for(400)
        check(scene + ' actual threshold boost', raw() > 30 and 'is-boosting' in gauge.get_attribute('class'))
        check(scene + ' threshold status', '30' in page.locator('#speedStatus').inner_text() and '短语' in page.locator('#speedStatus').inner_text())
        check(scene + ' arena boost', 'speed-boost' in page.locator('#arena').get_attribute('class'))
        animation = page.locator('.speed-trails').evaluate('(e)=>e.getAnimations()[0]?.currentTime')
        page.clock.run_for(150)
        later = page.locator('.speed-trails').evaluate('(e)=>e.getAnimations()[0]?.currentTime')
        check(scene + ' effects persist across renders', animation is not None and later > animation)
        check(scene + ' no per-frame live announcements', gauge.get_attribute('aria-live') == 'off' and page.locator('#speedStatus').get_attribute('role') != 'status')
        page.set_viewport_size({'width': 320, 'height': 900})
        page.clock.run_for(100)
        check(scene + ' 320px no overflow', page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
        check(scene + ' gauge fits mobile', gauge.evaluate('(e)=>e.getBoundingClientRect().right <= innerWidth'))
        page.emulate_media(reduced_motion='reduce')
        hit()
        page.clock.run_for(32)
        check(scene + ' reduced motion direct speed', abs(float(page.locator('#hpm').inner_text()) - raw()) <= 1)
        check(scene + ' reduced motion disables trails', page.locator('.speed-trails').evaluate('(e)=>getComputedStyle(e).animationName') == 'none')
        page.emulate_media(reduced_motion='no-preference')
        page.set_viewport_size({'width': 1280, 'height': 1000})
    page.clock.fast_forward(61000)
    check('final gauge settles to actual result', abs(float(page.locator('#hpm').inner_text()) - raw()) <= 1)
    check('rules explain actual threshold', '30' in page.locator('.rules').text_content() and 'HITS/MIN' in page.locator('.rules').text_content())
    check('legacy WPM retained', page.locator('#wpm').count() == 1)
    check('no JavaScript errors', not errors)
    browser.close()
print(f'{len(checks)} speed browser checks passed: ' + ', '.join(checks))
