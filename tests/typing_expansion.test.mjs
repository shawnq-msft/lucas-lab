import test from 'node:test';
import assert from 'node:assert/strict';
import * as M from '../typing/model.mjs';
const newScenes=['mining','rescue','race'];
const make=(scene,mode='words',speed=20)=>new M.Game(scene,mode,30,{speed,rng:()=>.37});
const complete=(g,now=0)=>{for(const ch of g.target)g.input(g.value+ch,now++);};
test('six missions retain legacy bridge index and append new score indexes',()=>{
 assert.deepEqual(Object.keys(M.scenes),['supply','defense','assault',...newScenes]);
 for(const [scene,index] of [['bridge',3],['mining',4],['rescue',5],['race',6]]){
  const rows=[[scene,'words',30,scene==='bridge'?0:20,20,100,1700000000000,100]];
  const raw=M.encodeScores(rows);assert.equal(JSON.parse(decodeURIComponent(raw)).r[0][0],index);assert.deepEqual(M.decodeScores(raw),rows);
 }
});
for(const [scene,event] of [['mining','drill'],['rescue','tether'],['race','boost']]){
 test(scene+' exact completion only drives distinct mechanics and objectives',()=>{
  const g=make(scene),target=g.target,initial=g.objective();
  g.input('~',0);assert.deepEqual(g.objective(),initial);assert.equal(g.events.at(-1).type,'error');
  g.input(target[0],1);g.input(g.value+'~',2);const prefix=g.value;
  for(const invalid of ['',prefix+'ab','wrong',prefix+'\n'])g.input(invalid,3);
  assert.equal(g.value,prefix);assert.equal(g.completed,0);assert.equal(g.events.some(e=>e.type===event),false);
  for(const ch of target.slice(1))g.input(g.value+ch,4);
  assert.equal(g.completed,1);assert.equal(g.events.filter(e=>e.type===event).length,1);assert.equal(g.objective().current,1);
  const goal=g.objective().goal;for(let n=1;n<goal;n++)complete(g,100*n);
  assert.equal(g.objective().cycles,1);assert.equal(g.objective().current,0);assert.ok(g.events.some(e=>e.type==='objective'));
  if(scene==='mining'){assert.deepEqual(g.minerals,[1,1,1]);assert.equal(g.crystals,3);}
  if(scene==='rescue')assert.equal(g.savedPods,5);
  if(scene==='race'){const state=g.raceState(1000);assert.ok(state.player>state.rival);assert.ok(g.overtakes>=1);assert.equal(g.gates,5);assert.ok(state.boost);}
 });
 test(scene+' strict phrase threshold, length lifetime, bounded spawns and misses',()=>{
  for(const hits of [29,30,31]){const g=make(scene,'words',60);g.started=0;g.hits=hits;g.completed=3;g.enemies=[];g.spawn(60000);assert.equal(g.target.includes(' '),hits>30);}
  const g=make(scene,'words',60);assert.ok(make(scene,'symbols',5).travelTime(25)>g.travelTime(3));g.input('~',0);
  g.step(18000);assert.equal(g.events.filter(e=>e.type==='miss').length,1);assert.equal(g.shield,2);assert.ok(g.enemies.length<=2);
  g.step(18001);assert.equal(g.shield,2);assert.equal(g.objective().cycles,0);
 });
}
test('race player/rival positions change independently with time and input',()=>{
 const g=make('race');g.input('~',0);const a=g.raceState(0),b=g.raceState(1200);
 assert.ok(b.player>a.player&&b.rival>a.rival);assert.notEqual(b.player-a.player,b.rival-a.rival);
 complete(g,1201);const c=g.raceState(1300);assert.ok(c.player>b.player+50);assert.ok(c.boost);assert.equal(g.raceState(5000).boost,false);
});
test('star awards require full eligible time round with precise thresholds and save once',()=>{
 for(const scene of Object.keys(M.scenes))for(const [completed,hits,attempts,want] of [[2,100,100,0],[3,85,100,1],[8,90,100,2],[15,95,100,3],[15,949,1000,2]]){
  const g=make(scene);g.started=0;g.completed=completed;g.hits=hits;g.attempts=attempts;
  assert.equal(g.step(30000).stars,want,scene);assert.equal(g.step(40000),null);
 }
 for(const kind of ['pause','shield','abandon','early']){const g=make('rescue');g.started=0;g.completed=20;g.hits=g.attempts=100;
  if(kind==='pause'){g.pause(100);g.resume(200);assert.equal(g.step(30200).stars,0);}
  else if(kind==='shield'){g.shield=0;assert.equal(g.finish(30000,'shield').stars,0);}
  else assert.equal(g.finish(kind==='early'?1000:30000,kind==='early'?'time':'abandon').stars,0);
 }
});
test('tiny separate stars codec is strict bounded and never lowers a personal best',()=>{
 assert.equal(typeof M.encodeStars,'function');let best={};for(const scene of Object.keys(M.scenes)){best=M.addStars(best,scene,3);best=M.addStars(best,scene,1);}
 const raw=M.encodeStars(best);assert.ok(raw.length<200);assert.deepEqual(M.decodeStars(raw),best);
 for(const raw of ['%ZZ','null','{}',encodeURIComponent(JSON.stringify({v:1,s:[3,3,3,3,3,9]})),encodeURIComponent(JSON.stringify({v:1,s:[3,3,3]})),'x'.repeat(200)])assert.deepEqual(M.decodeStars(raw),{});
 assert.deepEqual(M.addStars({},'bridge',3),{});assert.deepEqual(M.addStars({},'race',4),{});
 const old=M.decodeScores(encodeURIComponent(JSON.stringify({v:2,r:[[12,100,90,1700000000]]})));assert.equal(old[0][0],'bridge');
 let rows=[];for(const scene of Object.keys(M.scenes))for(const mode of Object.keys(M.modes))for(const duration of [30,60])for(const speed of [5,20,60])for(let i=0;i<3;i++)rows=M.addScore(rows,[scene,mode,duration,speed,20,90,1700000000000+i,100]);
 assert.ok(M.encodeScores(rows).length<3800);assert.equal(M.decodeScores(M.encodeScores(rows)).length,rows.length);
});
