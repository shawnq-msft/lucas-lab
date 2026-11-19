const normalize = (value) =>
  String(value ?? "")
    .normalize("NFKC")
    .toLocaleLowerCase()
    .trim();
export function matchesEntry(entry, category = "all", query = "") {
  const tokens = normalize(query).split(/\s+/).filter(Boolean);
  const haystack = normalize(entry.search);
  return (
    (category === "all" || entry.category === category) &&
    tokens.every((token) => haystack.includes(token))
  );
}
export function countCategories(entries) {
  const counts = { all: entries.length };
  for (const entry of entries)
    counts[entry.category] = (counts[entry.category] ?? 0) + 1;
  return counts;
}
