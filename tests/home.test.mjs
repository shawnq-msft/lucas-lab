import test from "node:test";
import assert from "node:assert/strict";
import { matchesEntry, countCategories } from "../home/model.mjs";
const entries = [
  { category: "science", search: "四足机器人 ToF RL 视觉 语音" },
  { category: "code", search: "Python 闯关" },
  { category: "contests", search: "101 科创营 摸底 模拟卷" },
  { category: "family", search: "小升初 选校" },
];
test("all, category and search combine without reordering entries", () => {
  assert.equal(entries.filter((x) => matchesEntry(x, "all", "")).length, 4);
  assert.deepEqual(
    entries.filter((x) => matchesEntry(x, "science", "语音")),
    [entries[0]],
  );
  assert.equal(
    entries.filter((x) => matchesEntry(x, "code", "机器人")).length,
    0,
  );
  assert.equal(
    entries.filter((x) => matchesEntry(x, "all", "  ｐＹｔｈｏｎ  ")).length,
    1,
  );
  assert.equal(
    entries.filter((x) => matchesEntry(x, "all", "不存在")).length,
    0,
  );
});
test("multiple search tokens require all, and totals come from actual entries", () => {
  assert.equal(
    entries.filter((x) => matchesEntry(x, "all", "机器人 RL")).length,
    1,
  );
  assert.equal(
    entries.filter((x) => matchesEntry(x, "all", "机器人 Python")).length,
    0,
  );
  assert.deepEqual(countCategories(entries), {
    all: 4,
    science: 1,
    code: 1,
    contests: 1,
    family: 1,
  });
  assert.deepEqual(countCategories([]), { all: 0 });
});
test("blank, absent and compatibility-normalized queries are safe", () => {
  assert.equal(matchesEntry(entries[0], "all", "\t  \n"), true);
  assert.equal(matchesEntry(entries[0], "science", null), true);
  assert.equal(matchesEntry({ category: "code" }, "all", "Python"), false);
  assert.equal(
    matchesEntry(
      { category: "code", search: "C++ Ｐｙｔｈｏｎ" },
      "code",
      "c++ python",
    ),
    true,
  );
  assert.equal(matchesEntry(entries[0], "unknown", ""), false);
});
