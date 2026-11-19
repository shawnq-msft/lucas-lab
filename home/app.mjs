import { matchesEntry, countCategories } from "./model.mjs";
const cards = [...document.querySelectorAll(".entry[data-category]")];
const entries = cards.map((card) => ({
  category: card.dataset.category,
  search: card.dataset.search + " " + card.textContent,
}));
const buttons = [...document.querySelectorAll("[data-filter]")];
const search = document.querySelector("#search");
const result = document.querySelector("#resultCount");
const empty = document.querySelector("#emptyState");
const counts = countCategories(entries);
const labels = {
  all: "全部",
  code: "编程与算法",
  science: "科学与工程",
  contests: "备赛与测评",
  family: "家庭参考",
};
let category = "all";
for (const el of document.querySelectorAll("[data-count]"))
  el.textContent = String(counts[el.dataset.count] ?? 0);
function render() {
  let visible = 0;
  cards.forEach((card, index) => {
    const match = matchesEntry(entries[index], category, search.value);
    card.hidden = !match;
    if (match) visible++;
  });
  buttons.forEach((button) =>
    button.setAttribute(
      "aria-pressed",
      String(button.dataset.filter === category),
    ),
  );
  result.textContent = `${labels[category]} · 显示 ${visible} / ${entries.length} 个模块`;
  empty.hidden = visible !== 0;
}
function reset() {
  category = "all";
  search.value = "";
  render();
  search.focus({ preventScroll: true });
}
buttons.forEach((button) =>
  button.addEventListener("click", () => {
    category = button.dataset.filter;
    render();
  }),
);
search.addEventListener("input", render);
document.querySelector("#resetFilters").addEventListener("click", reset);
document.querySelector("#showAll").addEventListener("click", reset);
for (const control of [
  ...buttons,
  search,
  document.querySelector("#resetFilters"),
])
  control.disabled = false;
render();
