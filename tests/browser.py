from pathlib import Path
from playwright.sync_api import sync_playwright
import json, os
ROOT=Path(__file__).resolve().parents[1]
BASE=os.environ.get('LAB_URL','http://127.0.0.1:8786/')
results=[]
def check(name,condition):
    assert condition,name
    results.append(name)
def expected(topic,m):
    data=m['data']
    if topic=='array': return data[m['index']]
    if topic=='stack': return data[-1]
    if topic=='queue': return data[0]
    if topic=='binary': return (m['lo']+m['hi'])//2
    if topic=='bubble': return next(i for i in range(len(data)-1) if data[i]>data[i+1])
    if topic=='bfs': return 'C'
    if topic=='insertion': return json.dumps(sorted(m['input'][:2])+m['input'][2:],separators=(',',':'))
    if topic=='merge': return json.dumps(sorted(m['left']+m['right']),separators=(',',':'))
    if topic=='quick': return sum(x<m['pivot'] for x in m['input'])
    if topic=='heap': return max(m['input'])
    if topic=='recursion':
        result=1
        for n in range(2,m['n']+1): result*=n
        return result
    if topic in ['preorder','inorder','postorder']:
        def walk(t):
            if not t:return []
            left,right,root=walk(t.get('left')),walk(t.get('right')),[t['value']]
            return root+left+right if topic=='preorder' else left+root+right if topic=='inorder' else left+right+root
        return ' → '.join(walk(m['tree']))
    if topic=='stones':
        wins=[False]
        for n in range(1,m['n']+1): wins.append(any(not wins[n-k] for k in range(1,min(n,m['limit'])+1)))
        return next((k for k in range(1,min(m['n'],m['limit'])+1) if not wins[m['n']-k]),0)
    if topic=='minimax': return max(min(pair) for pair in m['leaves'])
    raise AssertionError('untested topic '+topic)
