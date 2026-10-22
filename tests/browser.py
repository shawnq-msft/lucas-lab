from pathlib import Path
from playwright.sync_api import sync_playwright
import json, os
ROOT=Path(__file__).resolve().parents[1]
BASE=os.environ.get('LAB_URL','http://127.0.0.1:8786/')
results=[]
def check(name,condition):
    assert condition,name
    results.append(name)
with sync_playwright() as pw:
    chrome=sorted((Path.home()/'.cache/ms-playwright').glob('chromium-*/chrome-linux*/chrome'))[-1]
    browser=pw.chromium.launch(executable_path=str(chrome),headless=True,args=['--no-sandbox'])
    context=browser.new_context(viewport={'width':1440,'height':1000},accept_downloads=True)
    page=context.new_page(); errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(BASE)
    check('homepage contains three working module links',all(page.locator(f'a[href="{s}/"]').count()>0 for s in ['practice','algorithms','tokamak']))
    page.locator('a[href="algorithms/"]').first.click()
    page.wait_for_selector('[data-topic]')
    check('six algorithm lessons',page.locator('[data-topic]').count()==6)
    for topic in ['array','stack','queue','binary','bubble','bfs']:
        page.locator(f'[data-topic="{topic}"]').click()
        before=page.locator('#caption').inner_text()
        page.locator('#next').click()
        check(topic+' step changes explanation',page.locator('#caption').inner_text()!=before)
        page.locator('#end').click()
        check(topic+' demo reaches end',page.locator('#next').is_disabled())
        page.locator('#reset').click()
        check(topic+' reset returns to start',page.locator('#prev').is_disabled())
        # Expected answers derived independently from visible exercise, not model answer.
        meta=page.locator('#exercise').get_attribute('data-meta');m=json.loads(meta)
        answer={'array':lambda:m['data'][m['index']], 'stack':lambda:m['data'][-1], 'queue':lambda:m['data'][0], 'binary':lambda:(m['lo']+m['hi'])//2,'bubble':lambda:0,'bfs':lambda:'C'}[topic]()
        options=page.locator('[data-answer]')
        values=[json.loads(v) for v in options.evaluate_all('(xs)=>xs.map(x=>x.dataset.answer)')]
        wrong=next(v for v in values if v!=answer)
        page.locator('[data-answer]').nth(values.index(wrong)).click()
        page.locator('#check').click()
        check(topic+' rejects wrong answer',page.locator('#feedback').get_attribute('data-status')=='wrong')
        page.locator('#hint').click();check(topic+' hint shown',bool(page.locator('#hintText').inner_text()))
        page.locator('[data-answer]').nth(values.index(answer)).click();page.locator('#check').click()
        check(topic+' accepts correct answer',page.locator('#feedback').get_attribute('data-status')=='correct')
    with page.expect_download() as dl:page.locator('#export').click()
    dest=ROOT/'verification/algorithm-progress.json';dest.parent.mkdir(exist_ok=True);dl.value.save_as(dest)
    data=json.loads(dest.read_text());check('six topic histories exported',len(data['records'])==6)
    check('first wrong answer retained',all(not r['attempts'][0]['correct'] and r['attempts'][-1]['correct'] for r in data['records'].values()))
    page.reload();page.wait_for_selector('[data-topic]');check('progress survives reload','6 / 6' in page.locator('#progress').inner_text())
    page.locator('[data-topic="array"]').click();before=page.locator('#prompt').inner_text();page.locator('#newExercise').click();check('new exercise changes input',page.locator('#prompt').inner_text()!=before)
    page.screenshot(path=str(ROOT/'verification/algorithms-desktop.png'),full_page=True)
    for route in ['', 'algorithms/']:
        page.set_viewport_size({'width':390,'height':844});page.goto(BASE+route);page.wait_for_timeout(300)
        check(route+' mobile fits viewport',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
        page.screenshot(path=str(ROOT/('verification/home-mobile.png' if not route else 'verification/algorithms-mobile.png')),full_page=True)
    page.set_viewport_size({'width':1440,'height':1000});page.goto(BASE);page.screenshot(path=str(ROOT/'verification/home-desktop.png'),full_page=True)
    page.locator('a[href="tokamak/"]').first.click();page.wait_for_function('!!window.tokamak')
    check('Tokamak six stages integrated',page.locator('[data-step]').count()==6)
    for i in range(6):
        page.locator(f'[data-step="{i}"]').click();check(f'Tokamak stage {i}',page.evaluate('window.tokamak.state.step')==i)
    page.locator('#field-mode').select_option('toroidal');path=page.locator('#field-line-0').get_attribute('d')
    page.locator('#field-mode').select_option('poloidal');check('Tokamak field geometry changes',path!=page.locator('#field-line-0').get_attribute('d'))
    page.locator('[data-part-button="cs"]').click();check('Tokamak component selection',page.locator('#part-name').inner_text()=='中心螺线管')
    check('Tokamak back navigation present',page.locator('a[href="../"]').count()>0)
    check('no JavaScript errors',not errors)
    browser.close()
report={'base':BASE,'passed':len(results),'checks':results,'errors':errors}
(ROOT/'verification/browser-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2))
