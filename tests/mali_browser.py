"""Mali course UI acceptance against real Chromium, local or deployed URL."""
import os,json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
BASE=os.environ.get('LAB_URL','http://127.0.0.1:8786/').rstrip('/')+'/'
checks=[]
def check(name,value):
    assert value,name
    checks.append(name)
with sync_playwright() as pw:
    chrome=next((Path.home()/'.cache/ms-playwright').glob('*/chrome-linux64/chrome'))
    browser=pw.chromium.launch(executable_path=str(chrome),args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1366,'height':900});errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(BASE+'mali/');page.locator('[data-lesson="l01"]').wait_for()
    lessons=sum((json.loads((ROOT/'mali'/f'content-{c}.json').read_text()) for c in 'abc'),[])
    check('12 lesson navigation',page.locator('[data-lesson]').count()==12)
    check('official-source caveat','非官方真题' in page.locator('#sourceNote').inner_text())
    for lesson in lessons:
        page.locator(f'[data-lesson="{lesson["id"]}"]').click()
        check(lesson['id']+' title',lesson['title'] in page.locator('#lessonTitle').inner_text())
        for slide in lesson['slides']:
            check(lesson['id']+' slide '+slide['title'],page.locator('#slideTitle').inner_text()==slide['title'])
            if not page.locator('#nextSlide').is_disabled():page.locator('#nextSlide').click()
        page.locator('#showPractice').click()
        check(lesson['id']+' four practice questions',page.locator('#practice .question').count()==4)
        if 'coding' in lesson:
            check(lesson['id']+' editable C++ task',page.locator('#codeEditor').is_visible())
            text='// my independent attempt\nint main(){return 0;}\n'
            page.locator('#codeEditor').fill(text)
            with page.expect_download() as info:page.locator('#downloadCode').click()
            check(lesson['id']+' own source download',Path(info.value.path()).read_text()==text)
            page.locator('#revealCode').click()
            check(lesson['id']+' explicit reference',page.locator('#referenceCode').inner_text()==lesson['coding']['solution'].rstrip())
    page.locator('[data-lesson="l01"]').click();page.locator('#showPractice').click()
    q=lessons[0]['questions'][0];wrong=(q['answer']+1)%4
    box=page.locator(f'[data-qid="{q["id"]}"]')
    box.locator(f'input[value="{wrong}"]').check();box.locator('.check-answer').click()
    check('wrong answer explanation',box.locator('.feedback').is_visible() and '再想' in box.locator('.feedback').inner_text())
    box.locator(f'input[value="{q["answer"]}"]').check();box.locator('.check-answer').click()
    check('correct retry', '正确' in box.locator('.feedback').inner_text())
    page.reload();page.locator('[data-lesson="l01"]').wait_for();page.locator('[data-view="wrongbook"]').click()
    check('first wrong retained after correction and reload',page.locator('#workspace').get_by_text(q['prompt'],exact=True).count()>0)
    with page.expect_download() as info:page.locator('#exportProgress').click()
    export=json.loads(Path(info.value.path()).read_text())
    check('export retains independent first answer',export['answers'][q['id']]['first']['correct'] is False and export['answers'][q['id']]['last']['correct'] is True)
    page.locator('[data-view="exams"]').first.click();page.locator('[data-start-exam="stage1"]').click()
    check('stage1 has20choices and no answers',page.locator('.question').count()==20 and page.locator('.feedback').count()==0)
    page.locator('.question').first.locator('input').first.check()
    page.locator('#submitExam').click()
    check('submission exposes real score and explanations',page.locator('#examResult').is_visible() and page.locator('.exam-explanation').count()==20)
    page.locator('[data-view="exams"]').first.click();page.clock.install();page.locator('[data-start-exam="stage1"]').click();page.clock.fast_forward(2400001)
    check('40minute wallclock auto submission',page.locator('#examResult').is_visible() and '0 / 20' in page.locator('#examResult').inner_text())
    page.locator('[data-view="exams"]').first.click();page.locator('[data-start-exam="stage2"]').click()
    check('stage2 12choice8fill',page.locator('.question[data-type="choice"]').count()==12 and page.locator('.question[data-type="fill"]').count()==8)
    page.locator('#submitExam').click()
    for width in [320,390,1440]:
        page.set_viewport_size({'width':width,'height':900});page.locator('[data-lesson="l08"]').click()
        check(f'no horizontal overflow {width}',page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
    page.goto(BASE);check('homepage real entry',page.locator('a[href="mali/"]').count()>0)
    check('no JS errors',not errors);browser.close()
print(f'{len(checks)} Mali browser checks passed')