with sync_playwright() as pw:
    candidates=sorted((Path.home()/'.cache/ms-playwright').glob('chromium-*/chrome-linux*/chrome'))
    chrome=os.environ.get('CHROME_PATH',str(candidates[-1]) if candidates else '/usr/bin/google-chrome')
    browser=pw.chromium.launch(executable_path=chrome,headless=True,args=['--no-sandbox'])
    context=browser.new_context(viewport={'width':1440,'height':1000},accept_downloads=True)
    page=context.new_page(); errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(BASE)
    check('homepage contains three working module links',all(page.locator(f'a[href="{s}/"]').count()>0 for s in ['practice','algorithms','tokamak']))
    page.locator('a[href="algorithms/"]').first.click();page.wait_for_selector('[data-topic]')
    catalog=page.evaluate("async()=> (await import('./model.mjs')).topics.map(({id,stars})=>({id,stars}))")
    ids=[t['id'] for t in catalog];count=len(ids)
    check('catalog includes original and advanced lessons',set(['array','stack','queue','binary','bubble','bfs','insertion','merge','quick','heap','recursion','preorder','inorder','postorder','stones','minimax'])<=set(ids))
    check('all catalog lessons rendered',page.locator('[data-topic]').count()==count)
    check('progress announces accessible count',page.locator('#progress').get_attribute('role')=='status')
    check('visible star guidance',all(x in page.locator('#difficultyGuide').inner_text() for x in ['★','★★','★★★']))
    for stars in [1,2,3]:
        page.locator(f'[data-filter="{stars}"]').click()
        visible=page.locator('[data-topic]:visible').evaluate_all('(xs)=>xs.map(x=>x.dataset.topic)')
        wanted=[t['id'] for t in catalog if t['stars']==stars]
        check(f'{stars}-star exact filter',visible==wanted)
        check(f'{stars}-star accessible result count',str(len(wanted)) in page.locator('#filterCount').inner_text())
        check(f'{stars}-star selection remains visible',page.locator('[data-topic][aria-current="true"]').is_visible())
    page.locator('[data-filter="all"]').click()
    histories={}
    for topic in ids:
        page.locator(f'[data-topic="{topic}"]').click()
        check(topic+' star badge',bool(page.locator('#difficulty').inner_text()))
        before=page.locator('#caption').inner_text();page.locator('#next').click()
        check(topic+' step changes explanation',page.locator('#caption').inner_text()!=before)
        page.locator('#end').click();check(topic+' demo reaches end',page.locator('#next').is_disabled())
        check(topic+' final visual accessible',bool(page.locator('#visual').inner_text()) or page.locator('#visual svg[role="img"]').count()>0)
        page.locator('#prev').click();check(topic+' previous leaves end',not page.locator('#next').is_disabled())
        page.locator('#reset').click();check(topic+' reset returns to start',page.locator('#prev').is_disabled())
        m=json.loads(page.locator('#exercise').get_attribute('data-meta'));answer=expected(topic,m)
        options=page.locator('[data-answer]');values=[json.loads(v) for v in options.evaluate_all('(xs)=>xs.map(x=>x.dataset.answer)')]
        wrong=next(v for v in values if v!=answer)
        options.nth(values.index(wrong)).click();page.locator('#check').click()
        check(topic+' rejects independently wrong answer',page.locator('#feedback').get_attribute('data-status')=='wrong')
        page.locator('#hint').click();check(topic+' hint shown',bool(page.locator('#hintText').inner_text()))
        options.nth(values.index(answer)).click();page.locator('#check').click()
        check(topic+' accepts independently correct answer',page.locator('#feedback').get_attribute('data-status')=='correct')
        if topic not in ['bfs']:
            before=page.locator('#prompt').inner_text();page.locator('#newExercise').click()
            check(topic+' new deterministic variant',page.locator('#prompt').inner_text()!=before)
            m=json.loads(page.locator('#exercise').get_attribute('data-meta'));answer=expected(topic,m)
            values=[json.loads(v) for v in options.evaluate_all('(xs)=>xs.map(x=>x.dataset.answer)')]
            options.nth(values.index(answer)).click();page.locator('#check').click()
            check(topic+' new variant correct',page.locator('#feedback').get_attribute('data-status')=='correct')
    with page.expect_download() as dl:page.locator('#export').click()
    dest=ROOT/'verification/algorithm-progress.json';dest.parent.mkdir(exist_ok=True);dl.value.save_as(dest)
    data=json.loads(dest.read_text());first=[r for r in data['records'].values() if len(r['attempts'])==2]
    check('every topic history exported',set(r['topic'] for r in data['records'].values())==set(ids))
    check('first wrong answer and help levels retained',len(first)==count and all(not r['attempts'][0]['correct'] and r['attempts'][0]['hints']==0 and r['attempts'][1]['correct'] and r['attempts'][1]['hints']==1 for r in first))
    page.reload();page.wait_for_selector('[data-topic]');check('progress survives reload',f'{count} / {count}' in page.locator('#progress').inner_text())
    page.screenshot(path=str(ROOT/'verification/algorithms-desktop.png'),full_page=True)
    page.set_viewport_size({'width':390,'height':844})
    for topic in ids:
        page.locator(f'[data-topic="{topic}"]').click();page.locator('#end').click()
        check(topic+' mobile fits viewport',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
    page.screenshot(path=str(ROOT/'verification/algorithms-mobile.png'),full_page=True)
    for route in ['', 'algorithms/']:
        page.goto(BASE+route);page.wait_for_timeout(150)
        check(route+' mobile fits viewport',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
    # Load an untouched v1 record: adding topics must not migrate away first attempts.
    page.evaluate("""()=>localStorage.setItem('lucas-lab-algorithms-v1', JSON.stringify({version:1,selected:'array',seeds:{array:7},records:{'array:7':{topic:'array',seed:7,hints:0,attempts:[{answer:999,correct:false,hints:0,at:'2026-01-01T00:00:00Z'}]}}}))""")
    page.reload();page.wait_for_selector('[data-topic]')
    check('old v1 history preserved',page.evaluate("JSON.parse(localStorage.getItem('lucas-lab-algorithms-v1')).records['array:7'].attempts[0].answer")==999)
    page.set_viewport_size({'width':1440,'height':1000});page.goto(BASE)
    page.locator('a[href="tokamak/"]').first.click();page.wait_for_function('!!window.tokamak')
    check('Tokamak six stages integrated',page.locator('[data-step]').count()==6)
    for i in range(6):
        page.locator(f'[data-step="{i}"]').click();check(f'Tokamak stage {i}',page.evaluate('window.tokamak.state.step')==i)
    page.locator('#field-mode').select_option('toroidal');path=page.locator('#field-line-0').get_attribute('d')
    page.locator('#field-mode').select_option('poloidal');check('Tokamak field geometry changes',path!=page.locator('#field-line-0').get_attribute('d'))
    page.locator('[data-part-button="cs"]').click();check('Tokamak component selection',page.locator('#part-name').inner_text()=='中心螺线管')
    check('no JavaScript errors',not errors);browser.close()
report={'base':BASE,'topics':count,'passed':len(results),'checks':results,'errors':errors}
(ROOT/'verification/browser-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2))
