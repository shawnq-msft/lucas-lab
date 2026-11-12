"""Real Chromium acceptance. LAB_URL supports deployed Pages; --fixture uses test-only data."""
import json, os, sys
from pathlib import Path
from urllib.request import urlopen
from playwright.sync_api import sync_playwright
BASE=os.environ.get('LAB_URL','http://127.0.0.1:8786/').rstrip('/')+'/'
KEY='lucas-lab-camp101-v1'
checks=[]
def check(name,value):
    assert value,name
    checks.append(name)
def fixture():
    sections=[]
    for prefix,title,n,minutes,points in [('m','数学',10,30,6),('c','语文',4,12,5),('e','英语',4,8,5)]:
        qs=[]
        for i in range(1,n+1):
            q={'id':f'{prefix}{i:02}','title':'原创诊断','skill':'逻辑表达','stars':2,'points':points,'type':'fill','prompt':'7 + 5 = ?\n请记录思路。','answers':['12'],'explanation':'解析专用：七加五得十二。'}
            if i==2:q.update(type='choice',prompt='Which number is even?',options=['A. 3','B. 4','C. 5'],answer='B')
            if prefix=='c':q.update(type='manual',prompt='解释为什么要遵守规则。',answer='尊重与安全',rubric=[{'points':3,'note':'表达清楚'},{'points':2,'note':'给出例子'}])
            qs.append(q)
        sections.append({'id':prefix,'title':title,'minutes':minutes,'questions':qs})
    return {'title':'101科创营 · 原创诊断','version':'test','minutes':50,'disclaimer':'非官方真题，依据家长回忆原创。','sources':[{'title':'家长回忆','url':'https://example.com','status':'未独立核实','note':'可能同源'}],'sections':sections}
