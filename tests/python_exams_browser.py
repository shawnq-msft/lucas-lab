"""Real browser/Pyodide acceptance; deadline checks use an injected clock, not a real-hour wait."""
import json, os
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
BASE=os.environ.get('LAB_URL','http://127.0.0.1:8786/').rstrip('/')+'/'
OUT=ROOT/'verification';OUT.mkdir(exist_ok=True)
CONTENT=json.loads((ROOT/'python-exams/exams.json').read_text())
SOLUTIONS=json.loads((ROOT/'python-exams/solutions.json').read_text())['exams']
KEY='lucas-lab-python-exams-v1'
checks=[]
with sync_playwright() as p:
    browser=p.chromium.launch(args=['--no-sandbox'])
    context=browser.new_context(viewport={'width':1440,'height':1000},accept_downloads=True)
    context.add_init_script('window._offset=0;const realNow=Date.now.bind(Date);Date.now=()=>realNow()+window._offset;window.print=()=>{window._printed=true};')
    page=context.new_page();errors=[];failures=[];requests=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('response',lambda r:failures.append((r.status,r.url)) if r.status>=400 else None)
    page.on('request',lambda r:requests.append(r.url))
    page.on('dialog',lambda d:d.accept())
    page.goto(BASE+'python-exams/');page.wait_for_function("!document.querySelector('#start').disabled",timeout=120000)
    assert page.locator('#paper option').count()==3
    assert page.locator('#nav button').count()==12
    assert not any('solutions.json' in u for u in requests),'Answers fetched before submission'
    assert page.locator('.review').count()==0
    page.locator('#start').click();assert page.locator('#submit').is_disabled();assert page.locator('#paper').is_disabled()
    page.locator('input[name=choice]').nth(1).check();page.reload();page.wait_for_function("document.querySelector('#runtime').textContent.includes('已就绪')",timeout=120000)
    assert page.locator('input[name=choice]').nth(1).is_checked()
    assert page.locator('#submit').is_disabled();checks.append('draft, answers and remaining time restore; early submit locked')
    totals=[]
    for paper_index,exam in enumerate(CONTENT['exams']):
        if paper_index:
            page.locator('#paper').select_option(exam['id']);page.locator('#start').click()
        for i,q in enumerate(exam['choices']):
            page.locator(f'#nav button[data-i="{i}"]').click()
            page.locator('input[name=choice]').nth(SOLUTIONS[exam['id']]['choices'][q['id']]['answer']).check()
        for i,t in enumerate(exam['tasks']):
            page.locator(f'#nav button[data-i="{i+8}"]').click();page.wait_for_selector('#code')
            if paper_index==0 and i==0:
                page.locator('#code').fill('while True:\n    pass')
                page.locator('#run').click();page.wait_for_function("!document.querySelector('#run').disabled",timeout=25000)
                assert page.locator('#stars').inner_text()=='☆☆☆';checks.append('infinite loop bounded in real browser')
            reference=SOLUTIONS[exam['id']]['tasks'][t['id']]['solution']
            page.locator('#code').fill(reference);page.locator('#run').click()
            page.wait_for_function("!document.querySelector('#run').disabled && document.querySelector('#stars').textContent==='★★★'",timeout=25000)
            assert page.locator('#map svg').count()==1
            assert int(page.locator('#timeline').get_attribute('max'))>=1
            if paper_index==0 and i==0:
                page.locator('#code').fill(reference+'\n# modified')
                assert page.locator('#stars').inner_text()==''
                page.locator('#run').click();page.wait_for_function("document.querySelector('#stars').textContent==='★★★'",timeout=25000)
                checks.append('code edit invalidates old run; rerun restores stars')
            checks.append(exam['id']+':'+t['id']+' reference executed by browser Python, 3 stars')
        assert page.locator('.review').count()==0
        assert not any('solutions.json' in u for u in requests) if paper_index==0 else True
        page.locator('#printPaper').click();page.wait_for_function('window._printed===true');assert page.locator('#printArea .print-question').count()==12
        assert page.locator('#printArea .review').count()==0
        page.evaluate('window._offset+=1800001');page.wait_for_function("!document.querySelector('#submit').disabled")
        page.locator('#submit').click();page.wait_for_function("document.querySelector('#report').textContent.includes('100 / 100')")
        assert page.locator('#code').get_attribute('readonly') is not None
        assert page.locator('.review').count()==1
        with page.expect_download() as download:page.locator('#export').click()
        path=Path(download.value.path());saved=json.loads(path.read_text())
        assert saved['state']['papers'][exam['id']]['first']['reason']=='manual'
        totals.append({'paper':exam['id'],'knowledge':8,'tasks':4,'score':100})
    # New attempt auto-submits at the hard deadline and cannot overwrite first.
    page.locator('#paper').select_option('A');page.locator('#start').click()
    page.evaluate('window._offset+=3600001');page.wait_for_function("document.querySelector('#report').textContent.includes('0 / 100')",timeout=15000)
    saved=page.evaluate('(key)=>JSON.parse(localStorage.getItem(key))',KEY)
    assert len(saved['papers']['A']['attempts'])==2
    assert saved['papers']['A']['attempts'][-1]['reason']=='timeout'
    assert saved['papers']['A']['first']==saved['papers']['A']['attempts'][0]
    page.locator('#record').select_option('0');assert '100 / 100' in page.locator('#report').inner_text()
    page.locator('#printReview').click();page.wait_for_function('document.querySelectorAll("#printArea .review").length===12')
    checks.extend(['all three paper totals 100; no solutions fetched before first submit','timeout auto-submit; first snapshot immutable; record navigation','12 question blank print and submitted answer print','JSON export contains actual saved attempts'])
    for width in [390,768,1440]:
        page.set_viewport_size({'width':width,'height':1000})
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),width
    page.set_viewport_size({'width':1440,'height':1000});page.screenshot(path=str(OUT/'python-exams-desktop.png'),full_page=True)
    page.set_viewport_size({'width':390,'height':844});page.screenshot(path=str(OUT/'python-exams-mobile.png'),full_page=True)
    page.goto(BASE);page.wait_for_function("!document.querySelector('#search').disabled")
    page.locator('#search').fill('Python 模拟卷');assert page.locator('a[href="python-exams/"]').is_visible()
    checks.append('home searchable link and 390/768/1440 no horizontal overflow')
    assert not errors,errors
    assert not failures,failures
    result={'base':BASE,'checks':checks,'papers':totals,'js_errors':errors,'http_failures':failures,'clock_test':'Date.now offset injected; real Python runs, not fabricated scores'}
    (OUT/'python-exams-browser.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print(json.dumps(result,ensure_ascii=False,indent=2));browser.close()
