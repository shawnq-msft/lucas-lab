"""Rebuild integrated pages from repository-local snapshots; originals stay untouched."""
from pathlib import Path
import importlib.util
import json
ROOT=Path(__file__).resolve().parent
src=ROOT/'sources/practice'
spec=importlib.util.spec_from_file_location('quest_engine',src/'engine.py')
engine=importlib.util.module_from_spec(spec);spec.loader.exec_module(engine)
payload={'levels':engine.catalog(),'engine':(src/'engine.py').read_text(),'initial':{str(n)+':'+str(v):engine.evaluate(n,'',v)['trace'][0] for n in range(1,7) for v in (0,1)}}
text=(src/'template.html').read_text()
assert text.count('__PAYLOAD__')==1
text=text.replace('__PAYLOAD__',json.dumps(payload,ensure_ascii=False).replace('</','<\\/'))
text=text.replace('https://cdn.jsdelivr.net/pyodide/v0.27.7/full/pyodide.js',"${new URL('runtime/pyodide.js',location.href).href}")
text=text.replace('https://cdn.jsdelivr.net/pyodide/v0.27.7/full/',"${new URL('runtime/',location.href).href}")
# A Blob worker cannot resolve relative paths itself: interpolate absolute same-site URLs.
text=text.replace('maodou-python-quest-v1','lucas-lab-python-quest-v1')
nav='<nav style="padding:12px 24px;font:14px system-ui;background:#e5efea"><a href="../" style="color:#1c6559">← Lucas Lab 首页</a></nav>'
text=text.replace('<body>','<body>'+nav,1)
text=text.replace('<head>','<head><meta name="robots" content="noindex,nofollow"><link rel="icon" href="../favicon.svg" type="image/svg+xml">',1)
(ROOT/'practice').mkdir(exist_ok=True)
(ROOT/'practice/index.html').write_text(text)
tokamak=(ROOT/'sources/tokamak/original.html').read_text()
tokamak=tokamak.replace('<head>','<head><meta name="robots" content="noindex,nofollow"><link rel="icon" href="../favicon.svg" type="image/svg+xml">',1)
# Original has body attributes; insert after its opening tag.
import re
tokamak=re.sub(r'(<body[^>]*>)',lambda m:m[1]+nav,tokamak,count=1)
(ROOT/'tokamak').mkdir(exist_ok=True)
(ROOT/'tokamak/index.html').write_text(tokamak)
print('Built practice/index.html and tokamak/index.html from local sources.')
