export function gradeQuestion(q,value){
 if(q.type==='choice')return Number.isInteger(value)&&value>=0&&value<q.options.length&&value===q.answer;
 return typeof value==='string'&&value.trim()!==''&&value.trim()===String(q.answer).trim();
}
export function gradeExam(exam,answers,time=Date.now()){
 const details=exam.questions.map(q=>({id:q.id,value:answers[q.id]??null,correct:gradeQuestion(q,answers[q.id])}));
 const correct=details.filter(d=>d.correct).length;
 return {id:exam.id,time,total:details.length,correct,percent:Math.round(correct/details.length*100),details};
}
export function retainExamRuns(runs){const out=[...runs];while(out.length>20){const seen=new Set();let remove=-1;for(let i=0;i<out.length;i++){if(seen.has(out[i].id)){remove=i;break;}seen.add(out[i].id);}if(remove<0)break;out.splice(remove,1);}return out;}
export function newProgress(){return {version:1,answers:{},positions:{},notes:{},drafts:{},examRuns:[]};}
const object=x=>x!==null&&typeof x==='object'&&!Array.isArray(x);
const safeKey=k=>/^[a-z0-9-]{1,60}$/i.test(k)&&!['constructor','prototype'].includes(k);
export function readProgress(raw){
 try{const p=JSON.parse(raw);if(!object(p)||p.version!==1||!object(p.answers)||!object(p.positions)||!object(p.notes)||!object(p.drafts)||!Array.isArray(p.examRuns))return newProgress();
 const out=newProgress();for(const [id,r]of Object.entries(p.answers)){if(!safeKey(id)||!object(r)||!object(r.first)||!object(r.last)||!Number.isSafeInteger(r.attempts)||r.attempts<1)continue;
 const valid=a=>typeof a.correct==='boolean'&&Number.isFinite(a.time)&&(typeof a.value==='string'||Number.isInteger(a.value));if(valid(r.first)&&valid(r.last))out.answers[id]={first:r.first,last:r.last,attempts:r.attempts,revealed:r.revealed===true};}
 for(const [id,n]of Object.entries(p.positions))if(safeKey(id)&&Number.isSafeInteger(n)&&n>=0&&n<100)out.positions[id]=n;
 for(const field of ['notes','drafts'])for(const [id,s]of Object.entries(p[field]))if(safeKey(id)&&typeof s==='string'&&s.length<=50000)out[field][id]=s;
 out.examRuns=p.examRuns.filter(r=>object(r)&&safeKey(r.id)&&Number.isFinite(r.time)&&Number.isInteger(r.correct)&&r.correct>=0&&Number.isInteger(r.total)&&r.total>0&&r.correct<=r.total&&Array.isArray(r.details)).slice(-20);return out;
 }catch{return newProgress();}
}
export function recordAnswer(progress,q,value,time=Date.now(),revealed=false){
 const attempt={value,correct:gradeQuestion(q,value),time};const old=progress.answers[q.id];
 progress.answers[q.id]={first:old?.first??attempt,last:attempt,attempts:(old?.attempts??0)+1,revealed:old?.revealed===true||revealed};return progress.answers[q.id];
}
export function remainingSeconds(start,minutes,now=Date.now()){return Math.max(0,Math.ceil((minutes*60000-Math.max(0,now-start))/1000));}
