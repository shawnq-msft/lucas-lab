"""Run the real Python worker in Chromium, including failures and record export."""
from pathlib import Path
import json, os, sys
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'sources/practice'))
from test_engine import SOLUTIONS
from test_advanced import ADVANCED_SOLUTIONS, bfs
import engine
SOLUTIONS={**SOLUTIONS,**ADVANCED_SOLUTIONS}
LEVELS=engine.catalog()
BASE=os.environ.get('LAB_URL','http://127.0.0.1:8786/')
results=[]
def check(name,condition):
    assert condition,name
    results.append(name)
with sync_playwright() as pw:
    chrome=sorted((Path.home()/'.cache/ms-playwright').glob('chromium-*/chrome-linux*/chrome'))[-1]
    browser=pw.chromium.launch(executable_path=str(chrome),headless=True,args=['--no-sandbox'])
    ctx=browser.new_context(viewport={'width':1440,'height':1000},accept_downloads=True)
    page=ctx.new_page();errors=[];failed=[];requests=[]
    page.on('request',lambda r:requests.append(r.url))
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('response',lambda r:failed.append({'url':r.url,'status':r.status}) if r.status>=400 else None)
    page.goto(BASE+'practice/')
    page.wait_for_function("document.querySelector('#runtime').dataset.state==='ready'",timeout=180000)
    check('local Python runtime ready',True)
    check('catalog has ten levels',page.locator('#levels button').count()==len(LEVELS)==10)
    check('expandable higher category',page.locator('#higher summary').inner_text().startswith('提高'))
    page.locator('#higher summary').click()
    check('higher category opens',page.locator('#higher').get_attribute('open') is not None)
    check('star ratings',page.locator('#levels button[data-id="8"]').inner_text().count('★')==3)
    for variant in [0,1]:
        page.locator('#variant').select_option(str(variant))
        for n,source in SOLUTIONS.items():
            page.locator(f'#levels button[data-id="{n}"]').click()
            page.locator('#editor').fill(source);page.locator('#run').click()
            page.wait_for_function("document.querySelector('#result').dataset.status==='passed'",timeout=30000)
            check(f'level {n} variant {variant} runs real Python',True)
            if n>=7:
                check(f'level {n} variant {variant} input visible',bool(page.locator('#contextText').inner_text()))
                check(f'level {n} variant {variant} replay has actions',int(page.locator('#frameCounter').get_attribute('data-frame'))>0)
                page.locator('#replay').click();page.locator('#pauseReplay').click();page.locator('#step').click()
                check(f'level {n} variant {variant} animated replay',int(page.locator('#frameCounter').get_attribute('data-frame'))>=1)
                if n==8:check('maze walls rendered',page.locator('#map').inner_html().count('#667761')>10)
                if n==9:
                    check('tree edges rendered',page.locator('#map .tree-edge').count()==5)
                    check('Python None input notation','None' in page.locator('#contextText').inner_text())
    # Use CPython's independent oracle for wrong-variant results, not engine answers.
    wrong_path=bfs(engine.World(8,0).maze,engine.World(8,0).start,engine.World(8,0).goal)
    failures={7:['for coin in coins:\n    goto(coin)',ADVANCED_SOLUTIONS[7].replace(' > ',' >= '),'for coin in sorted(coins):\n    goto(coin)'],8:['submit(None)','submit([start,goal])','submit('+repr(wrong_path)+')'],9:["submit(['A','B','D','E','C','F'])",ADVANCED_SOLUTIONS[9].replace('order.append(node)','order.append(root)')],10:['submit(True)','submit(-1)','submit(1)']}
    for n,codes in failures.items():
        page.locator(f'#levels button[data-id="{n}"]').click()
        for code in codes:
            page.locator('#editor').fill(code);page.locator('#run').click()
            page.wait_for_function("document.querySelector('#result').dataset.status==='failed'",timeout=30000)
            check(f'advanced {n} rejects {code[:30]}',True)
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
    check('all twenty level records exported',all(data['records'][f'{i}:{v}']['attempts'] for i in SOLUTIONS for v in [0,1]))
    check('first advanced solutions retained',all(data['records'][f'{i}:{v}']['attempts'][0]['code']==SOLUTIONS[i] for i in range(7,11) for v in [0,1]))
    check('hints exported',any(r['hints']>0 for r in data['records'].values()))
    check('first and failed attempts retained',len(data['records']['1:0']['attempts'])>=4)
    page.reload();page.wait_for_selector('#editor');page.locator('#levels button[data-id="1"]').click()
    check('edited code survives reload',page.locator('#editor').input_value()=='if True\n    move(1)')
    page.screenshot(path=str(ROOT/'verification/practice-desktop.png'),full_page=True)
    page.set_viewport_size({'width':390,'height':844})
    check('practice mobile fits viewport',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
    page.locator('#higher summary').click()
    for n in range(7,11):
        page.locator(f'#levels button[data-id="{n}"]').click()
        check(f'advanced {n} mobile fits',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
        check(f'advanced {n} custom API visible','非官方' in page.locator('#goal').inner_text())
    page.screenshot(path=str(ROOT/'verification/practice-mobile.png'),full_page=True)
    check('home navigation',page.locator('a[href="../"]').count()>0)
    check('no JavaScript errors',not errors);check('no failed HTTP responses',not failed)
    check('Python assets are same-site',all(u.startswith(BASE) or u.startswith('blob:') for u in requests))
    legacy=browser.new_context()
    legacy.add_init_script("localStorage.setItem('lucas-lab-python-quest-v1',JSON.stringify({selected:4,variant:1,records:{'4:1':{code:'# existing student answer',seconds:73,hints:2,attempts:[{code:'# first answer',passed:false,hints:0,seconds:10}]}}}));")
    old=legacy.new_page();old.goto(BASE+'practice/');old.wait_for_selector('#editor')
    check('legacy selected variant and code preserved',old.locator('#editor').input_value()=='# existing student answer' and old.locator('#variant').input_value()=='1')
    check('legacy hint history preserved','已看提示 2 条' in old.locator('#attemptInfo').inner_text())
    check('legacy first submission preserved',old.evaluate("JSON.parse(localStorage.getItem('lucas-lab-python-quest-v1')).records['4:1'].attempts[0].code")=='# first answer')
    legacy.close()
    browser.close()
report={'base':BASE,'passed':len(results),'checks':results,'errors':errors,'failedResponses':failed}
(ROOT/'verification/practice-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2))
