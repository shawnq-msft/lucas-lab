import unittest
try:
    import engine
except ModuleNotFoundError:
    engine = None

SOLUTIONS = {
1: 'turnRight()\nmove(2)\nturnLeft()\nmove(4)\nturnLeft()\nmove(2)',
2: 'for coin in coins:\n    goto(coin)',
3: 'for monster in monsters:\n    card = getDict(monster)\n    if card["hostile"]:\n        goto(monster)\n        attack()',
4: 'def nearer(target):\n    if hero.dTo(target) < hygeia.dTo(target):\n        return hero\n    else:\n        return hygeia\n\nfor monster in monsters:\n    mover = nearer(monster)\n    mover.goto(monster)\n    mover.attack()',
5: 'password = message[1:7:2].lower()\nunlock(password)\nmove(4)',
6: 'def select(items, limit):\n    chosen = []\n    for item in items:\n        card = getDict(item)\n        if card["safe"] and card["value"] >= limit:\n            chosen.append(item)\n    return chosen\n\nfor item in select(coins, limit):\n    goto(item)'
}

class Tests(unittest.TestCase):
    def evaluate(self, n, code, variant=0):
        self.assertIsNotNone(engine, 'Missing playable Python simulation engine')
        return engine.evaluate(n, code, variant)

    def test_all_six_reference_solutions(self):
        for n, code in SOLUTIONS.items():
            with self.subTest(level=n):
                r = self.evaluate(n, code)
                self.assertTrue(r['passed'], r)
                self.assertGreater(len(r['trace']), 1)
    def test_empty_code_never_passes(self):
        for n in SOLUTIONS:
            self.assertFalse(self.evaluate(n, '')['passed'])
    def test_wall_collision_is_visible(self):
        r = self.evaluate(1, 'move(4)')
        self.assertFalse(r['passed'])
        self.assertIn('墙', r['error'])
    def test_negative_move_is_rejected(self):
        r = self.evaluate(1, 'move(-1)')
        self.assertFalse(r['passed'])
        self.assertIn('非负整数',r['error'])
    def test_python_syntax_error_has_line(self):
        r=self.evaluate(2,'for coin in coins\n    goto(coin)')
        self.assertIn('SyntaxError',r['error'])
        self.assertEqual(r['errorLine'],1)
    def test_friendly_target_must_not_be_attacked(self):
        r=self.evaluate(3,'for monster in monsters:\n    goto(monster)\n    attack()')
        self.assertFalse(r['passed'])
        self.assertIn('友好',r['error'])
    def test_far_attack_is_rejected(self):
        r=self.evaluate(3,'attack()')
        self.assertFalse(r['passed'])
    def test_function_return_must_drive_selected_actor(self):
        bad=SOLUTIONS[4].replace('mover.goto(monster)','hero.goto(monster)').replace('mover.attack()','hero.attack()')
        self.assertFalse(self.evaluate(4,bad)['passed'])
    def test_password_case_is_significant(self):
        self.assertFalse(self.evaluate(5,'unlock("SUN")\nmove(4)')['passed'])
    def test_gate_blocks_unopened_route(self):
        r=self.evaluate(5,'move(4)')
        self.assertFalse(r['passed'])
        self.assertIn('门',r['error'])
    def test_unsafe_or_low_value_coins_fail(self):
        r=self.evaluate(6,'def select(items, limit):\n    return items\nfor item in select(coins, limit):\n    goto(item)')
        self.assertFalse(r['passed'])
    def test_variants_pass_general_solutions(self):
        for n in (2,3,4,5,6):
            self.assertTrue(self.evaluate(n,SOLUTIONS[n],1)['passed'])
    def test_runs_reset_state(self):
        a=self.evaluate(2,SOLUTIONS[2]); b=self.evaluate(2,SOLUTIONS[2])
        self.assertEqual(a,b)
    def test_no_imports_or_internal_attributes(self):
        for code in ('import os','hero.__dict__','open("x")'):
            self.assertFalse(self.evaluate(2,code)['passed'])
    def test_action_budget_stops_long_runs(self):
        r=self.evaluate(1,'for i in range(1000):\n    turnLeft()')
        self.assertFalse(r['passed'])
        self.assertIn('动作',r['error'])
    def test_infinite_loop_stops(self):
        r=self.evaluate(1,'while True:\n    pass')
        self.assertFalse(r['passed'])
        self.assertIn('执行',r['error'])
    def test_catalog_has_metadata_and_no_answers(self):
        self.assertIsNotNone(engine,'Missing playable Python simulation engine')
        c=engine.catalog()
        self.assertEqual(len(c),14)
        for q in c:
            self.assertIn('starter',q)
            self.assertIn('hints',q)
            self.assertNotIn('solution',q)
    def test_trace_contains_initial_and_final_state(self):
        r=self.evaluate(1,SOLUTIONS[1]); self.assertEqual(r['trace'][0]['actors'][0]['x'],1)
        self.assertEqual(r['trace'][-1]['actors'][0]['x'],5)
        self.assertEqual(r['trace'][-1]['actors'][0]['y'],1)

if __name__=='__main__': unittest.main(verbosity=2)
