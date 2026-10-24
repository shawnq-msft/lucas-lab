export const scenes={supply:{label:'星矿补给站'},defense:{label:'太空防御'},bridge:{label:'星际修桥'}};
export const modes={
 words:{label:'英语起步',items:['cat','dog','sun','moon','book','tree','fish','bird','happy','apple','green','hello']},
 python:{label:'Python 关键词',items:['if','else','for','in','while','def','return','print','input','range','True','False']},
 symbols:{label:'代码表达式',items:['x = 1','print(x)','a[0]','x + 2','len(a)','x == 3','a = [1, 2]','print("hi")','x != 0']}
};
for(const m of Object.values(modes))m.text=m.items.join(' ');
// Count inserted/replaced characters, not deletions. Errors remain after correction.
function countEdit(owner,value,target){
 let p=0;while(p<value.length&&p<owner.value.length&&value[p]===owner.value[p])p++;
 let s=0;while(s<value.length-p&&s<owner.value.length-p&&value.at(-1-s)===owner.value.at(-1-s))s++;
 for(let i=p;i<value.length-s;i++){owner.attempts++;if(value[i]===target[i])owner.hits++;}
 owner.value=value;
}
export class Run{
 constructor(target,duration){Object.assign(this,{target,duration,started:null,done:false,value:'',attempts:0,hits:0});}
 remaining(now){return this.started===null?this.duration:Math.max(0,Math.ceil((this.started+this.duration*1000-now)/1000));}
 update(value,now){if(this.done)return null;if(this.started!==null&&now>=this.started+this.duration*1000)return this.finish(now);value=value.slice(0,this.target.length);if(value===this.value)return null;if(this.started===null&&value.length)this.started=now;countEdit(this,value,this.target);return value===this.target?this.finish(now,true):null;}
 finish(now,complete=false){if(this.done||this.started===null||(!complete&&now<this.started+this.duration*1000))return null;this.done=true;const elapsed=Math.max(1,Math.min(this.duration,(now-this.started)/1000)),correct=[...this.value].filter((c,i)=>c===this.target[i]).length;return {elapsed,wpm:Math.round(correct/5/(elapsed/60)*10)/10,accuracy:this.attempts?Math.round(this.hits/this.attempts*100):0};}
}
// Pausing freezes active time and permanently removes leaderboard eligibility.
export class Game{
 constructor(scene,mode,duration){
  if(!Object.hasOwn(scenes,scene)||!Object.hasOwn(modes,mode)||![30,60].includes(duration))throw new Error('Invalid game');
  Object.assign(this,{scene,mode,duration,started:null,pausedAt:null,pausedTotal:0,eligible:true,done:false,value:'',attempts:0,hits:0,correct:0,completed:0,progress:0,index:0,shield:3,enemies:[],laser:null,nextSpawn:5000,serial:0});
  if(scene==='defense')this.spawn(0);
 }
 elapsed(now){return this.started===null?0:Math.max(0,(this.pausedAt??now)-this.started-this.pausedTotal);}
 remaining(now){return Math.max(0,Math.ceil(this.duration-this.elapsed(now)/1000));}
 get target(){return this.scene==='defense'?(this.enemies[0]?.text||''):modes[this.mode].items[this.index%modes[this.mode].items.length];}
 spawn(at){const n=this.serial++;this.enemies.push({id:n,text:modes[this.mode].items[n%modes[this.mode].items.length],born:at,life:Math.max(9000,14000-n*250),x:18+(n%3)*30});}
 step(now){
  if(this.done||this.started===null||this.pausedAt!==null)return null;
  const t=Math.min(this.duration*1000,this.elapsed(now));
  if(this.scene==='defense'){
   const missed=this.enemies.filter(e=>t-e.born>=e.life);
   if(missed.length){this.shield=Math.max(0,this.shield-missed.length);this.enemies=this.enemies.filter(e=>!missed.includes(e));this.value='';}
   if(this.shield===0)return this.finish(now,'shield');
   // One fresh spawn at current elapsed time, never a timestamp catch-up flood.
   if(t>=this.nextSpawn&&t<this.duration*1000){if(this.enemies.length<3)this.spawn(t);this.nextSpawn=t+Math.max(4000,5500-this.serial*80);}
  }
  return this.elapsed(now)>=this.duration*1000?this.finish(now,'time'):null;
 }
 input(value,now){
  if(this.done||this.pausedAt!==null)return null;
  const end=this.step(now);if(end)return end;
  if(!this.target)return null;
  value=value.slice(0,120);if(value===this.value)return null;
  if(this.started===null&&value.length)this.started=now;
  countEdit(this,value,this.target);
  if(value===this.target){this.correct+=value.length;this.completed++;this.progress++;this.index++;
   if(this.scene==='defense'){const e=this.enemies.shift();this.laser={...e,at:this.elapsed(now),y:12+68*Math.min(1,(this.elapsed(now)-e.born)/e.life)};}
   this.value='';
  }
  return null;
 }
 pause(now){if(this.done||this.started===null||this.pausedAt!==null)return null;const end=this.step(now);if(end)return end;this.pausedAt=now;this.eligible=false;return null;}
 resume(now){if(this.pausedAt!==null){this.pausedTotal+=now-this.pausedAt;this.pausedAt=null;}}
 finish(now,reason){
  if(this.done||this.started===null)return null;this.done=true;
  const elapsed=Math.max(1,Math.min(this.duration,this.elapsed(now)/1000));
  const correct=this.correct+[...this.value].filter((c,i)=>c===this.target[i]).length;
  return {reason,elapsed,wpm:Math.min(2000,Math.round(correct/5/(elapsed/60)*10)/10),accuracy:this.attempts?Math.round(this.hits/this.attempts*100):0,eligible:this.eligible,completed:this.completed};
 }
}
const sk=Object.keys(scenes),mk=Object.keys(modes);
const valid=r=>Array.isArray(r)&&r.length===6&&Object.hasOwn(scenes,r[0])&&Object.hasOwn(modes,r[1])&&[30,60].includes(r[2])&&Number.isFinite(r[3])&&r[3]>=0&&r[3]<=2000&&Number.isInteger(r[4])&&r[4]>=0&&r[4]<=100&&Number.isSafeInteger(r[5])&&r[5]>=1577836800000&&r[5]<=4102444800000;
export function addScore(scores,row){
 const all=[...(Array.isArray(scores)?scores:[]),row].filter(valid),out=[];
 for(const s of sk)for(const m of mk)for(const d of [30,60])out.push(...all.filter(r=>r[0]===s&&r[1]===m&&r[2]===d).sort((a,b)=>b[3]-a[3]||b[4]-a[4]||b[5]-a[5]).slice(0,2));return out;
}
export function encodeScores(rows){return encodeURIComponent(JSON.stringify({v:2,r:addScore(rows,null).map(r=>[sk.indexOf(r[0])*6+mk.indexOf(r[1])*2+(r[2]===60?1:0),Math.round(r[3]*10),r[4],Math.floor(r[5]/1000)])}));}
export function decodeScores(raw){
 try{
  if(typeof raw!=='string'||raw.length>=3800)return [];
  const data=JSON.parse(decodeURIComponent(raw));let rows;
  if(Array.isArray(data)){if(data.length>30)return [];rows=data.map(r=>Array.isArray(r)&&r.length===5?['supply',...r]:null);}
  else{if(!data||data.v!==2||Object.keys(data).length!==2||!Array.isArray(data.r)||data.r.length>36)return [];
   rows=data.r.map(r=>{if(!Array.isArray(r)||r.length!==4||!r.every(Number.isSafeInteger)||r[0]<0||r[0]>=18)return null;const k=r[0];return [sk[Math.floor(k/6)],mk[Math.floor(k%6/2)],k%2?60:30,r[1]/10,r[2],r[3]*1000];});}
  if(!rows.every(valid))return [];return addScore(rows,null);
 }catch{return [];}
}
export function cookiePath(path){return path.endsWith('/')?path:path.slice(0,path.lastIndexOf('/')+1);}
