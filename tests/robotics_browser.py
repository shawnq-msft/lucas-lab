"""Read-only roadmap navigation and responsive acceptance; no hardware claims."""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
base=os.environ.get('LAB_URL','http://127.0.0.1:8786/').rstrip('/')+'/'
with sync_playwright() as p:
    chrome=next((Path.home()/'.cache/ms-playwright').glob('*/chrome-linux64/chrome'))
    browser=p.chromium.launch(executable_path=str(chrome),args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1440,'height':1000});errors=[];failed=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('response',lambda r:failed.append(r.url) if r.status>=400 else None)
    page.goto(base);page.locator('a[href="robotics/"]').click()
    assert page.title()=='四足机器人路线 · Lucas Lab'
    assert page.locator('.stage').count()==3
    assert '视觉 + 语音' in page.locator('#stage-1').inner_text()
    assert 'RL' in page.locator('#stage-2').inner_text()
    assert '3DOF' in page.locator('#stage-3').inner_text()
    assert '尚未实测' in page.locator('.status').inner_text()
    for link in page.locator('.route-nav a').all():
        href=link.get_attribute('href');link.click();assert page.url.endswith(href)
        assert page.locator(href).evaluate('el => Math.abs(el.getBoundingClientRect().top)<100')
    for width in [320,390,1440]:
        page.set_viewport_size({'width':width,'height':1000})
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),width
    out=Path('verification');out.mkdir(exist_ok=True)
    page.evaluate('window.scrollTo(0,0)');page.screenshot(path=str(out/'robotics-desktop.png'),full_page=True)
    page.set_viewport_size({'width':390,'height':844});page.screenshot(path=str(out/'robotics-mobile.png'),full_page=True)
    page.emulate_media(media='print');assert page.locator('.stage:visible').count()==3
    assert not errors,errors
    assert not failed,failed
    browser.close()
print('Robot roadmap acceptance passed: home entry, stage order, anchors, 3 widths, print, no runtime/resource errors.')
