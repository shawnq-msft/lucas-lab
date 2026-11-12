export const STORAGE_KEY = 'lucas-lab-camp101-v1';
const clone = value => JSON.parse(JSON.stringify(value));
export const normalize = value => String(value ?? '').normalize('NFKC').trim().toLowerCase().replace(/\s+/gu, ' ');
export const emptyState = () => ({schema:1,first:null,attempts:[],draft:null});
export function grade(exam, answers = {}, parentScores = {}) {
  const result={autoEarned:0,autoMax:0,parentEarned:0,pending:0,earned:0,unaided:0,assisted:0,max:0,items:{}};
  for (const q of exam.sections.flatMap(s=>s.questions)) {
    const entry=answers[q.id] || {}; let earned=0,status='incorrect';
    result.max+=q.points;
    if(q.type==='manual') {
      const score=parentScores[q.id];
      if(typeof score==='number' && Number.isFinite(score) && score>=0 && score<=q.points) {
        earned=score;status='parent';result.parentEarned+=earned;
      } else { status='pending';result.pending+=q.points; }
    } else {
      result.autoMax+=q.points;
      const accepted=q.type==='choice'?[q.answer]:(q.answers || []);
      if(normalize(entry.answer) && accepted.some(a=>normalize(a)===normalize(entry.answer))) {earned=q.points;status='correct';}
      result.autoEarned+=earned;
    }
    result.earned+=earned;
    if(!entry.help || entry.help==='H0') result.unaided+=earned; else result.assisted+=earned;
    result.items[q.id]={earned,status,max:q.points};
  }
  return result;
}
export function startAttempt(state, now=Date.now()) {
  if(state.draft) return state;
  return {...clone(state),draft:{startedAt:now,answers:{}}};
}
export const remainingMs = (draft,exam,now=Date.now()) => Math.max(0, draft.startedAt+exam.minutes*60000-now);
export function submitAttempt(state,exam,now=Date.now(),reason='manual') {
  if(!state.draft) return state;
  const next=clone(state);
  const attempt={...clone(next.draft),submittedAt:Math.min(now,next.draft.startedAt+exam.minutes*60000),reason,parentScores:{},contentVersion:exam.version || ''};
  next.attempts.push(attempt);
  if(!next.first) next.first=clone(attempt);
  next.draft=null;
  return next;
}
const record=x=>x!==null && typeof x==='object' && !Array.isArray(x);
const validAnswers=x=>record(x) && Object.values(x).every(a=>record(a) && typeof a.answer==='string' && (a.reasoning===undefined || typeof a.reasoning==='string') && ['H0','H1','H2','H3',undefined].includes(a.help));
const validDraft=x=>record(x) && Number.isFinite(x.startedAt) && x.startedAt>=0 && validAnswers(x.answers);
const validAttempt=x=>validDraft(x) && Number.isFinite(x.submittedAt) && record(x.parentScores);
export function loadState(storage) {
  try {
    const raw=storage.getItem(STORAGE_KEY);
    if(raw===null) return {state:emptyState(),warning:''};
    const x=JSON.parse(raw);
    if(!record(x) || x.schema!==1 || !Array.isArray(x.attempts) || !x.attempts.every(validAttempt) || !(x.first===null || validAttempt(x.first)) || !(x.draft===null || validDraft(x.draft)) || Boolean(x.first)!==Boolean(x.attempts.length)) throw Error('invalid');
    return {state:x,warning:''};
  } catch {return {state:emptyState(),warning:'无法读取本地记录（记录损坏或浏览器禁用存储）。本次可继续，请及时导出；旧数据不会自动恢复。'};}
}
export function saveState(storage,state) {
  try {storage.setItem(STORAGE_KEY,JSON.stringify(state));return true;} catch {return false;}
}
