import {Game,scenes,modes,addScore,decodeScores,encodeScores,cookiePath} from './model.mjs';
const $=id=>document.getElementById(id),NAME='lucas_lab_typing_v1';
const attrs=`; Path=${cookiePath(location.pathname)}; SameSite=Lax${location.protocol==='https:'?'; Secure':''}`;
function rawCookie(){try{return document.cookie.split(';').map(v=>v.trim()).find(v=>v.startsWith(NAME+'='))?.slice(NAME.length+1)||'';}catch{return '';}}
function writeCookie(value,maxAge=31536000){try{document.cookie=`${NAME}=${value}; Max-Age=${maxAge}${attrs}`;return rawCookie()===(maxAge?value:'');}catch{return false;}}
function storageMessage(ok){$('storageStatus').textContent=ok?'成绩使用本地 Cookie 保存。':'此浏览器无法保存 Cookie：成绩仅在当前页面临时显示，刷新会丢失。请检查浏览器设置。';$('storageStatus').classList.toggle('storage-warning',!ok);}
let scores=decodeScores(rawCookie()),game,ready=false,composing=false;
storageMessage(writeCookie(encodeScores(scores)));
function ranking(){
 const scene=$('scene').value,mode=$('mode').value,duration=Number($('duration').value);
 $('groupLabel').textContent=`${scenes[scene].label} · ${modes[mode].label} · ${duration} 秒`;
 const rows=scores.filter(r=>r[0]===scene&&r[1]===mode&&r[2]===duration);
 $('scores').querySelector('tbody').replaceChildren(...rows.map((row,i)=>{
  const tr=document.createElement('tr');for(const value of [i+1,`玩家 · ${new Date(row[5]).toLocaleString('zh-CN',{month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit'})}`,row[3].toFixed(1),`${row[4]}%`]){const td=document.createElement('td');td.textContent=value;tr.append(td);}return tr;
 }));$('empty').hidden=rows.length>0;
}
function node(className,text='',style=''){const el=document.createElement('div');el.className=className;el.textContent=text;el.style.cssText=style;return el;}
function arena(now){
 const a=$('arena'),n=game.completed,t=game.elapsed(now);a.replaceChildren(node('arena-title',scenes[game.scene].label));
 if(game.scene==='supply'){
  const load=n===0?0:(n-1)%8+1,ships=Math.floor(n/8);
  a.append(node('planet'),node('dock'),node('ship',`货舱 ${load} / 8`));
  for(let i=0;i<load;i++)a.append(node('crate','✦',`left:${8+(i%4)*7}%;bottom:${42+Math.floor(i/4)*29}px`));
  a.append(node('cargo-label',`已装 ${n} 箱 · 已发船 ${ships} 艘`));a.setAttribute('aria-label',`补给站：已装 ${n} 箱，已发船 ${ships} 艘`);
 }else if(game.scene==='bridge'){
  const step=n===0?0:(n-1)%10+1;
  a.append(node('planet'),node('bank left'),node('bank right'),node('finish-flag','⚑'));
  for(let i=0;i<step;i++)a.append(node('bridge-segment','',`left:${10+i*8}%`));
  const robot=node('robot','🤖',`left:${7+step*8}%`);robot.id='robot';robot.dataset.step=step;a.append(robot,node('arena-summary',`已修 ${n} 段 · 到站 ${Math.floor(n/10)} 次`));a.setAttribute('aria-label',`修桥：已建 ${n} 段，机器人前进到第 ${step} 段`);
 }else{
  a.append(node('shield-wall','',`--shield:${game.shield/3}`),node('turret','♜'));
  for(const [i,e] of game.enemies.entries()){
   const el=node(`enemy${i===0?' active':''}`,e.text,`left:${e.x}%;top:${12+68*Math.max(0,Math.min(1,(t-e.born)/e.life))}%`);el.dataset.enemy=e.id;el.setAttribute('aria-label',`${i===0?'当前键盘目标':'待拦截'}：${e.text}`);a.append(el);
  }
  if(game.laser&&t-game.laser.at<650){
   const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.id='laser';svg.classList.add('laser-layer');svg.setAttribute('viewBox','0 0 100 100');svg.setAttribute('preserveAspectRatio','none');svg.setAttribute('aria-label','炮台激光命中目标');svg.setAttribute('role','img');
   const line=document.createElementNS(svg.namespaceURI,'line');for(const [k,v] of Object.entries({x1:50,y1:91,x2:game.laser.x,y2:game.laser.y,class:'laser-beam'}))line.setAttribute(k,v);
   const impact=document.createElementNS(svg.namespaceURI,'circle');for(const [k,v] of Object.entries({cx:game.laser.x,cy:game.laser.y,r:3,class:'impact'}))impact.setAttribute(k,v);svg.append(line,impact);a.append(svg);
  }
  a.setAttribute('aria-label',`太空防御：护盾 ${game.shield}/3，已拦截 ${n} 项，当前目标 ${game.target||'等待下一项'}`);
 }
}
function render(){
 const now=Date.now(),text=game.target,value=game.value;
 $('target').dataset.text=text;$('target').replaceChildren(...[...(text||'等待下一项目标…')].map((ch,i)=>{const el=document.createElement('span');el.textContent=ch;el.className=i<value.length?(ch===value[i]?'correct':'wrong'):(i===value.length?'current':'');return el;}));
 if(!composing)$('entry').value=value;$('entry').disabled=!ready||game.done||game.pausedAt!==null;$('entry').readOnly=!text;
 $('remaining').textContent=game.remaining(now);$('completed').textContent=game.completed;
 $('correctCount').textContent=game.correct+[...value].filter((c,i)=>c===text[i]).length;
 $('shieldBox').hidden=game.scene!=='defense';$('shield').textContent=game.shield;$('shieldMeter').value=game.shield;
 $('resume').hidden=game.pausedAt===null;$('start').disabled=ready&&!game.done;$('restart').disabled=!ready;
 arena(now);
}
function finish(result){
 if(!result)return;
 $('result').textContent=`${result.reason==='shield'?'防御失败：护盾已归零！':'任务完成！'} 完成 ${result.completed} 项 · 速度 ${result.wpm.toFixed(1)} WPM · 准确率 ${result.accuracy}% · 用时 ${result.elapsed.toFixed(1)} 秒。${result.eligible?'已结算本轮成绩。':'本轮曾暂停，仅练习，不入榜。'}`;
 $('status').textContent='可以重新开始，或换一个任务。';
 if(result.eligible){const persisted=decodeScores(rawCookie());scores=addScore(persisted.length?persisted:scores,[game.scene,game.mode,game.duration,result.wpm,result.accuracy,Date.now()]);const encoded=encodeScores(scores);storageMessage(encoded.length<3800&&writeCookie(encoded));ranking();}
 render();
}
function setup(start=false){
 ready=start;composing=false;game=new Game($('scene').value,$('mode').value,Number($('duration').value));$('result').textContent='';
 $('hint').textContent={supply:'完整打对一项，装上一箱星矿；8 箱发一艘船。',defense:'金色边框 ⌨ 是当前目标。完整打对才开炮；漏一项扣 1 护盾，0 点立即失败。',bridge:'完整打对一项，建一段真实桥面，机器人向前一步；10 段到站。'}[game.scene];
 $('status').textContent=start?'准备好了：输入第一个字符才开始计时。':'准备好就开始吧。';render();ranking();if(start)$('entry').focus();
}
function tick(){if(!ready||game.done||game.pausedAt!==null)return;const result=game.step(Date.now());render();finish(result);}
function input(){
 if(composing||!ready||game.done||game.pausedAt!==null)return;
 const result=game.input($('entry').value,Date.now());render();finish(result);
 if(!game.done)$('status').textContent=game.target?'照着当前目标输入，红色表示错误，可退格修改。':'拦截成功！等待下一项目标…';
}
$('start').addEventListener('click',()=>setup(true));$('restart').addEventListener('click',()=>setup(true));
for(const id of ['scene','mode','duration'])$(id).addEventListener('change',()=>setup(false));
$('entry').addEventListener('compositionstart',()=>{composing=true;});$('entry').addEventListener('compositionend',()=>{composing=false;input();});
$('entry').addEventListener('input',e=>{if(!e.isComposing)input();});
function reject(e){e.preventDefault();$('status').textContent='请用键盘自己输入，不支持粘贴或拖入文字。';}
for(const name of ['paste','drop'])$('entry').addEventListener(name,reject);
$('entry').addEventListener('beforeinput',e=>{if(['insertFromPaste','insertFromDrop','insertReplacementText','historyUndo','historyRedo'].includes(e.inputType))reject(e);});
$('clear').addEventListener('click',()=>{if(!confirm('清空所有场景、内容和时长的本地成绩？此操作不能撤销。'))return;scores=[];storageMessage(writeCookie('',0));ranking();});
document.addEventListener('visibilitychange',()=>{if(document.hidden&&ready){const result=game.pause(Date.now());render();finish(result);if(game.pausedAt!==null)$('status').textContent='已自动暂停。返回后点击继续，本轮仅练习、不入榜。';}else tick();});
$('resume').addEventListener('click',()=>{if(document.hidden)return;game.resume(Date.now());render();$('status').textContent='继续练习：本轮因暂停不入榜。';$('entry').focus();});
window.addEventListener('focus',tick);setInterval(tick,100);setup();
