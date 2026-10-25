"""Real Chromium acceptance for both teaching demos."""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
base=os.environ.get('LAB_URL','http://127.0.0.1:8786/').rstrip('/')+'/computer/'
checks=[]
def check(name,value):
    assert value,name
    checks.append(name)
with sync_playwright() as p:
    chrome=next((Path.home()/'.cache/ms-playwright').glob('*/chrome-linux64/chrome'))
    browser=p.chromium.launch(executable_path=str(chrome),args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1440,'height':1100});errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)));page.goto(base)
    def finish(kind):
        for _ in range(100):
            b=page.locator('#'+kind+'Next')
            if b.is_disabled():break
            b.click()
        check(kind+' terminates',b.is_disabled())
    page.locator('#translationNext').click();check('translation before execute',page.locator('#value').inner_text()=='0' and page.locator('#code li').count()==1)
    finish('translation');check('compiler calculates',page.locator('#translationOutput').inner_text()=='7')
    page.locator('#errorExample').click();finish('translation');check('compiler stops before output',page.locator('#translationOutput').inner_text()=='还没有输出' and '不认识' in page.locator('#translationMessage').inner_text())
    page.locator('#mode').select_option('interpreter');finish('translation');check('interpreter output before later error',page.locator('#translationOutput').inner_text()=='7' and '不认识' in page.locator('#translationMessage').inner_text())
    page.locator('#source').fill('SET 9\nADD -2\nPRINT');finish('translation');check('editable program actually runs',page.locator('#translationOutput').inner_text()=='7')
    page.locator('#translationReset').click();page.locator('#translationAuto').click();page.wait_for_timeout(1200);check('autoplay steps', '0/' not in page.locator('#translationPhase').inner_text());page.locator('#translationAuto').click()
    Path('verification').mkdir(exist_ok=True);page.screenshot(path='verification/computer-translator.png',full_page=True)
    page.locator('#machineTab').click();check('shared memory',page.locator('#memory .cell').count()==16)
    page.locator('#inputA').fill('8');page.locator('#inputB').fill('5');page.locator('#load').click()
    page.locator('#machineNext').click();check('fetch PC and IR',page.locator('#pc').inner_text()=='1' and page.locator('#ir').inner_text()=='LOAD 10' and '内存' in page.locator('#bus').inner_text())
    page.locator('#machineNext').click();check('decode no arithmetic yet',page.locator('#acc').inner_text()=='0')
    page.locator('#machineNext').click();check('load executes',page.locator('#acc').inner_text()=='8')
    finish('machine');check('stored result and output',page.locator('#machineOutput').inner_text()=='13' and page.locator('#memory .cell').nth(12).locator('strong').inner_text()=='13')
    page.locator('#machineReset').click();check('reset clears screen',page.locator('#machineOutput').inner_text()=='?')
    page.locator('#inputA').fill('100');page.locator('#load').click();check('invalid input explained','整数' in page.locator('#inputError').inner_text())
    page.locator('#prediction').fill('13');page.locator('#checkPrediction').click();check('prediction feedback','对了' in page.locator('#predictionResult').inner_text())
    page.screenshot(path='verification/computer-machine.png',full_page=True)
    for width in [320,390,1440]:
        page.set_viewport_size({'width':width,'height':1000})
        for tab in ['translation','machine']:
            page.locator('#'+tab+'Tab').click();check(f'no overflow {width} {tab}',page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
        if width==390:page.screenshot(path='verification/computer-mobile.png',full_page=True)
    check('no runtime errors',not errors);browser.close()
print(f'{len(checks)} computer browser checks passed: '+', '.join(checks))
