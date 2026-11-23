const root=new URL('../practice/runtime/',self.location.href).href;let py;
(async()=>{try{importScripts(root+'pyodide.js');py=await loadPyodide({indexURL:root});postMessage({ready:true})}catch(e){postMessage({fault:String(e)})}})();
self.onmessage=async({data:{code,cases}})=>{try{py.globals.set('src',code);py.globals.set('payload',JSON.stringify(cases));let out=await py.runPythonAsync(`import json, contextlib, io
outputs=[]
for case in json.loads(payload):
    try:
        scope={}
        with contextlib.redirect_stdout(io.StringIO()):
            exec(compile(src, '<任务>', 'exec'), scope)
            val=scope['solve'](case)
        if type(val) not in (int, str, list, type(None)) or (type(val) in (list,str) and len(val)>200): raise ValueError('返回值类型或长度不符合任务要求')
        outputs.append({'value':json.loads(json.dumps(val,allow_nan=False))})
    except BaseException as e:
        outputs.append({'error':(type(e).__name__+': '+str(e))[:400]})
json.dumps(outputs, ensure_ascii=False)`);postMessage({outputs:JSON.parse(out)})}catch(e){postMessage({fault:String(e)})}};
