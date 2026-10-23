import test from 'node:test';
import assert from 'node:assert/strict';
import * as model from '../algorithms/model.mjs';
const ids=['insertion','merge','quick','heap','recursion','preorder','inorder','postorder','stones','minimax'];
test('catalog preserves six lessons and adds graded advanced lessons',()=>{
 for(const id of ['array','stack','queue','binary','bubble','bfs',...ids])assert.ok(model.topics.some(t=>t.id===id),id);
 for(const t of model.topics)assert.ok([1,2,3].includes(t.stars),t.id);
 assert.equal(model.topics.find(t=>t.id==='heap').stars,3);
 assert.equal(model.topics.find(t=>t.id==='minimax').stars,3);
});
test('sort traces handle empty/singleton/duplicates/negative and random data without mutation',()=>{
 assert.equal(typeof model.sortTrace,'function','sortTrace API');
 let s=942;const random=()=>{s=(Math.imul(s,1664525)+1013904223)>>>0;return s;};
 const cases=[[],[9],[2,2,2],[4,-1,0,4,-8],[1,2,3],[3,2,1],...Array.from({length:80},()=>Array.from({length:random()%12},()=>random()%21-10))];
 for(const id of ['insertion','merge','quick','heap'])for(const data of cases){
  const original=[...data],frames=model.sortTrace(id,data);
  assert.deepEqual(data,original);assert.deepEqual(frames.at(-1).items,[...data].sort((a,b)=>a-b),`${id}: ${data}`);
  assert.ok(frames.every(f=>f.caption&&f.active.every(i=>i>=0&&i<f.items.length)));
 }
});
test('recursion reaches base case before unwinding and returns factorial',()=>{
 assert.equal(typeof model.recursionTrace,'function');
 for(let n=0;n<=7;n++){
  const frames=model.recursionTrace(n);let expected=1;for(let i=2;i<=n;i++)expected*=i;
  assert.equal(frames.at(-1).result,expected);assert.deepEqual(frames.at(-1).stack,[]);
  const base=frames.findIndex(f=>f.phase==='base');assert.ok(base>=0);
  assert.ok(frames.slice(0,base).every(f=>f.phase!=='return'));
  assert.equal(frames[base].result,1);
 }
});
const tree={value:'A',left:{value:'B',left:{value:'D'},right:{value:'E'}},right:{value:'C',right:{value:'F'}}};
test('binary tree visits actual left/right pointers in three orders',()=>{
 assert.equal(typeof model.treeTrace,'function');
 for(const [mode,expected] of Object.entries({preorder:['A','B','D','E','C','F'],inorder:['D','B','E','A','C','F'],postorder:['D','E','B','F','C','A']})){
  assert.deepEqual(model.treeTrace(tree,mode).at(-1).visited,expected);
  assert.deepEqual(model.treeTrace(null,mode).at(-1).visited,[]);
 }
});
test('takeaway dynamic programming agrees with exhaustive optimal play',()=>{
 assert.equal(typeof model.stoneTrace,'function');
 const win=(n,k)=>n>0&&Array.from({length:Math.min(n,k)},(_,i)=>i+1).some(t=>!win(n-t,k));
 for(let k=1;k<=3;k++)for(let n=0;n<=13;n++){
  const last=model.stoneTrace(n,k).at(-1);assert.equal(last.winning[n],win(n,k));
  const expected=Array.from({length:Math.min(n,k)},(_,i)=>i+1).filter(t=>!win(n-t,k));
  assert.deepEqual(last.moves,expected);
 }
});
test('minimax alternates MAX/MIN and agrees with independent recursion',()=>{
 assert.equal(typeof model.minimaxTrace,'function');
 const solve=(t,max=true)=>typeof t==='number'?t:(max?Math.max:Math.min)(...t.map(c=>solve(c,!max)));
 for(const t of [[[3,8],[4,1]],[[[-3,2],[9,0]],[[4,5],[7,-2]]],[[2,2],[2,2]],-5]){
  const frames=model.minimaxTrace(t);assert.equal(frames.at(-1).result,solve(t));
  assert.ok(frames.every(f=>f.caption));
 }
});
function independent(l){const e=l.exercise,m=e.meta;
 switch(l.id){
 case 'insertion':return JSON.stringify([...m.input.slice(0,2)].sort((a,b)=>a-b).concat(m.input.slice(2)));
 case 'merge':return JSON.stringify([...m.left,...m.right].sort((a,b)=>a-b));
 case 'quick':return m.input.filter(x=>x<m.pivot).length;
 case 'heap':return Math.max(...m.input);
 case 'recursion':{let v=1;for(let i=2;i<=m.n;i++)v*=i;return v;}
 case 'preorder':case 'inorder':case 'postorder':{const walk=t=>!t?[]:l.id==='preorder'?[t.value,...walk(t.left),...walk(t.right)]:l.id==='inorder'?[...walk(t.left),t.value,...walk(t.right)]:[...walk(t.left),...walk(t.right),t.value];return walk(m.tree).join(' → ');}
 case 'stones':{const wins=[false];for(let n=1;n<=m.n;n++)wins[n]=Array.from({length:Math.min(n,m.limit)},(_,i)=>i+1).some(k=>!wins[n-k]);return Array.from({length:Math.min(m.n,m.limit)},(_,i)=>i+1).find(k=>!wins[m.n-k])??0;}
 case 'minimax':return Math.max(...m.leaves.map(pair=>Math.min(...pair)));
 }
}
test('advanced predictions are deterministic varied and independently correct',()=>{
 for(const id of ids){const prompts=new Set();for(let seed=1;seed<=30;seed++){
  const l=model.makeLesson(id,seed);assert.deepEqual(l,model.makeLesson(id,seed));
  assert.ok(l.frames.length>=3,id);assert.ok(l.python.length>80,id);assert.ok(l.cost.includes('O('),id);
  assert.equal(l.exercise.answer,independent(l),`${id}/${seed}`);
  assert.equal(l.exercise.options.filter(o=>model.judge(l.exercise,o.value)).length,1,id);
  assert.ok(l.exercise.options.length>=3,id);prompts.add(l.exercise.prompt);
 }assert.ok(prompts.size>=3,id+' variants');}
});
