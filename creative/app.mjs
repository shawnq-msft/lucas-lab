const storageKey = 'lucas-lab-creative-guide-v1';
const checkboxes = [...document.querySelectorAll('[data-check]')];
let saved = {};
let storageAvailable = true;
try {
  const parsed = JSON.parse(localStorage.getItem(storageKey) || '{}');
  if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) saved = parsed;
} catch { storageAvailable = false; }
for (const input of checkboxes) input.checked = saved[input.dataset.check] === true;

function updateChecklist(persist = true) {
  const state = Object.fromEntries(checkboxes.map(input => [input.dataset.check, input.checked]));
  document.querySelector('#progress').textContent = `${checkboxes.filter(input => input.checked).length} / ${checkboxes.length} 项已勾选（仅表示自行确认）`;
  if (persist) {
    try { localStorage.setItem(storageKey, JSON.stringify(state)); }
    catch { storageAvailable = false; }
  }
  document.querySelector('#storageStatus').textContent = storageAvailable
    ? '本页清单保存在当前浏览器；没有上传或报名。可导出备份。'
    : '浏览器存储不可用，清单只在本次页面有效；请及时导出。';
}
checkboxes.forEach(input => input.addEventListener('change', () => updateChecklist()));
updateChecklist(false);
document.querySelector('#resetPlan').addEventListener('click', () => {
  checkboxes.forEach(input => { input.checked = false; });
  updateChecklist();
});
document.querySelector('#exportPlan').addEventListener('click', () => {
  const lines = [
    'Lucas Lab · 创意项目准备清单',
    '规则参考核验：2026-11-12；以最新正式规则和本校通知为准。',
    '勾选不代表已报名、获准复用或已通过测试。',
    '',
    ...checkboxes.map(input => `[${input.checked ? 'x' : ' '}] ${input.parentElement.textContent.trim()}`),
    '',
    '作品真实贡献、原始数据、隐私授权、AI使用说明及失败记录需另行保存。',
    '学校AI赛完整附件尚待取得，不能用本清单代替规则审查。'
  ];
  const url = URL.createObjectURL(new Blob([lines.join('\n')], {type:'text/plain;charset=utf-8'}));
  const link = document.createElement('a');
  link.href = url;
  link.download = 'lucas-creative-checklist.txt';
  document.body.append(link); link.click(); link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});
document.querySelector('#printGuide').addEventListener('click', () => {
  document.querySelectorAll('details').forEach(element => { element.open = true; });
  window.print();
});

const fields = [
  ['eligibility','资格／分组'], ['team','组队'], ['theme','主题'],
  ['deliverables','材料／评审'], ['platform','平台／形态'], ['fit','毛豆策略'],
  ['date','时间'], ['unknown','待确认']
];
function textElement(tag, text, className) {
  const element = document.createElement(tag);
  element.textContent = text;
  if (className) element.className = className;
  return element;
}
function renderContest(contest) {
  const article = document.createElement('article');
  article.className = 'contest';
  article.dataset.contest = contest.id;
  article.dataset.kind = contest.kind;
  article.append(textElement('span', contest.priority, 'tag'));
  article.append(textElement('h3', contest.name));
  article.append(textElement('p', contest.evidence, 'evidence'));
  const description = document.createElement('dl');
  for (const [field,label] of fields) {
    const row = document.createElement('div');
    row.append(textElement('dt',label),textElement('dd',contest[field]));
    description.append(row);
  }
  article.append(description);
  const source = document.createElement('a');
  source.href = contest.source; source.textContent = '查看原始来源 →';
  article.append(source);
  if (contest.rulesSource) {
    article.append(document.createTextNode('　'));
    const rules = document.createElement('a');
    rules.href = contest.rulesSource; rules.textContent = '规则附件／FAQ →';
    article.append(rules);
  }
  return article;
}
function applyFilter(kind) {
  const articles = [...document.querySelectorAll('.contest')];
  for (const article of articles) article.hidden = kind !== 'all' && article.dataset.kind !== kind;
  for (const button of document.querySelectorAll('[data-filter]')) button.setAttribute('aria-pressed',String(button.dataset.filter === kind));
  document.querySelector('#filterCount').textContent = `${articles.filter(article => !article.hidden).length} / ${articles.length} 个赛项；规则状态见每项证据说明。`;
}
for (const button of document.querySelectorAll('[data-filter]')) button.addEventListener('click', () => applyFilter(button.dataset.filter));
try {
  const response = await fetch(new URL('./contests.json', import.meta.url));
  if (!response.ok) throw new Error('rules unavailable');
  const data = await response.json();
  const fragment = document.createDocumentFragment();
  data.contests.forEach(contest => fragment.append(renderContest(contest)));
  document.querySelector('#contestList').replaceChildren(fragment);
  applyFilter('all');
} catch {
  document.querySelector('#filterCount').textContent = '赛事详表暂未加载，请刷新或查看页末官方来源与规则摘要数据。其余攻略可继续阅读。';
}
