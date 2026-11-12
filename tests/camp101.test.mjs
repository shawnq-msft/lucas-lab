import test from 'node:test';
import assert from 'node:assert/strict';
const model = await import('../camp101/model.mjs').catch(() => ({}));
const questions = [
 {id:'m01',type:'fill',points:6,answers:['12']},
 {id:'m02',type:'choice',points:6,answer:'B'},
 {id:'c01',type:'manual',points:5},
];
const exam={minutes:50,sections:[{questions}]};
test('normalization preserves meaning but folds width, case and whitespace',()=>{
 assert.equal(model.normalize('  ＡＢＣ\n１２  '),'abc 12');
 assert.notEqual(model.normalize('1 / 2'),model.normalize('12'));
 assert.equal(model.normalize(null),'');
});
test('grading separates automatic, assisted and pending; manual is never NLP graded',()=>{
 const result=model.grade(exam,{m01:{answer:'１２',help:'H0'},m02:{answer:'B',help:'H2'},c01:{answer:'a beautiful essay',help:'H0'}});
 assert.equal(result.autoEarned,12);assert.equal(result.autoMax,12);
 assert.equal(result.unaided,6);assert.equal(result.assisted,6);
 assert.equal(result.pending,5);assert.equal(result.earned,12);
 assert.equal(result.items.c01.status,'pending');
});
test('explicit parent partial credit is validated and never counted automatically',()=>{
 const a={c01:{answer:'essay',help:'H1'}};
 const result=model.grade(exam,a,{c01:3});
 assert.equal(result.parentEarned,3);assert.equal(result.pending,0);assert.equal(result.assisted,3);
 for(const score of [-1,6,'3',NaN])assert.equal(model.grade(exam,a,{c01:score}).pending,5);
 assert.equal(model.grade(exam,a,{c01:0}).pending,0);
});
test('first submitted baseline and attempts are cloned, immutable across retries and parent scores',()=>{
 let state=model.emptyState(); state=model.startAttempt(state,1000);
 state.draft.answers.m01={answer:'12',help:'H0'};
 state=model.submitAttempt(state,exam,2000,'manual');
 const first=JSON.stringify(state.first);state.attempts[0].parentScores.c01=4;
 state=model.startAttempt(state,3000);state.draft.answers.m01={answer:'0',help:'H3'};
 state=model.submitAttempt(state,exam,4000,'manual');
 assert.equal(JSON.stringify(state.first),first);assert.equal(state.attempts.length,2);
 assert.equal(state.first.answers.m01.answer,'12');assert.equal(state.draft,null);
 assert.equal(model.submitAttempt(state,exam,5000).attempts.length,2);
});
test('deadline is wall-clock based including zero start and reload; expiry timestamp is capped',()=>{
 const s=model.startAttempt(model.emptyState(),0);
 assert.equal(model.remainingMs(s.draft,exam,1),2999999);
 assert.equal(model.remainingMs(s.draft,exam,3000000),0);
 const submitted=model.submitAttempt(s,exam,5000000,'timeout');
 assert.equal(submitted.first.submittedAt,3000000);assert.equal(submitted.first.reason,'timeout');
});
test('storage rejects malformed histories and handles unavailable storage safely',()=>{
 for(const value of ['bad','null','[]','{"draft":{"startedAt":"oops"}}','{"first":{},"attempts":[]}']){
  const loaded=model.loadState({getItem:()=>value});assert.deepEqual(loaded.state,model.emptyState());assert.ok(loaded.warning);
 }
 assert.deepEqual(model.loadState({getItem:()=>null}).state,model.emptyState());
 assert.ok(model.loadState({getItem(){throw Error('denied')}}).warning);
 assert.equal(model.saveState({setItem(){throw Error('full')}},model.emptyState()),false);
 const s=model.startAttempt(model.emptyState(),100);let raw;
 assert.equal(model.saveState({setItem:(k,v)=>{assert.equal(k,'lucas-lab-camp101-v1');raw=v}},s),true);
 assert.deepEqual(model.loadState({getItem:()=>raw}).state,s);
});
