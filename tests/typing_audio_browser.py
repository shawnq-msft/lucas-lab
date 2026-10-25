"""Exercise the real WebAudio graph, not mocked oscillator output."""
import json, os
from pathlib import Path
from playwright.sync_api import sync_playwright
base=os.environ.get('LAB_URL','http://127.0.0.1:8786/').rstrip('/')+'/typing/'
with sync_playwright() as p:
    chrome=next((Path.home()/'.cache/ms-playwright').glob('*/chrome-linux64/chrome'))
    browser=p.chromium.launch(executable_path=str(chrome),args=['--no-sandbox'])
    page=browser.new_page()
    page.route('**/typing/audio-check.html',lambda r:r.fulfill(content_type='text/html',body='<button id="go">Play test</button>'))
    page.goto(base+'audio-check.html')
    page.evaluate('''async () => {
      const {createAudio}=await import('./audio.mjs');
      class ObservedContext extends AudioContext {
        constructor(){super();window.ctx=this;window.analyser=this.createAnalyser();window.analyser.connect(this.destination);this.gainCount=0;}
        createGain(){const g=super.createGain();if(this.gainCount++===0){const connect=g.connect.bind(g);g.connect=(dest)=>connect(window.analyser);}return g;}
      }
      window.a=createAudio({AudioContext:ObservedContext,speechSynthesis,SpeechSynthesisUtterance,setInterval:(...args)=>setInterval(...args),clearInterval:(...args)=>clearInterval(...args)});
      window.sample=()=>{const data=new Float32Array(analyser.fftSize);analyser.getFloatTimeDomainData(data);return Math.sqrt(data.reduce((s,v)=>s+v*v,0)/data.length);};
      document.querySelector('#go').onclick=()=>{window.unlocked=a.unlock();};
    }''')
    page.click('#go')
    unlocked=page.evaluate('unlocked')
    assert unlocked, {'unlock':unlocked,'context':page.evaluate('({exists:!!window.ctx,state:window.ctx?.state,gains:window.ctx?.gainCount})')}
    def peak(ms=550):
        values=[]
        for _ in range(ms//50):
            page.wait_for_timeout(50);values.append(page.evaluate('sample()'))
        return max(values)
    page.wait_for_timeout(180)
    music=peak();assert music>0.00001, music
    # More than a whole 4.8s phrase: the soundtrack really loops.
    page.wait_for_timeout(4900)
    loop=peak();assert loop>0.00001, loop
    page.evaluate('a.setMusic(false)');page.wait_for_timeout(1100)
    quiet=page.evaluate('sample()');assert quiet<0.00001, quiet
    page.evaluate("a.effect('explosion')");page.wait_for_timeout(80)
    boom=page.evaluate('sample()');assert boom>0.00001, boom
    page.wait_for_timeout(600);page.evaluate("a.setEffects(false);a.effect('laser')");page.wait_for_timeout(80)
    muted=page.evaluate('sample()');assert muted<0.00001, muted
    page.evaluate('a.setMusic(true)');page.wait_for_timeout(370)
    resumed=peak();assert resumed>0.00001, resumed
    page.evaluate('a.stop()');page.wait_for_timeout(700)
    stopped=page.evaluate('sample()');assert stopped<0.00001, stopped
    print(json.dumps({'real_audio_checks':7,'loop_rms':loop,'music_rms':music,'music_off_rms':quiet,'explosion_rms':boom,'effects_off_rms':muted,'music_resumed_rms':resumed,'stopped_rms':stopped,'speech_api':page.evaluate('a.hasSpeech()'),'installed_voices':page.evaluate('speechSynthesis.getVoices().length')},ensure_ascii=False))
    page.evaluate('a.dispose()');browser.close()
