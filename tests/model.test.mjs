import test from 'node:test';
import assert from 'node:assert/strict';
import {topics,makeLesson,judge} from '../algorithms/model.mjs';
test('all topics generate valid demos and answerable exercises',()=>{
 assert.ok(topics.length>=16);
 for(let seed=1;seed<30;seed++) for(const topic of topics){
  const l=makeLesson(topic.id,seed);
  assert.ok(l.frames.length>=3,topic.id);
  assert.ok(l.frames.every(f=>f.caption && Array.isArray(f.items)));
  assert.ok(l.exercise.options.length>=3);
  assert.equal(l.exercise.options.filter(o=>judge(l.exercise,o.value)).length,1);
  assert.ok(l.exercise.hint);
 }
});
test('array uses zero-based indexing',()=>{const l=makeLesson('array',1);assert.equal(l.exercise.answer,l.data[l.exercise.index]);});
test('stack is last in first out; queue first in first out',()=>{
 const s=makeLesson('stack',2),q=makeLesson('queue',2);
 assert.equal(s.exercise.answer,s.data.at(-1));assert.equal(q.exercise.answer,q.data[0]);
});
test('binary search only uses sorted data and shrinks to target',()=>{
 for(let seed=1;seed<30;seed++){
 const l=makeLesson('binary',seed);assert.deepEqual(l.data,[...l.data].sort((a,b)=>a-b));
 assert.equal(l.exercise.answer,Math.floor((l.exercise.lo+l.exercise.hi)/2));
 assert.equal(l.frames.at(-1).items[l.frames.at(-1).active[0]],l.target);
 }
});
test('bubble trace ends sorted and preserves all values',()=>{
 for(let seed=1;seed<30;seed++){const l=makeLesson('bubble',seed);assert.deepEqual(l.frames.at(-1).items,[...l.data].sort((a,b)=>a-b));assert.equal(l.exercise.answer,0);assert.ok(l.data[0]>l.data[1]);}
});
test('BFS trace visits each node once in queue order',()=>{
 const l=makeLesson('bfs',1);assert.deepEqual(l.order,['A','B','C','D','E','F']);assert.equal(l.exercise.answer,'C');
 assert.equal(l.frames.at(-1).visited.length,6);
});
test('wrong answers are rejected strictly',()=>{for(const t of topics){const e=makeLesson(t.id,3).exercise;assert.equal(judge(e,'not-an-answer'),false);}});
