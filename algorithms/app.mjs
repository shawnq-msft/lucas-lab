import {topics,makeLesson,judge} from './model.mjs';
const $=s=>document.querySelector(s),KEY='lucas-lab-algorithms-v1';
let store={version:1,selected:'array',seeds:{},records:{}},canSave=true;
try{const saved=JSON.parse(localStorage.getItem(KEY));if(saved?.version===1&&saved.records&&saved.seeds)store=saved;}catch{canSave=false;}
let id=topics.some(t=>t.id===store.selected)?store.selected:'array',lesson,frame=0,chosen=null,playing=null,filter='all';
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function save(){
 store.selected=id;if(canSave)try{localStorage.setItem(KEY,JSON.stringify(store));}catch{canSave=false;}
 $('#saveStatus').textContent=canSave?'已保存到此浏览器 · 不自动同步':'无法保存到浏览器，请及时导出记录';
 const passed=new Set(Object.values(store.records).filter(r=>topics.some(t=>t.id===r.topic)&&r.attempts.some(a=>a.correct)).map(r=>r.topic));
 $('#progress').textContent=`${passed.size} / ${topics.length} 个主题已练习通过`;
}
function record(){const key=id+':'+store.seeds[id];if(!store.records[key])store.records[key]={topic:id,seed:store.seeds[id],hints:0,attempts:[]};return store.records[key];}
function stop(){clearInterval(playing);playing=null;$('#play').textContent='自动演示';}
function drawTree(f){
 const positions=Object.fromEntries(f.nodes.map(n=>[n.key,n]));
 const edges=f.edges.map(([a,b])=>`<line x1="${positions[a].x}" y1="${positions[a].y}" x2="${positions[b].x}" y2="${positions[b].y}"/>`).join('');
 const nodes=f.nodes.map((n,i)=>{
  const value=f.kind==='minimax'?(f.values[n.key]??'?'):null;
  return `<g class="${f.active.includes(i)?'active':f.visited?.includes(n.key)?'visited':''}"><circle cx="${n.x}" cy="${n.y}" r="21"/><text x="${n.x}" y="${n.y+5}" text-anchor="middle">${esc(f.kind==='minimax'&&!n.leaf?value:n.label)}</text>${f.kind==='minimax'&&!n.leaf?`<text class="node-role" x="${n.x}" y="${n.y-26}" text-anchor="middle">${n.label}</text>`:''}</g>`;
 }).join('');
 const height=Math.max(...f.nodes.map(n=>n.y))+34;
 const label=f.kind==='tree'?`${lesson.title}。`+f.nodes.map(n=>`${n.key} 位于第 ${n.depth} 层`).join('，'):`极小极大博弈树。当前已求值：${Object.entries(f.values).map(([k,v])=>k+'='+v).join('，')||'还没有'}`;
 $('#visual').innerHTML=`<svg class="graph algorithm-tree" viewBox="0 -12 320 ${height+12}" role="img" aria-label="${esc(label)}">${edges}${nodes}</svg>`;
}
function draw(){
 const f=lesson.frames[frame];let label='绿色框表示这一步正在查看或操作的格子';
 if(f.kind==='tree'||f.kind==='minimax'){
  drawTree(f);label=f.kind==='tree'?`输出：[${f.visited.join(' → ')}] · 调用路径：[${f.path.join(' → ')}]`:'MAX 选大 · MIN 选小 · ? 表示还没有回传 · 叶子是 MAX 的分数';
 }else if(id==='bfs'){
  const pos={A:[150,25],B:[85,80],C:[215,80],D:[40,140],E:[125,140],F:[260,140]};
  $('#visual').innerHTML='<svg class="graph" viewBox="0 0 300 165" role="img" aria-label="从 A 到 F 的六节点树状图">'+[['A','B'],['A','C'],['B','D'],['B','E'],['C','F']].map(([a,b])=>`<line x1="${pos[a][0]}" y1="${pos[a][1]}" x2="${pos[b][0]}" y2="${pos[b][1]}"/>`).join('')+f.items.map((v,i)=>`<g class="${f.active.includes(i)?'active':f.visited.includes(v)?'visited':''}"><circle cx="${pos[v][0]}" cy="${pos[v][1]}" r="17"/><text x="${pos[v][0]}" y="${pos[v][1]+5}" text-anchor="middle">${v}</text></g>`).join('')+'</svg>';
  label=`待探索队列：[${f.queue.join(' → ')}]　已探索：${f.visited.join('、')||'还没有'}`;
 }else{
  const cells=f.items.map((v,i)=>{
   const stone=f.kind==='stones',status=stone?(f.winning[i]===null?'?':f.winning[i]?'胜':'败'):'';
   const value=id==='recursion'?`f(${v})`:stone?`${v}颗`:f.hole===i?'□':v;
   const note=stone?status:id==='stack'?(i===f.items.length-1?'栈顶':''):id==='queue'?(i===0?'队首':i===f.items.length-1?'队尾':''):id==='recursion'?(i===f.items.length-1?'当前调用':'等待返回'):'['+i+']';
   return `<div class="cell ${f.active.includes(i)?'active':''} ${id==='binary'&&(i<f.lo||i>f.hi)?'excluded':''} ${f.heapSize!==undefined&&i>=f.heapSize?'settled':''}" ${stone?`aria-label="${v} 颗，${status==='?'?'尚未求解':status==='胜'?'必胜态':'必败态'}"`:''}><strong>${esc(value)}</strong><small>${esc(note)}</small></div>`;
  }).join('');
  $('#visual').innerHTML=`<div class="cells ${id==='recursion'?'call-stack':''}">${cells||'<span class="cost">'+(id==='recursion'?'调用栈已空。':'空的，等待放入。')+'</span>'}</div>`;
  if(id==='binary')label=`目标 ${lesson.target} · 淡色格已排除`;
  else if(id==='stack')label='左侧是底部，右侧是栈顶';
  else if(id==='queue')label='左侧出队 ← 队首 … 队尾 ← 右侧加入';
  else if(id==='recursion')label=`底部 → 顶部的调用栈；${f.result!==undefined?'本步结果：'+f.result:'新调用先入栈，再等子调用返回'}`;
  else if(f.kind==='stones')label=`每次取 1～${f.limit} 颗 · 胜/败是“轮到当前玩家”的状态，不是固定某个人。`;
  else if(id==='insertion')label=`${f.held!==undefined?'手中暂存：'+f.held+' · ':''}${f.hole!==undefined?'□ 是待填空位 · ':''}${f.prefix!==undefined?'已排好前缀长度：'+f.prefix:'从编号 1 开始逐张插入'}`;
  else if(id==='merge')label=f.left?`左缓冲：[${f.left.join(', ')}] · 右缓冲：[${f.right.join(', ')}]`:f.range?`拆分边界 [${f.range.join(', ')}] · 区间左闭右开`:'分开再合并；合并时比较两个队首';
  else if(id==='quick')label=`${f.pivot!==undefined?'基准：'+f.pivot+' · ':''}${f.boundary!==undefined?'小于基准区的右边界：'+f.boundary:'基准就位后，两侧继续递归'}`;
  else if(id==='heap')label=`数组 i 的孩子：2i+1、2i+2 · ${f.heapSize!==undefined?'堆大小 '+f.heapSize+'，右侧深色底线为已就位区':'先从最后一个父节点向前建堆'}`;
 }
 $('#queueLabel').textContent=label;$('#caption').textContent=f.caption;$('#prev').disabled=frame===0;$('#next').disabled=frame===lesson.frames.length-1;$('#frameCount').textContent=`${frame+1} / ${lesson.frames.length} 步`;
 if(frame===lesson.frames.length-1)stop();
}
function exercise(){
 chosen=null;const e=lesson.exercise;$('#prompt').textContent=e.prompt;
 $('#exercise').dataset.meta=JSON.stringify({data:lesson.data,index:e.index,lo:e.lo,hi:e.hi,...e.meta});
 $('#options').innerHTML='';for(const o of e.options){const b=document.createElement('button');b.textContent=o.label;b.dataset.answer=JSON.stringify(o.value);b.setAttribute('aria-pressed','false');b.onclick=()=>{chosen=o.value;for(const el of $('#options').children)el.setAttribute('aria-pressed',String(el===b));};$('#options').append(b);}
 $('#feedback').textContent='先选择一个答案，再检查。';$('#feedback').dataset.status='idle';$('#hintText').textContent=record().hints?e.hint:'';
}
function select(next){
 stop();id=next;store.seeds[id]??=Math.floor(Math.random()*1000000)+1;lesson=makeLesson(id,store.seeds[id]);frame=0;
 $('#title').textContent=lesson.title+' / '+lesson.subtitle;$('#idea').textContent=lesson.idea;$('#cost').textContent=lesson.cost;$('#python').textContent=lesson.python;
 $('#difficulty').textContent='★'.repeat(lesson.stars)+' · '+lesson.stars+' 星';$('#difficulty').setAttribute('aria-label',`难度 ${lesson.stars} 星`);
 for(const b of $('#topics').children)b.setAttribute('aria-current',String(b.dataset.topic===id));exercise();draw();save();
}
function applyFilter(next){
 filter=next;const visible=topics.filter(t=>filter==='all'||t.stars===Number(filter));
 for(const b of $('#filters').children)b.setAttribute('aria-pressed',String(b.dataset.filter===filter));
 for(const b of $('#topics').children)b.hidden=!visible.some(t=>t.id===b.dataset.topic);
 $('#filterCount').textContent=`显示 ${visible.length} / ${topics.length} 个主题`;
 if(!visible.some(t=>t.id===id))select(visible[0].id);
}
for(const topic of topics){const b=document.createElement('button');b.dataset.topic=topic.id;b.dataset.stars=topic.stars;b.innerHTML=esc(topic.title)+` <span class="topic-stars" aria-label="${topic.stars} 星">${'★'.repeat(topic.stars)}</span><small>${esc(topic.subtitle)}</small>`;b.onclick=()=>select(topic.id);$('#topics').append(b);}
for(const b of $('#filters').children)b.onclick=()=>applyFilter(b.dataset.filter);
$('#next').onclick=()=>{stop();frame=Math.min(lesson.frames.length-1,frame+1);draw();};
$('#prev').onclick=()=>{stop();frame=Math.max(0,frame-1);draw();};
$('#reset').onclick=()=>{stop();frame=0;draw();};$('#end').onclick=()=>{stop();frame=lesson.frames.length-1;draw();};
$('#play').onclick=()=>{if(playing){stop();return;}if(frame===lesson.frames.length-1)frame=0;draw();$('#play').textContent='暂停演示';playing=setInterval(()=>{frame=Math.min(lesson.frames.length-1,frame+1);draw();},1400);};
$('#check').onclick=()=>{
 if(chosen===null){$('#feedback').textContent='先点一个选项，想好后再检查。';return;}
 const correct=judge(lesson.exercise,chosen);record().attempts.push({answer:chosen,correct,hints:record().hints,at:new Date().toISOString()});
 $('#feedback').dataset.status=correct?'correct':'wrong';$('#feedback').textContent=correct?'对了！'+lesson.exercise.explanation:'还不对。再想想规则，或者先看一个提示。第一次答案已保留。';save();
};
$('#hint').onclick=()=>{record().hints++;$('#hintText').textContent=lesson.exercise.hint;save();};
$('#newExercise').onclick=()=>{
 const old=lesson.exercise.prompt;let tries=0;do{store.seeds[id]++;lesson=makeLesson(id,store.seeds[id]);}while(lesson.exercise.prompt===old&&++tries<50);
 stop();frame=0;exercise();draw();if(lesson.exercise.prompt===old)$('#feedback').textContent='这个概念使用同一道练习；新一轮记录已分开保存。试试不看提示，自己解释原因。';save();
};
$('#export').onclick=()=>{save();const data={type:'lucas-lab-algorithm-progress',exportedAt:new Date().toISOString(),...store};const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='Lucas-Lab-算法学习记录.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
document.addEventListener('visibilitychange',()=>{if(document.hidden)stop();});
select(id);applyFilter('all');
