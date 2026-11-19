// Progressive enhancement: the complete guide and original links live in HTML.
const form = document.querySelector('#filters');
const category = document.querySelector('#category');
const difficulty = document.querySelector('#difficulty');
const cards = [...document.querySelectorAll('.course-card')];
const status = document.querySelector('#result-count');
const empty = document.querySelector('#empty');

function filterCourses() {
  let visible = 0;
  for (const card of cards) {
    const matches = (category.value === 'all' || card.dataset.category === category.value)
      && (difficulty.value === 'all' || card.dataset.difficulty === difficulty.value);
    card.hidden = !matches;
    if (matches) visible += 1;
  }
  status.textContent = `显示 ${visible} / ${cards.length} 门课程`;
  empty.hidden = visible !== 0;
}

form.addEventListener('change', filterCourses);
form.addEventListener('submit', event => event.preventDefault());
form.addEventListener('reset', () => {
  // Set explicitly: reset's default action normally runs after the listener.
  category.value = 'all';
  difficulty.value = 'all';
  filterCourses();
});
// Route links still work after narrowing the shelf: reveal their destination.
function revealAnchor() {
  const target = cards.find(card => `#${card.id}` === location.hash);
  if (target?.hidden) {
    form.reset();
    target.scrollIntoView({ block: 'start' });
  }
}
window.addEventListener('hashchange', revealAnchor);
filterCourses();
form.hidden = false;
revealAnchor();
