import test from 'node:test';
import assert from 'node:assert/strict';
import {translationTrace,computerTrace} from '../computer/model.mjs';
test('compiler translates all before output, interpreter executes before later syntax error',()=>{
 const source='SET 3\nADD 4\nPRINT\nOOPS';
 const c=translationTrace(source,'compiler'),i=translationTrace(source,'interpreter');
 assert.ok(c.at(-1).error);assert.deepEqual(c.at(-1).output,[]);
 assert.ok(i.at(-1).error);assert.deepEqual(i.at(-1).output,[7]);
});
test('both modes execute valid source with distinct translation order and reject invalid values',()=>{
 for(const mode of ['compiler','interpreter']){
  const t=translationTrace('SET 3\nADD 4\nPRINT',mode);assert.deepEqual(t.at(-1).output,[7]);
  assert.equal(t.filter(s=>s.phase==='execute').length,3);
  assert.ok(translationTrace('SET frog',mode).at(-1).error);
 }
 const t=translationTrace('SET 3\nPRINT','compiler');assert.equal(t[1].phase,'translate');assert.equal(t[2].phase,'translate');assert.equal(t[3].phase,'execute');
});
test('stored-program computer fetches decodes executes and shares memory for data and instructions',()=>{
 const t=computerTrace(8,5);assert.equal(t.at(-1).output,13);assert.equal(t.at(-1).memory[12],13);
 assert.deepEqual(t.slice(1,4).map(x=>x.phase),['fetch','decode','execute']);
 assert.equal(t[1].pc,1);assert.equal(t[1].ir,'LOAD 10');assert.equal(t[3].acc,8);
 assert.equal(t.at(-1).halted,true);assert.equal(t[0].memory[0],'LOAD 10');assert.equal(t[0].memory[10],8);
 for(const [a,b] of [[0,0],[-4,2],[99,99]])assert.equal(computerTrace(a,b).at(-1).output,a+b);
 assert.throws(()=>computerTrace(NaN,2));
});
