"""Run the real Python worker in Chromium, including failures and record export."""
from pathlib import Path
import json, os, sys
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'sources/practice'))
from test_engine import SOLUTIONS
BASE=os.environ.get('LAB_URL','http://127.0.0.1:8786/')
results=[]
def check(name,condition):
    assert condition,name
    results.append(name)
with sync_playwright() as pw:
    chrome=sorted((Path.home()/'.cache/ms-playwright').glob('chromium-*/chrome-linux*/chrome'))[-1]
    browser=pw.chromium.launch(executable_path=str(chrome),headless=True,args=['--no-sandbox'])
    ctx=browser.new_context(viewport={'width':1440,'height':1000},accept_downloads=True)
    page=ctx.new_page();errors=[];failed=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('response',lambda r:failed.append({'url':r.url,'status':r.status}) if r.status>=400 else None)
    page.goto(BASE+'practice/')
    page.wait_for_function("document.querySelector('#runtime').dataset.state==='ready'",timeout=180000)
    check('local Python runtime ready',True)
    check('six levels',page.locator('#levels button').count()==6)
    for variant in [0,1]:
        page.locator('#variant').select_option(str(variant))
        for n,source in SOLUTIONS.items():
            page.locator(f'#levels button[data-id="{n}"]').click()
            page.locator('#editor').fill(source);page.locator('#run').click()
            page.wait_for_function("document.querySelector('#result').dataset.status==='passed'",timeout=30000)
            check(f'level {n} variant {variant} runs real Python',True)
    page.locator('#variant').select_option('0');page.locator('#levels button[data-id="1"]').click()
    for code,word in [('move(4)','墙'),('while True:\n    pass','执行'),('if True\n    move(1)','SyntaxError')]:
        page.locator('#editor').fill(code);page.locator('#run').click()
        page.wait_for_function("document.querySelector('#result').dataset.status==='failed'",timeout=30000)
        check('failure: '+word,word in page.locator('#result').inner_text())
    page.locator('#hint').click();check('graded hint displayed',bool(page.locator('#hints').inner_text()))
    page.locator('#levels button[data-id="4"]').click();page.locator('#editor').fill(SOLUTIONS[4]);page.locator('#run').click()
    page.wait_for_function("document.querySelector('#result').dataset.status==='passed'",timeout=30000)
    page.locator('#replay').click();page.locator('#pauseReplay').click();page.locator('#step').click()
    check('single-step replay advances',int(page.locator('#frameCounter').get_attribute('data-frame'))>=1)
    page.locator('svg .actor').first.click();check('object inspection visible',bool(page.locator('#inspect').inner_text()))
    with page.expect_download() as dl:page.locator('#export').click()
    dest=ROOT/'verification/practice-progress.json';dl.value.save_as(dest);data=json.loads(dest.read_text())
    check('all twelve level records exported',all(data['records'][f'{i}:{v}']['attempts'] for i in range(1,7) for v in [0,1]))
    check('hints exported',any(r['hints']>0 for r in data['records'].values()))
    check('first and failed attempts retained',len(data['records']['1:0']['attempts'])>=4)
    page.reload();page.wait_for_selector('#editor');page.locator('#levels button[data-id="1"]').click()
    check('edited code survives reload',page.locator('#editor').input_value()=='if True\n    move(1)')
    page.screenshot(path=str(ROOT/'verification/practice-desktop.png'),full_page=True)
    page.set_viewport_size({'width':390,'height':844})
    check('practice mobile fits viewport',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
    page.screenshot(path=str(ROOT/'verification/practice-mobile.png'),full_page=True)
    check('home navigation',page.locator('a[href="../"]').count()>0)
    check('no JavaScript errors',not errors);check('no failed HTTP responses',not failed)
    browser.close()
report={'base':BASE,'passed':len(results),'checks':results,'errors':errors,'failedResponses':failed}
(ROOT/'verification/practice-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2))
