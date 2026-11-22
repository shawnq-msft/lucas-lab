"""Expanded missions: real input, timed rounds and visible mechanics. No injected scores."""
import os,json
from pathlib import Path
from playwright.sync_api import sync_playwright
BASE=os.environ.get('LAB_URL','http://127.0.0.1:8786/').rstrip('/')+'/typing/'
checks=[]
def check(name,value):
    assert value,name
    checks.append(name)
with sync_playwright() as pw:
    chrome=next((Path.home()/'.cache/ms-playwright').glob('*/chrome-linux64/chrome'))
    browser=pw.chromium.launch(executable_path=str(chrome),args=['--no-sandbox'])
    context=browser.new_context(viewport={'width':1440,'height':1000})
    page=context.new_page();errors=[];resources=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('response',lambda r:resources.append(r.url) if r.status>=400 else None)
    page.clock.install();page.add_init_script('crypto.getRandomValues=a=>{a.fill(1589137899);return a}')
    page.goto(BASE);page.locator('#speech').uncheck()
    out=Path('verification');out.mkdir(exist_ok=True)
    check('six illustrated mission cards',page.locator('[data-mission]').count()==6 and page.locator('[data-mission] .mission-art svg').count()>=12)
    check('six personal mission progress entries',page.locator('[data-best-scene]').count()==6)
    check('visible star criteria','85%' in page.locator('#starCriteria').inner_text() and '95%' in page.locator('#starCriteria').inner_text())
    page.evaluate('scrollTo(0,0)');page.clock.run_for(200);page.screenshot(path=str(out/'typing-new-chooser.png'))
    field=page.locator('#entry')
    def start(scene,speed='20',mode='words',duration='30'):
        if page.locator('#back').is_visible():page.locator('#back').click()
        page.locator('#mode').select_option(mode);page.locator('#duration').select_option(duration);page.locator('#speed').fill(speed)
        page.locator(f'[data-mission="{scene}"]').click()
    def target():return page.locator('#target').get_attribute('data-text')
    def type_target():field.press_sequentially(target()[len(field.input_value()):])
    def before(ch):field.evaluate("(e,ch)=>e.dispatchEvent(new InputEvent('beforeinput',{inputType:'insertText',data:ch,cancelable:true,bubbles:true}))",ch)
    def cookie(name):return next((c['value'] for c in context.cookies() if c['name']==name),'')
    for scene,effect,hold,goal in [('mining','.drill-effect','.crystal-held',3),('rescue','.tether-effect','.pod-docked',5),('race','.gate-cleared',None,5)]:
        start(scene);text=target();field.press('~');field.press_sequentially(text[0]);before('~')
        check(scene+' correct prefix immutable',field.input_value()==text[0] and field.evaluate('(e)=>e.selectionStart')==1)
        check(scene+' wrong action blocked',page.locator(effect).count()==0 and page.locator('#completed').inner_text()=='0')
        for key in ['Backspace','Delete','ArrowLeft','ControlOrMeta+a']:field.press(key)
        check(scene+' forbidden beforeinput paths',field.evaluate("""e=>['insertFromPaste','insertFromDrop','insertReplacementText','historyUndo','historyRedo','deleteContentBackward'].every(inputType=>{const evt=new InputEvent('beforeinput',{inputType,data:'x',cancelable:true,bubbles:true});e.dispatchEvent(evt);return evt.defaultPrevented})"""))
        check(scene+' paste drop cut blocked',field.evaluate("""e=>['paste','drop','cut'].every(type=>{const ev=new Event(type,{cancelable:true,bubbles:true});e.dispatchEvent(ev);return ev.defaultPrevented})"""))
        check(scene+' replacement never erases prefix',field.input_value()==text[0])
        initial=page.locator('.vehicle.active').get_attribute('style');page.clock.run_for(900)
        check(scene+' target travels across frames',page.locator('.vehicle.active').get_attribute('style')!=initial)
        for ch in text[1:]:before(ch)
        check(scene+' exact mobile completion',page.locator('#completed').inner_text()=='1' and page.locator(effect).count()==1)
        check(scene+' attached locked text',page.locator('.vehicle.active .vehicle-label').inner_text()==target())
        if scene=='race':check('race prompt leaves gate opening visible',page.locator('.vehicle.active').evaluate('(e)=>e.querySelector(".vehicle-label").getBoundingClientRect().bottom<=e.getBoundingClientRect().top'))
        check(scene+' single word label never breaks',page.locator('.vehicle.active .vehicle-label').evaluate('(e)=>e.offsetHeight<35'))
        check(scene+' visible objective progress',page.locator('#objective').get_attribute('data-current')=='1')
        if scene=='mining':check('drill connects rig to mineral',page.locator('.drill-effect').evaluate('(e)=>parseFloat(e.style.width)>100'))
        page.locator('#arena').scroll_into_view_if_needed();page.screenshot(path=str(out/f'typing-new-{scene}.png'))
        if scene=='race':
            player=page.locator('.race-player');rival=page.locator('.race-rival')
            a=[player.get_attribute('style'),rival.get_attribute('style')];page.clock.run_for(500)
            b=[player.get_attribute('style'),rival.get_attribute('style')]
            check('race separate moving player and rival',a[0]!=b[0] and a[1]!=b[1] and b[0]!=b[1])
            check('race advance and overtake','领先' in page.locator('#racePosition').inner_text() and float(player.get_attribute('data-distance'))>float(rival.get_attribute('data-distance')))
        if scene!='race':
            flight=page.locator('.crystal-flight' if scene=='mining' else '.pod-flight');a=flight.get_attribute('style');page.clock.run_for(400);check(scene+' extraction/docking travels',flight.get_attribute('style')!=a)
        page.clock.run_for(1700)
        if hold:check(scene+' extracted object retained in hold',page.locator(hold).count()==1)
        for _ in range(goal-1):type_target()
        check(scene+' completed mission objective',page.locator('#objective').get_attribute('data-cycles')=='1')
        page.locator('#restart').click();check(scene+' reset effects and objective',page.locator(effect).count()==0 and page.locator('#objective').get_attribute('data-cycles')=='0' and (not hold or page.locator(hold).count()==0))
    for width in [320,390,1440]:
        page.set_viewport_size({'width':width,'height':1000})
        for scene in ['mining','rescue','race']:
            for mode in ['words','python','symbols']:
                start(scene,'5',mode)
                for _ in range(3):type_target()
                page.clock.run_for(1234)
                check(f'{scene}/{mode}/{width} arena and labels fit',page.evaluate("""()=>{const a=document.querySelector('#arena').getBoundingClientRect();return document.documentElement.scrollWidth<=innerWidth&&[...document.querySelectorAll('.vehicle')].every(e=>{const r=e.getBoundingClientRect(),l=e.querySelector('.vehicle-label').getBoundingClientRect();return r.left>=a.left-1&&r.right<=a.right+1&&l.left>=a.left-1&&l.right<=a.right+1})}"""))
                check(f'{scene}/{mode}/{width} locked label readable',page.locator('.vehicle.active .vehicle-label').evaluate('(e)=>parseFloat(getComputedStyle(e).fontSize)>=11'))
                check(f'{scene}/{mode}/{width} HUD values fit',page.locator('.hud > div').evaluate_all('(es)=>es.every(e=>{const s=e.querySelector("strong"),r=s.getBoundingClientRect(),b=e.getBoundingClientRect();return r.left>=b.left&&r.right<=b.right})'))
            if width<400:
                page.locator('#arena').scroll_into_view_if_needed();page.screenshot(path=str(out/f'typing-new-{scene}-{width}.png'))
    page.set_viewport_size({'width':1440,'height':1000})
    for scene,n,stars in [('mining',3,1),('rescue',8,2),('race',15,3)]:
        start(scene)
        for _ in range(n):type_target()
        check(scene+' stars not awarded before end',page.locator('#roundStars').get_attribute('data-stars')=='0')
        check(scene+' no premature score cookie',not any(r[0]=={'mining':4,'rescue':5,'race':6}[scene] for r in json.loads(__import__('urllib.parse',fromlist=['unquote']).unquote(cookie('lucas_lab_typing_v1')))['r']))
        page.clock.fast_forward(31000)
        check(scene+' full-round stars',page.locator('#roundStars').get_attribute('data-stars')==str(stars) and '30.0 秒' in page.locator('#result').inner_text())
        saved=cookie('lucas_lab_typing_stars_v1');score=cookie('lucas_lab_typing_v1')
        check(scene+' bounded exact cookie readback',len(saved)<200 and saved in page.evaluate('document.cookie') and len(score)<3800)
        page.clock.fast_forward(9000);check(scene+' save once',cookie('lucas_lab_typing_stars_v1')==saved and cookie('lucas_lab_typing_v1')==score)
        page.reload();check(scene+' reload best stars',page.locator(f'[data-best-scene="{scene}"]').get_attribute('data-stars')==str(stars))
    saved=cookie('lucas_lab_typing_stars_v1');score=cookie('lucas_lab_typing_v1')
    start('mining');[type_target() for _ in range(16)];page.locator('#back').click();page.clock.fast_forward(31000)
    check('abandoned round no award or save',cookie('lucas_lab_typing_stars_v1')==saved and cookie('lucas_lab_typing_v1')==score)
    start('rescue');[type_target() for _ in range(16)]
    page.evaluate("Object.defineProperty(document,'hidden',{configurable:true,get:()=>true});document.dispatchEvent(new Event('visibilitychange'))")
    remaining=page.locator('#remaining').inner_text();page.clock.fast_forward(60000);check('paused round clock frozen',page.locator('#remaining').inner_text()==remaining)
    page.evaluate("Object.defineProperty(document,'hidden',{configurable:true,get:()=>false})");page.locator('#resume').click();page.clock.fast_forward(31000)
    check('paused completed round no stars or ranking',page.locator('#roundStars').get_attribute('data-stars')=='0' and cookie('lucas_lab_typing_stars_v1')==saved and cookie('lucas_lab_typing_v1')==score)
    start('rescue','60',duration='60');[type_target() for _ in range(15)];page.clock.run_for(59000)
    check('failed rescue no stars','防御失败' in page.locator('#result').inner_text() and page.locator('#roundStars').get_attribute('data-stars')=='0' and cookie('lucas_lab_typing_stars_v1')==saved)
    start('mining','5');field.press('~');page.clock.run_for(29400);type_target();page.clock.run_for(2600)
    check('last-second extracted crystal finishes flight after clock end',page.locator('.crystal-held').count()==1 and field.is_disabled())
    page.emulate_media(reduced_motion='reduce');start('race');field.press('~');a=page.locator('.race-rival').get_attribute('style');page.clock.run_for(800)
    check('reduced motion retains race physics',a!=page.locator('.race-rival').get_attribute('style'));page.emulate_media(reduced_motion='no-preference')
    for getter in ["return ''","throw Error('blocked')"]:
        bp=browser.new_page();bp.add_init_script("Object.defineProperty(document,'cookie',{get(){"+getter+"},set(v){}})");bp.goto(BASE)
        check('blocked cookie warning','无法' in bp.locator('#starStorageStatus').inner_text());bp.close()
    malformed=browser.new_context();malformed.add_cookies([{'name':'lucas_lab_typing_stars_v1','value':'%ZZ','url':BASE},{'name':'lucas_lab_typing_v1','value':'%ZZ','url':BASE}]);mp=malformed.new_page();mp.goto(BASE)
    check('malformed cookies safe zero progress',all(v=='0' for v in mp.locator('[data-best-scene]').evaluate_all('(es)=>es.map(e=>e.dataset.stars)')));malformed.close()
    check('browser codec all six and permanent bridge index',page.evaluate("""async()=>{const m=await import('./model.mjs'),keys=Object.keys(m.scenes),rows=keys.map((s,i)=>[s,'words',30,20,20,90,1700000000000+i*1000,100]);rows.push(['bridge','words',30,0,20,90,1700000000000,0]);const raw=m.encodeScores(rows),data=JSON.parse(decodeURIComponent(raw));return raw.length<3800&&m.decodeScores(raw).length===7&&data.r.find(r=>r[0]===3)[3]===0&&data.r.some(r=>r[0]===6)&&m.decodeScores(encodeURIComponent(JSON.stringify({v:2,r:[[12,100,90,1700000000]]})))[0][0]==='bridge'}"""))
    page.on('dialog',lambda d:d.accept());page.locator('#clear').click()
    check('clear removes both exact cookies',cookie('lucas_lab_typing_v1')=='' and cookie('lucas_lab_typing_stars_v1')=='' and page.locator('#starTotal').inner_text()=='0 / 18 ★')
    page.emulate_media(media='print');check('print criteria and progress available',page.locator('#starCriteria').is_visible() and page.locator('#missionProgress').is_visible());page.emulate_media(media='screen')
    check('no JS or resource errors',not errors and not resources)
    browser.close()
print(f'{len(checks)} expansion browser checks passed: '+', '.join(checks))
