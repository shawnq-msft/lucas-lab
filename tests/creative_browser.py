"""Chromium acceptance: guide, filters, state, export, privacy and responsive layout."""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
base=os.environ.get('LAB_URL','http://127.0.0.1:8786/').rstrip('/')+'/'
checks=[]
def check(name,value):
    assert value,name
    checks.append(name)
with sync_playwright() as p:
    chrome=next((Path.home()/'.cache/ms-playwright').glob('*/chrome-linux64/chrome'))
    browser=p.chromium.launch(executable_path=str(chrome),args=['--no-sandbox'])
    context=browser.new_context(viewport={'width':1440,'height':1000},accept_downloads=True)
    page=context.new_page(); errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(base)
    page.locator('a[href="creative/"]').click()
    page.wait_for_selector('.contest')
    check('six tracks',page.locator('.contest').count()==6)
    check('school limitations visible','附件未读' in page.locator('[data-contest="school-ai"]').inner_text())
    check('future primary art directions','歌曲不向小学组开放' in page.locator('[data-contest="future-art"]').inner_text())
    page.locator('[data-filter="application"]').click()
    check('four application tracks',page.locator('.contest:visible').count()==4)
    check('filter pressed',page.locator('[data-filter="application"]').get_attribute('aria-pressed')=='true')
    page.locator('[data-filter="art"]').click()
    check('two art tracks',page.locator('.contest:visible').count()==2)
    check('filter count','2 / 6' in page.locator('#filterCount').inner_text())
    page.locator('[data-filter="all"]').click()
    check('all restored',page.locator('.contest:visible').count()==6)
    page.locator('[data-check="rules"]').check()
    page.locator('[data-check="baseline"]').check()
    check('progress actual','2 / 9' in page.locator('#progress').inner_text())
    page.reload();page.wait_for_selector('.contest')
    check('checklist persists',page.locator('[data-check="baseline"]').is_checked())
    check('namespace',page.evaluate('JSON.parse(localStorage.getItem("lucas-lab-creative-guide-v1")).baseline') is True)
    with page.expect_download() as info:page.locator('#exportPlan').click()
    download=info.value
    content=Path(download.path()).read_text()
    check('export honest checklist','[x]' in content and '[ ]' in content and '规则' in content)
    check('export has limits','不代表已报名' in content)
    page.locator('#resetPlan').click()
    check('reset','0 / 9' in page.locator('#progress').inner_text())
    page.reload();page.wait_for_selector('.contest')
    check('reset persists',not page.locator('[data-check="rules"]').is_checked())
    for link in page.locator('aside nav a').all():
        target=link.get_attribute('href')
        check('anchor '+target,page.locator(target).count()==1)
    Path('verification').mkdir(exist_ok=True)
    page.set_viewport_size({'width':1440,'height':1000});page.screenshot(path='verification/creative-desktop.png',full_page=True)
    for width in [320,390,1440]:
        page.set_viewport_size({'width':width,'height':1000})
        check('no page overflow '+str(width),page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
    page.set_viewport_size({'width':390,'height':844});page.screenshot(path='verification/creative-mobile.png',full_page=True)
    for i,table in enumerate(page.locator('.table-scroll').all()):
        check('mobile scroll cue '+str(i),'左右滑动' in table.evaluate('el => getComputedStyle(el,"::before").content'))
        table.evaluate('el => {el.scrollLeft=el.scrollWidth}')
        check('table right edge reachable '+str(i),table.evaluate('el => el.scrollLeft > 0 && el.scrollLeft+el.clientWidth>=el.scrollWidth-1'))
        table.evaluate('el => {el.scrollLeft=0}')
    page.evaluate('window.scrollTo(0,0)')
    page.screenshot(path='verification/creative-mobile-top.png')
    page.set_viewport_size({'width':1440,'height':1000})
    page.screenshot(path='verification/creative-desktop-top.png')
    page.emulate_media(media='print')
    check('print includes six tracks',page.locator('.contest:visible').count()==6)
    check('no runtime errors',not errors)
    context.close()
    # Blocked storage must not break reading or exporting.
    context=browser.new_context()
    context.add_init_script('Object.defineProperty(window, "localStorage", {get(){throw new Error("blocked")}})')
    page=context.new_page();page.goto(base+'creative/');page.wait_for_selector('.contest')
    check('storage denial explained','不可用' in page.locator('#storageStatus').inner_text())
    page.locator('[data-check="rules"]').check()
    check('storage denial still usable','1 / 9' in page.locator('#progress').inner_text())
    context.close()
    # Corrupted state must safely reset and remain readable.
    context=browser.new_context()
    context.add_init_script('localStorage.setItem("lucas-lab-creative-guide-v1", "null")')
    page=context.new_page();page.goto(base+'creative/');page.wait_for_selector('.contest')
    check('malformed state harmless','0 / 9' in page.locator('#progress').inner_text())
    browser.close()
print(f'{len(checks)} creative browser checks passed: '+', '.join(checks))
