// A deliberately tiny teaching language, not Python or a real CPU emulator.
function parse(line,n){const m=/^(SET|ADD)\s+(-?\d{1,3})$/.exec(line);if(m)return {op:m[1],value:Number(m[2]),line:n};if(line==='PRINT')return {op:'PRINT',line:n};throw Error(`第 ${n} 行不认识：${line}。只用 SET 数字、ADD 数字或 PRINT。`);}
export function translationTrace(source,mode){
 if(!['compiler','interpreter'].includes(mode))throw Error('Unknown mode');
 const lines=String(source).split('\n').map((v,i)=>({text:v.trim(),n:i+1})).filter(v=>v.text),steps=[],code=[],output=[];let value=0;
 const push=(phase,message,line=null,error=false)=>steps.push({phase,message,line,error,value,code:code.map(x=>({...x})),output:[...output]});
 push('ready','先猜一猜：屏幕最后会显示什么？');
 const translate=l=>{const instruction=parse(l.text,l.n);code.push(instruction);push('translate',`翻译第 ${l.n} 行 → ${instruction.op==='PRINT'?'OUT':instruction.op==='SET'?'LOAD #'+instruction.value:'ADD #'+instruction.value}`,l.n);return instruction;};
 const execute=i=>{if(i.op==='SET')value=i.value;else if(i.op==='ADD')value+=i.value;else output.push(value);push('execute',i.op==='PRINT'?`把 ${value} 送到屏幕。`:`执行第 ${i.line} 行，数字盒现在是 ${value}。`,i.line);};
 try{if(!lines.length)throw Error('先写一行程序吧。');if(lines.length>30)throw Error('教学程序最多 30 行。');if(mode==='compiler'){lines.forEach(translate);code.forEach(execute);}else lines.forEach(l=>execute(translate(l)));push('done','完成！翻译是理解指令，执行才会改变数字和屏幕。');}catch(e){push('error',e.message,null,true);}return steps;
}
export function computerTrace(a=3,b=4){
 if(!Number.isInteger(a)||!Number.isInteger(b)||Math.abs(a)>99||Math.abs(b)>99)throw Error('输入 -99 到 99 的整数');
 const memory=Array(16).fill(0);['LOAD 10','ADD 11','STORE 12','OUT 12','HALT'].forEach((v,i)=>memory[i]=v);memory[10]=a;memory[11]=b;
 const steps=[];let pc=0,ir='—',acc=0,output=null,halted=false;
 const push=(phase,message,address=null,route='')=>steps.push({phase,message,address,route,pc,ir,acc,output,halted,memory:[...memory]});
 push('ready','输入装置把两个数字放入内存 10 和 11 号格。指令和数据住在同一块内存。',10,'input');
 while(!halted){const address=pc;ir=memory[pc++];push('fetch',`取指：从内存 ${address} 号格取出 ${ir}；PC 指向下一条。`,address,'fetch');const [op,arg]=ir.split(' '),n=Number(arg);push('decode',`译码：控制器读懂 ${op}，${op==='HALT'?'准备停机':`将使用 ${n} 号格`}。`,address,'control');let message='';if(op==='LOAD'){acc=memory[n];message=`运算器取出 ${acc} 放入 ACC（临时数字盒）。`;}if(op==='ADD'){acc+=memory[n];message=`运算器加上 ${memory[n]}，ACC 变成 ${acc}。`;}if(op==='STORE'){memory[n]=acc;message=`把 ACC 的 ${acc} 写回内存 ${n} 号格。`;}if(op==='OUT'){output=memory[n];message=`输出装置显示 ${output}。`;}if(op==='HALT'){halted=true;message='停机！不是断电，是这段程序完成了。';}push('execute',message,op==='HALT'?address:n,op==='OUT'?'output':op==='HALT'?'control':'data');}
 return steps;
}
