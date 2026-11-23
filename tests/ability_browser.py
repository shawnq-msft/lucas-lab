"""Exercise real Python against changing mission inputs, including two faulty repair tickets."""
from pathlib import Path
import os,json
from playwright.sync_api import sync_playwright
base=os.getenv('LAB_URL','http://127.0.0.1:8786/').rstrip('/')+'/'
refs=[
'def solve(d):\n    lane = "下" if "#" in d["top"] else "上"\n    return lane + "右"*len(d["top"]) + ("下" if lane=="上" else "上")',
'def solve(d):\n    lane=d["key"]\n    return lane + "右"*len(d["top"]) + ("上" if lane=="下" else "下")',
'def solve(d):\n    return max(([j] for j,w in enumerate(d["kg"]) if w<=d["cap"]),key=lambda a:d["value"][a[0]],default=[])',
'def solve(d):\n    from itertools import combinations\n    choices=[a for n in (0,1,2) for a in combinations(range(len(d["kg"])),n) if sum(d["kg"][j] for j in a)<=d["cap"]]\n    return list(max(choices,key=lambda a:sum(d["value"][j] for j in a)))',
'def solve(d):\n    return max(map(len,"".join(map(str,d["signal"])).split("0")))',
'def solve(d):\n    p=d["start"]\n    for x in d["delta"]: p=max(0,min(d["cap"],p+x))\n    return p']
with sync_playwright() as pw:
 b=pw.chromium.launch(args=['--no-sandbox']);p=b.new_page();errors=[];p.on('pageerror',lambda e:errors.append(str(e)));p.goto(base+'ability/');p.locator('#run:enabled').wait_for(timeout=90000)
 for i,ref in enumerate(refs):
    p.locator('#missions button').nth(i).click()
    if i in (4,5):
        p.locator('#check').click();p.wait_for_function("document.querySelector('#result').children.length===5");assert '未通过' in p.locator('#result div').first.inner_text()
    if i==0:
        sample=json.loads(p.locator('#input').inner_text());hardcoded='下'+'右'*len(sample['top'])+'上';p.locator('#code').fill('def solve(d):\n    return '+repr(hardcoded));p.locator('#check').click();p.wait_for_function("document.querySelector('#result').children.length===5");assert '现场 · 通过' in p.locator('#result').inner_text() and '未通过' in p.locator('#result').inner_text()
    p.locator('#code').fill(ref);p.locator('#check').click();p.wait_for_function("document.querySelector('#status').textContent.startsWith('通关')",timeout=18000);assert p.locator('#result div').count()==5
    print(i+1,p.locator('#title').inner_text(),'5/5')
 p.reload();p.locator('#run:enabled').wait_for(timeout=90000);assert '首次验收：未通过' in p.locator('#history').inner_text();assert p.locator('#code').input_value()==refs[0]
 p.locator('#hint').click();assert p.locator('#hintText').inner_text();p.locator('#change').click();assert p.locator('#code').input_value()==refs[0]
 for width in (390,1280):
    p.set_viewport_size({'width':width,'height':800});assert p.evaluate('document.documentElement.scrollWidth <= innerWidth')
 assert not errors,errors
 print('First failure preserved after success, shared-code retest, hint, reload and layout passed:',base);b.close()