exam=fixture() if '--fixture' in sys.argv else json.load(urlopen(BASE+'camp101/content.json'))
questions=[q for s in exam['sections'] for q in s['questions']]
with sync_playwright() as pw:
    chrome=next((Path.home()/'.cache/ms-playwright').glob('*/chrome-linux64/chrome'))
    browser=pw.chromium.launch(executable_path=str(chrome),args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1366,'height':900});errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    if '--fixture' in sys.argv:page.route('**/camp101/content.json',lambda r:r.fulfill(json=exam))
    page.goto(BASE+'camp101/')
    page.locator('#startExam').wait_for(timeout=5000)
    check('noindex and backlink',page.locator('meta[name=robots]').get_attribute('content')=='noindex,nofollow' and page.locator('a[href="../"]').count()>0)
    check('solutions absent before start',page.locator('.solution').count()==0)
    page.locator('#evidence summary').click()
    check('privacy AI-off caveats',all(t in page.locator('body').inner_text() for t in ['不上传','AI','非官方','同源']))
    if '--fixture' not in sys.argv:
        for field in ['assessmentGuide','evidenceNote','coverageNote']:
            check('content metadata '+field,exam[field] in page.locator('body').inner_text())
        check('diagnostic methods not revealed before submit',not page.locator('#diagnosticDetails').is_visible())
    page.locator('#startExam').click()
    check('18 questions and no solutions',page.locator('.question').count()==18 and page.locator('.solution').count()==0)
    check('50 minute timer',page.locator('#timer').inner_text().startswith(('50:','49:')))
    # Independently solve the first fixture problems, before consulting content keys.
    if '--fixture' in sys.argv:
        page.locator('[data-qid=m01] [data-answer]').fill(str(7+5))
        page.locator('[data-qid=m02] input[value=B]').check()
    else:
        # Solve supplied tasks independently (no key lookup): congruences, permutations,
        # and a loop trace. Content keys are used only later for exhaustive UI coverage.
        from itertools import permutations
        solved={'m01':str(next(n for n in range(51,100) if n%5==2 and n%7==3)),
                'm02':str(sum((100*a+10*b+c)%4==0 for a,b,c in permutations([1,2,3,4],3))),
                'm09':str(sum(i if i%2==0 else -1 for i in range(1,6)))}
        for qid,answer in solved.items():page.locator(f'[data-qid="{qid}"] [data-answer]').fill(answer)
        check('independent meaningful answers',solved=={'m01':'52','m02':'6','m09':'3'})
    page.locator('[data-qid=m01] [data-reasoning]').fill('拆成 7+3+2。')
    page.locator('[data-qid=m02] [data-help]').select_option('H2')
    page.reload();page.locator('.question').first.wait_for()
    check('draft reload preserves reasoning and help',page.locator('[data-qid=m01] [data-reasoning]').input_value()=='拆成 7+3+2。' and page.locator('[data-qid=m02] [data-help]').input_value()=='H2')
    check('reload still hides explanations',page.locator('.solution').count()==0)
    for q in questions:
        box=page.locator(f'[data-qid="{q["id"]}"]')
        if q['type']=='choice':box.locator(f'input[value="{q["answer"]}"]').check()
        else:box.locator('[data-answer]').fill(q.get('answers',['我的独立表达'])[0])
    page.locator('#submitExam').click();page.locator('#confirmSubmit').click()
    page.locator('#result').wait_for()
    if '--fixture' not in sys.argv:
        check('diagnostic guide visible after submission',all(t in page.locator('body').inner_text() for t in exam['diagnosticGuide']))
    check('submission exposes solutions and pending explicitly',page.locator('.solution').count()==18 and '待家长' in page.locator('#result').inner_text() and '自动' in page.locator('#result').inner_text())
    auto_max=sum(q['points'] for q in questions if q['type']!='manual')
    pending_max=sum(q['points'] for q in questions if q['type']=='manual')
    check('independent section score totals',f'自动判分 {auto_max} / {auto_max}' in page.locator('#result').inner_text() and f'待家长评分 {pending_max} 分' in page.locator('#result').inner_text())
    check('all supplied rubric points displayed',all(f'{r["points"]} 分 · {r["note"]}' in page.locator(f'[data-qid="{q["id"]}"] .solution').inner_text() for q in questions for r in q.get('rubric',[])))
    check('submitted answer and help frozen',page.locator('[data-answer]:enabled').count()==0 and page.locator('[data-help]:enabled').count()==0)
    first_snapshot=page.evaluate('(key)=>JSON.stringify(JSON.parse(localStorage.getItem(key)).first)',KEY)
    manual=next(q for q in questions if q['type']=='manual')
    page.locator(f'[data-parent-score="{manual["id"]}"]').select_option('3')
    check('parent score status updates without reload',page.locator(f'[data-qid="{manual["id"]}"] .solution h4').first.inner_text()==f'家长评分 3 / {manual["points"]}')
    page.reload();page.locator('#result').wait_for()
    check('parent partial credit survives reload','家长已评 3' in page.locator('#result').inner_text())
    with page.expect_download() as download:page.locator('#exportRecord').click()
    export=json.loads(Path(download.value.path()).read_text())
    check('export distinct frozen first and scored attempt',json.dumps(export['first'],ensure_ascii=False,separators=(',',':'))==first_snapshot and export['attempts'][0]['parentScores'][manual['id']]==3)
    # Print mode must default to student, even after explicitly printing a parent sheet.
    page.evaluate('window.print=()=>{}');page.locator('#printParent').click();page.emulate_media(media='print')
    check('explicit parent print shows solutions',page.locator('.solution').first.is_visible())
    page.emulate_media(media='screen');page.evaluate("dispatchEvent(new Event('afterprint'))")
    page.emulate_media(media='print')
    check('default student print hides solutions',not page.locator('.solution').first.is_visible())
    check('student print has blank answer fields',page.locator('[data-qid=m01] [data-answer]').evaluate("e=>getComputedStyle(e).webkitTextFillColor")=='rgba(0, 0, 0, 0)')
    check('student print excludes long parent guide',not page.locator('#assessment').is_visible())
    page.evaluate("dispatchEvent(new Event('beforeprint'))")
    check('student print removes actual stored-answer values',page.locator('[data-qid=m01] [data-answer]').input_value()=='')
    page.evaluate("dispatchEvent(new Event('afterprint'))")
    check('printing restores screen answer',page.locator('[data-qid=m01] [data-answer]').input_value()==('12' if '--fixture' in sys.argv else '52'))
    page.emulate_media(media='screen');page.locator('#newAttempt').click();page.locator('#startExam').click()
    page.clock.install();page.clock.fast_forward(3000001)
    page.locator('#result').wait_for()
    check('wall-clock 50 minute auto submission','时间到' in page.locator('#result').inner_text())
    state=page.evaluate('(key)=>JSON.parse(localStorage.getItem(key))',KEY)
    check('retry never overwrites baseline',len(state['attempts'])==2 and json.dumps(state['first'],ensure_ascii=False,separators=(',',':'))==first_snapshot)
    # A closed tab still has a deadline: restore an expired persisted draft.
    page.evaluate('(key)=>{const s=JSON.parse(localStorage.getItem(key));s.draft={startedAt:Date.now()-3001000,answers:{}};localStorage.setItem(key,JSON.stringify(s))}',KEY)
    page.reload();page.locator('#result').wait_for()
    check('expired draft auto submitted on reload',page.evaluate('(key)=>JSON.parse(localStorage.getItem(key)).attempts.length',KEY)==3)
    for width in [320,390,1440]:
        page.set_viewport_size({'width':width,'height':900})
        check(f'no horizontal overflow {width}',page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
    check('no JavaScript errors',not errors)
    # Corrupted and unavailable storage must not block a usable exam.
    page.evaluate('(key)=>localStorage.setItem(key,"broken")',KEY);page.reload();page.locator('#startExam').wait_for()
    check('malformed storage visible warning','无法读取' in page.locator('#storageStatus').inner_text())
    blocked=browser.new_page()
    if '--fixture' in sys.argv:blocked.route('**/camp101/content.json',lambda r:r.fulfill(json=exam))
    blocked.add_init_script("Object.defineProperty(window,'localStorage',{get(){throw new Error('denied')}})")
    blocked.goto(BASE+'camp101/');blocked.locator('#startExam').click()
    check('unavailable storage still permits exam',blocked.locator('.question').count()==18 and '无法' in blocked.locator('#storageStatus').inner_text())
    browser.close()
print(f'{len(checks)} Camp101 browser checks passed ({"test fixture" if "--fixture" in sys.argv else "real content"})')
