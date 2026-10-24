import test from 'node:test';
import assert from 'node:assert/strict';
import * as M from '../typing/model.mjs';
const {Run,modes,cookiePath}=M;
test('stats retain corrected mistakes and deadline rejects late input',()=>{
 const r=new Run('cat',30);r.update('x',1000);r.update('',2000);r.update('c',3000);r.update('ca',4000);const s=r.update('cat',7000);assert.equal(s.accuracy,75);assert.equal(s.wpm,6);assert.equal(r.finish(8000),null);
 const late=new Run('cat',30);late.update('c',1000);assert.equal(late.update('cat',31001).wpm,0.4);assert.equal(late.value,'c');
});
test('three scenes and safe whole expression prompts',()=>{
 assert.deepEqual(Object.keys(M.scenes),['supply','defense','bridge']);assert.equal(Object.keys(modes).length,3);
 assert.ok(modes.symbols.items.some(x=>x.includes(' ')));for(const m of Object.values(modes))for(const x of m.items)assert.match(x,/^[\x20-\x7e]+$/);
});
test('supply and bridge advance only on exact whole prompt without separator',()=>{
 for(const scene of ['supply','bridge']){const g=new M.Game(scene,'words',30);assert.equal(g.remaining(99999),30);g.input('x',1000);assert.equal(g.completed,0);g.input('',1100);const t=g.target;for(let i=1;i<=t.length;i++)g.input(t.slice(0,i),1200+i);assert.equal(g.completed,1);assert.equal(g.value,'');assert.notEqual(g.target,t);assert.equal(g.attempts,t.length+1);assert.equal(g.hits,t.length);assert.equal(g.progress,1);}
});
test('defense exact laser only, gentle descent, bounded spawning, shield zero fails once',()=>{
 const g=new M.Game('defense','words',60);assert.ok(g.enemies[0].life>=8000&&g.enemies[0].life<=15000);g.input('x',0);assert.equal(g.laser,null);g.input(g.target,100);assert.equal(g.completed,1);assert.ok(g.laser);assert.equal(g.shield,3);g.step(6000);assert.ok(g.enemies.length<=3);g.step(20000);assert.ok(g.shield<3);assert.ok(g.enemies.length<=3);
 let result;for(let t=21000;t<=59000&&!result;t+=1000)result=g.step(t);assert.equal(result.reason,'shield');assert.equal(g.shield,0);assert.equal(g.done,true);assert.equal(g.step(61000),null);assert.equal(g.input('cat',62000),null);
 const jump=new M.Game('defense','words',60);jump.input('x',0);jump.step(25000);assert.equal(jump.shield,2);assert.ok(jump.enemies.length<=1,'no overdue spawn flood');
});
test('elapsed truthful; pause removes ranking eligibility and cannot farm wall time',()=>{
 const g=new M.Game('bridge','symbols',30);g.input('x',1000);g.pause(2000);assert.equal(g.eligible,false);assert.equal(g.remaining(90000),29);g.resume(90000);assert.equal(g.remaining(91000),28);const s=g.step(120000);assert.equal(s.elapsed,30);assert.equal(s.eligible,false);assert.equal(g.step(150000),null);
 const late=new M.Game('supply','words',30);late.input('c',0);const r=late.input('cat',31000);assert.equal(late.completed,0);assert.equal(r.elapsed,30);
});
test('all 18 boards separate, bounded and compact even maximum numbers',()=>{
 let rows=[];for(const scene of Object.keys(M.scenes))for(const mode of Object.keys(modes))for(const duration of [30,60])for(let n=0;n<8;n++)rows=M.addScore(rows,[scene,mode,duration,1999.9,100,4102444799999-n]);
 assert.equal(rows.length,36);assert.ok(M.encodeScores(rows).length<3800);assert.deepEqual(M.decodeScores(M.encodeScores(rows)),rows.map(r=>[...r.slice(0,5),Math.floor(r[5]/1000)*1000]));
 assert.equal(rows.filter(r=>r[0]==='defense'&&r[1]==='words'&&r[2]===30).length,2);
});
test('expression whitespace exactness and full supply/bridge cycles',()=>{
 const d=new M.Game('defense','symbols',60);d.input('x=1',0);assert.equal(d.completed,0);assert.equal(d.laser,null);d.input('x = 2',100);assert.equal(d.completed,0);d.input('x = ',200);d.input('x = 1',300);assert.equal(d.completed,1);assert.ok(d.laser);
 for(const scene of ['supply','bridge']){const g=new M.Game(scene,'python',30);for(let i=0;i<12;i++)g.input(g.target,i*1000);assert.equal(g.progress,12);assert.equal(g.completed,12);assert.equal(g.done,false);}
});
test('strict cookie numeric, schema and board validation',()=>{
 const row=['supply','words',30,10,90,1700000000000];
 for(const [index,value] of [[0,'constructor'],[1,'bad'],[2,90],[3,-1],[3,2001],[4,1.5],[4,101],[5,0]]){const bad=[...row];bad[index]=value;assert.deepEqual(M.addScore([],bad),[]);}
 for(const r of [[[0,1.5,90,1700000000]],[[0,-1,90,1700000000]],[[18,1,90,1700000000]],[[0,1,101,1700000000]],[[0,1,90,0]],[[0,1,90,1700000000,0]]])assert.deepEqual(M.decodeScores(encodeURIComponent(JSON.stringify({v:2,r}))),[]);
});
test('invalid cookies rejected, previous boards migrate to supply, path derived',()=>{
 for(const raw of ['%ZZ','null','{}','x'.repeat(4000),encodeURIComponent(JSON.stringify({v:2,r:[[99,0,30,1,90,1700000000]]}))])assert.deepEqual(M.decodeScores(raw),[]);
 assert.deepEqual(M.decodeScores(encodeURIComponent(JSON.stringify([['words',30,12,90,1700000000000]]))),[['supply','words',30,12,90,1700000000000]]);
 assert.equal(cookiePath('/lucas-lab/typing/index.html'),'/lucas-lab/typing/');
 assert.deepEqual(M.addScore([] ,['bad','words',30,0,100,1700000000000]),[]);
});
