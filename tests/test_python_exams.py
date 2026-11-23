"""Original primary mock-exam content and engine acceptance tests (stdlib)."""
import ast
import copy
import importlib.util
import io
import json
from pathlib import Path
import unittest
from contextlib import redirect_stdout

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'python-exams'


def load(name):
    path = DATA / name
    assert path.exists(), f'缺少交付文件：{path}'
    return json.loads(path.read_text(encoding='utf-8'))


class ContentTests(unittest.TestCase):
    def test_required_files_exist(self):
        for name in ['exams.json', 'solutions.json', 'rules.md']:
            self.assertTrue((DATA / name).exists(), f'缺少交付文件：{name}')

    def test_engine_file_exists(self):
        self.assertTrue((DATA / 'engine.py').exists(), '缺少游戏引擎：engine.py')

    def test_contract_counts_scope_and_no_answer_leak(self):
        data, solutions = load('exams.json'), load('solutions.json')
        self.assertEqual(data['version'], '1')
        self.assertIn('非官方真题', data['notice'])
        self.assertEqual(len(data['scope']), 12)
        self.assertEqual([e['id'] for e in data['exams']], ['A', 'B', 'C'])
        titles, prompts, starters, refs = [], [], [], []
        for exam in data['exams']:
            self.assertEqual(exam['minutes'], 60)
            self.assertEqual(len(exam['choices']), 8)
            self.assertEqual(len(exam['tasks']), 4)
            self.assertEqual(8 * 2 + 4 * 3 * 7, 100)
            ids = [q['id'] for q in exam['choices'] + exam['tasks']]
            self.assertEqual(len(ids), len(set(ids)))
            for q in exam['choices']:
                for field in ['id', 'title', 'prompt', 'options', 'topic']:
                    self.assertIn(field, q)
                self.assertEqual(len(q['options']), 4)
                self.assertEqual(len(set(q['options'])), 4)
                prompts.append(q['prompt'] + q.get('code', ''))
                self.assertIn(q['topic'], data['scope'])
            for task in exam['tasks']:
                for field in ['id', 'title', 'topic', 'goal', 'starter', 'api', 'inputs', 'budget', 'required', 'scenario']:
                    self.assertIn(field, task)
                self.assertGreater(task['budget'], 0)
                self.assertIsInstance(task['inputs'], dict)
                self.assertIn('模拟', task['goal'])
                titles.append(task['title'])
                starters.append(task['starter'])
                ref = solutions['exams'][exam['id']]['tasks'][task['id']]
                refs.append(ref['solution'])
                self.assertTrue(ref['explanation'])
                self.assertTrue(ref['commonMistakes'])
                ast.parse(ref['solution'])
        for values in [titles, prompts, starters, refs]:
            self.assertEqual(len(values), len(set(values)))
        def check(value):
            if isinstance(value, dict):
                for k, v in value.items():
                    self.assertNotIn(k, ['answer', 'explanation', 'solution', 'commonMistakes'])
                    check(v)
            elif isinstance(value, list):
                for v in value:
                    check(v)
        check(data)
        topics = {q['topic'] for e in data['exams'] for q in e['choices'] + e['tasks']}
        self.assertEqual(topics, set(data['scope']))

    def test_all_choice_answers_independently(self):
        data, solutions = load('exams.json'), load('solutions.json')
        conceptual = {('A', 'q1'): '键盘', ('A', 'q2'): 'for', ('B', 'q1'): '断开可疑链接，向老师报告', ('C', 'q1'): '内存中的数据断电后通常丢失'}
        count = 0
        for exam in data['exams']:
            for q in exam['choices']:
                ref = solutions['exams'][exam['id']]['choices'][q['id']]
                self.assertIn(ref['answer'], range(4))
                self.assertTrue(ref['explanation'])
                if q.get('code'):
                    out = io.StringIO()
                    env = {'input': lambda prompt='': q.get('stdin', '')}
                    with redirect_stdout(out):
                        exec(compile(q['code'], '<independent-choice>', 'exec'), env)
                    expected = out.getvalue().strip()
                else:
                    expected = conceptual[(exam['id'], q['id'])]
                self.assertEqual(q['options'][ref['answer']], expected, (exam['id'], q['id']))
                count += 1
        self.assertEqual(count, 24)


class EngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = DATA / 'engine.py'
        if not path.exists():
            raise unittest.SkipTest(f'缺少游戏引擎：{path}；由文件存在性测试报告')
        spec = importlib.util.spec_from_file_location('exam_engine', path)
        assert spec is not None and spec.loader is not None
        cls.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)
        cls.evaluate = staticmethod(cls.module.evaluate)
        cls.exams = load('exams.json')['exams']
        cls.solutions = load('solutions.json')['exams']

    def assert_result(self, result):
        self.assertEqual(set(result), {'passed', 'stars', 'error', 'reason', 'actionCount', 'trace'})
        json.dumps(result, ensure_ascii=False)
        self.assertIsInstance(result['passed'], bool)
        self.assertIn(result['stars'], range(4))
        self.assertLessEqual(len(result['trace']), 150)
        for frame in result['trace']:
            self.assertEqual(set(frame), {'width', 'height', 'actors', 'switches', 'enemies', 'walls', 'message'})
            for actor in frame['actors']:
                self.assertIn(actor['name'], ['hero', 'luke'])
                self.assertIn(actor['direction'], range(4))
                self.assertTrue(0 <= actor['x'] < frame['width'])
                self.assertTrue(0 <= actor['y'] < frame['height'])
            self.assertIsInstance(frame['message'], str)

    def test_all_twelve_references_three_stars_and_exact_goals(self):
        count = 0
        for exam in self.exams:
            for task in exam['tasks']:
                with self.subTest(exam=exam['id'], task=task['id']):
                    r = self.evaluate(exam['id'], task['id'], self.solutions[exam['id']]['tasks'][task['id']]['solution'])
                    self.assert_result(r)
                    self.assertEqual((r['passed'], r['stars'], r['error']), (True, 3, ''), r)
                    self.assertEqual(r['actionCount'], task['budget'])
                    last = r['trace'][-1]
                    for actor in last['actors']:
                        self.assertEqual([actor['x'], actor['y']], task['scenario']['endpoints'][actor['name']])
                    self.assertTrue(all(s['pressed'] == s['required'] for s in last['switches']))
                    self.assertTrue(all(not e['active'] for e in last['enemies']))
                    count += 1
        self.assertEqual(count, 12)

    def test_reference_actions_match_independent_untransformed_cpython(self):
        for exam in self.exams:
            for task in exam['tasks']:
                with self.subTest(exam=exam['id'], task=task['id']):
                    source = self.solutions[exam['id']]['tasks'][task['id']]['solution']
                    recorded = []
                    class Recorder:
                        def __init__(self, name):
                            self.name = name
                        def move(self, n):
                            recorded.append(f'{self.name}.move({n})')
                        def turnLeft(self):
                            recorded.append(f'{self.name}.turnLeft()')
                        def turnRight(self):
                            recorded.append(f'{self.name}.turnRight()')
                        def attack(self):
                            recorded.append(f'{self.name}.attack()')
                        def press(self):
                            recorded.append(f'{self.name}.press()')
                    hero, luke = Recorder('hero'), Recorder('luke')
                    env = copy.deepcopy(task['inputs'])
                    env.update({'hero': hero, 'luke': luke, 'move': hero.move,
                                'turnLeft': hero.turnLeft, 'turnRight': hero.turnRight,
                                'attack': hero.attack, 'press': hero.press})
                    exec(compile(source, '<independent-reference>', 'exec'), env)
                    result = self.evaluate(exam['id'], task['id'], source)
                    self.assertEqual([f['message'] for f in result['trace'][1:-1]], recorded)
                    self.assertEqual(len(recorded), task['budget'])

    def test_empty_and_wrong_submissions_all_twelve(self):
        for exam in self.exams:
            for task in exam['tasks']:
                for source in ['', 'print("完成")', 'move(999)', 'unknown()']:
                    with self.subTest(exam=exam['id'], task=task['id'], source=source):
                        r = self.evaluate(exam['id'], task['id'], source)
                        self.assert_result(r)
                        self.assertEqual((r['passed'], r['stars']), (False, 0))
                        self.assertTrue(r['reason'])
                        self.assertTrue(r['trace'])
                        self.assertEqual(r['trace'][0]['actors'], task['scenario']['actors'])

    def test_missing_feature_and_excess_actions_each_cost_one_star(self):
        r = self.evaluate('A', 't2', 'move(2)\npress()\nmove(2)\npress()\nmove(2)\npress()')
        self.assertEqual((r['passed'], r['stars']), (True, 2), r)
        both = self.evaluate('A', 't2', 'move(0)\n' + 'move(2)\npress()\n' * 3)
        self.assertEqual((both['passed'], both['stars']), (True, 1))

    def test_redundant_movement_gets_two_stars(self):
        source = self.solutions['A']['tasks']['t2']['solution'] + '\nmove(-1)\nmove(1)'
        r = self.evaluate('A', 't2', source)
        self.assertEqual((r['passed'], r['stars'], r['actionCount']), (True, 2, 8), r)

    def test_zero_move_counts_as_action_not_lines_or_steps(self):
        source = self.solutions['A']['tasks']['t2']['solution'] + '\nmove(0)'
        r = self.evaluate('A', 't2', source)
        self.assertEqual((r['stars'], r['actionCount']), (2, 7))
        r = self.evaluate('A', 't1', self.solutions['A']['tasks']['t1']['solution'])
        self.assertEqual(r['actionCount'], 4)  # 10 walked squares still two move calls

    def test_negative_movement_keeps_direction(self):
        r = self.evaluate('A', 't1', 'luke.move(6)\nluke.attack()\nluke.move(-4)')
        luke = next(a for a in r['trace'][-1]['actors'] if a['name'] == 'luke')
        self.assertEqual((luke['x'], luke['y'], luke['direction']), (2, 0, 0))

    def test_receivers_are_independent(self):
        r = self.evaluate('A', 't1', 'move(1)\nluke.move(2)\nhero.turnRight()\nluke.turnLeft()')
        self.assertEqual(r['trace'][-1]['actors'], [
            {'name': 'hero', 'x': 1, 'y': 2, 'direction': 1},
            {'name': 'luke', 'x': 2, 'y': 0, 'direction': 3}])
        self.assertEqual(self.evaluate('A', 't2', 'luke.move(1)')['stars'], 0)

    def test_mutated_inputs_and_maps_reset(self):
        source = self.solutions['C']['tasks']['t3']['solution']
        first, second = self.evaluate('C', 't3', source), self.evaluate('C', 't3', source)
        self.assertEqual(first, second)
        self.assertEqual(first['stars'], 3)
        self.assertEqual(self.evaluate('C', 't3', '')['trace'][0]['switches'][0]['pressed'], False)
        self.assertEqual(load('exams.json')['exams'][2]['tasks'][2]['inputs']['route'], [1, 2])

    def test_invalid_actions_fail_and_preserve_last_legal_state(self):
        cases = [('A', 't2', 'press()'), ('A', 't2', 'attack()'),
                 ('A', 't4', 'move(4)\npress()'), ('A', 't2', 'move(2)\npress()\npress()'),
                 ('A', 't1', 'luke.move(7)'), ('A', 't2', 'move(-1)'),
                 ('C', 't1', 'hero.turnRight()\nhero.move(1)'),
                 ('A', 't2', 'move(True)'), ('A', 't2', 'move(1.5)'),
                 ('A', 't2', 'turnLeft(1)'), ('A', 't2', 'hero.goto(2,1)')]
        for eid, tid, source in cases:
            with self.subTest(source=source):
                r = self.evaluate(eid, tid, source)
                self.assert_result(r)
                self.assertEqual((r['passed'], r['stars']), (False, 0))
                self.assertTrue(r['error'])
        r = self.evaluate('A', 't1', 'luke.move(7)')
        self.assertEqual(r['trace'][-1]['actors'][1]['x'], 6)

    def test_forbidden_code_and_syntax(self):
        forbidden = ['import os', 'from math import sqrt', 'open("x")', 'eval("1")',
                     'exec("move(2)")', 'globals()', 'getattr(hero,"move")(1)',
                     'hero.__class__', '().__class__.__bases__', 'def f():\n    pass',
                     'class X:\n    pass', '(lambda: 1)()', 'try:\n    pass\nexcept:\n    pass',
                     '__builtins__', 'move = print', 'hero = 1', 'move(', 'move(**{})',
                     'while True:\n    pass', 'while True:\n    move(0)',
                     'for i in range(999999999):\n    move(0)',
                     'x = "a" * 999999999', 'x = 2 ** 999999999', 'x = [0] * 999999999',
                     'x = 1 << 999999999', 'x = "x"\nwhile True:\n    x = x.replace("x", x)',
                     'x = [i for i in range(999999)]', 'print("a")\n' * 2000]
        for source in forbidden:
            with self.subTest(source=source[:80]):
                r = self.evaluate('A', 't2', source)
                self.assert_result(r)
                self.assertEqual((r['passed'], r['stars']), (False, 0))
                self.assertTrue(r['error'])

    def test_runtime_errors_are_friendly_and_trace_restored(self):
        import sys
        old = sys.gettrace()
        for source in ['x=1/0', 'move(missing)', 'x=steps[99]', 'x={}["key"]', 'move(input())']:
            r = self.evaluate('A', 't2', source)
            self.assertEqual(r['stars'], 0)
            self.assertTrue(r['error'])
            self.assertNotIn('Traceback', r['error'])
            self.assertIs(sys.gettrace(), old)

    def test_unknown_identifiers_and_invalid_source(self):
        for eid, tid, source in [('Z', 't1', ''), ('A', 'bad', ''), ('A', 't1', None), ('A', 't1', 'x' * 20001)]:
            r = self.evaluate(eid, tid, source)
            self.assert_result(r)
            self.assertEqual(r['stars'], 0)
            self.assertTrue(r['error'])

    def test_augmented_list_alias_matches_cpython(self):
        source = 'a = [2]\nb = a\na += [2, 2]\nfor step in b:\n    move(step)\n    press()'
        self.assertEqual(self.evaluate('A', 't2', source)['stars'], 3)
        source = 'd = {"steps": [2]}\nb = d["steps"]\nd["steps"] *= 3\nfor step in b:\n    move(step)\n    press()'
        self.assertEqual(self.evaluate('A', 't2', source)['stars'], 3)

    def test_augmented_subscript_reads_old_value_before_rhs(self):
        source = 'd = {"n": 1}\nd["n"] += d.pop("n")\nfor i in range(3):\n    move(d["n"])\n    press()'
        self.assertEqual(self.evaluate('A', 't2', source)['stars'], 3)

    def test_limits_have_distinct_termination_reasons(self):
        cases = [('while True:\n    pass', '3000行次'),
                 ('while True:\n    move(0)', '128次'),
                 ('x = "x" * 1001', '重复操作'),
                 ('x = [1]\nx.append(x)', '循环引用'),
                 ('move(129)', '128格')]
        for code, expected in cases:
            r = self.evaluate('A', 't2', code)
            self.assertEqual(r['stars'], 0)
            self.assertIn(expected, r['error'])

    def test_augmented_subscript_repetition_guard_is_preallocation(self):
        # Safe-size reproduction: native repeat would happen and fail only after allocation.
        r = self.evaluate('A', 't2', 'a = ["x"]\na[0] *= 1001')
        self.assertIn('重复操作结果过大', r['error'])
        r = self.evaluate('A', 't2', 'a = {"n": 2}\na["n"] **= 129')
        self.assertIn('幂或移位次数过大', r['error'])

    def test_total_object_graph_guard(self):
        r = self.evaluate('A', 't2', 'a = [1] * 100\nb = [a] * 101')
        self.assertIn('数据总量', r['error'])

    def test_dict_augmented_assignment_retains_primary_semantics(self):
        source = 'd = {"distance": 1}\nd["distance"] += 1\nfor i in range(3):\n    move(d["distance"])\n    press()'
        r = self.evaluate('A', 't2', source)
        self.assertEqual(r['stars'], 3, r)

    def test_engine_contains_no_solution_file_dependency(self):
        text = (DATA / 'engine.py').read_text(encoding='utf-8')
        self.assertNotIn('solutions.json', text)
        self.assertNotIn('luke.move(advance)', text)


if __name__ == '__main__':
    unittest.main()
