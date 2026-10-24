"""Composition-only oracles and regression checks; never shipped to students."""
import ast
import hashlib
import json
import unittest
import engine
from test_engine import SOLUTIONS
from test_advanced import ADVANCED_SOLUTIONS

COMBINATION_SOLUTIONS = {
11: '''def select(items):
    chosen = []
    for item in items:
        card = getDict(item)
        if card["safe"] and card["value"] >= limit and card["name"].lower().count("star") == 1:
            chosen.append(item)
    return chosen
for item in select(coins):
    goto(item)''',
12: '''def nearer(target):
    if hero.dTo(target) < hygeia.dTo(target):
        return hero
    return hygeia
for target in monsters:
    card = getDict(target)
    if card["hostile"] and card["strength"] <= limit:
        actor = nearer(target)
        actor.goto(target)
        actor.attack()''',
13: '''def select(items):
    chosen = []
    for item in items:
        card = getDict(item)
        if card["safe"] and card["value"] >= limit:
            chosen.append(item)
    return chosen
unlock(message[1:7:2].lower())
for item in select(coins):
    goto(item)
goto(exitTarget)''',
14: '''def select(items):
    chosen = []
    for item in items:
        card = getDict(item)
        if card["safe"] and card["value"] >= limit and (hero.dTo(item) <= maxDistance or hygeia.dTo(item) <= maxDistance):
            chosen.append(item)
    return chosen
def nearer(target):
    if hero.dTo(target) < hygeia.dTo(target):
        return hero
    return hygeia
targets = select(coins)
for target in targets:
    actor = nearer(target)
    actor.goto(target)'''
}

class CompositionTests(unittest.TestCase):
    def test_catalog_order_groups_and_no_answers(self):
        items = engine.catalog()
        self.assertEqual([q['id'] for q in items], [1,2,3,4,5,6,11,12,13,14,7,8,9,10])
        self.assertEqual([q['group'] for q in items], [1]*6+[2]*4+[3]*4)
        self.assertEqual([q['category'] for q in items], ['basic']*6+['composition']*4+['higher']*4)
        for q in items:
            self.assertNotIn('solution', q)
        for q in items[6:10]:
            self.assertIn('组合', q['skill'])
            self.assertNotIn('submit', ' '.join(q['api']))

    def test_all_twenty_eight_cpython_solutions_act(self):
        for n, code in {**SOLUTIONS, **COMBINATION_SOLUTIONS, **ADVANCED_SOLUTIONS}.items():
            for variant in (0,1):
                with self.subTest(level=n, variant=variant):
                    r = engine.evaluate(n,code,variant)
                    self.assertTrue(r['passed'],r['error'])
                    self.assertGreater(r['actions'],0)
                    self.assertTrue(any(f['actors'] != r['trace'][0]['actors'] or f['objects'] != r['trace'][0]['objects'] for f in r['trace'][1:]))

    def test_compositions_only_use_prior_concepts(self):
        allowed = {'move','goto','attack','dTo','getDict','unlock','lower','count','append','select','nearer'}
        for code in COMBINATION_SOLUTIONS.values():
            tree = ast.parse(code)
            self.assertFalse(any(isinstance(n,(ast.While,ast.ListComp,ast.Import)) for n in ast.walk(tree)))
            for n in ast.walk(tree):
                if isinstance(n,ast.Call):
                    self.assertIn(n.func.id if isinstance(n.func,ast.Name) else n.func.attr,allowed)

    def test_wrong_predicates_and_boundaries(self):
        changes = {
            11: [('card["safe"] and ',''),(' >= limit',' > limit'),('.lower()',''),(' == 1',' >= 1'),(' and card["name"].lower().count("star") == 1','')],
            12: [('card["hostile"] and ',''),(' <= limit',' < limit'),(' and card["strength"] <= limit',''),(' < hygeia',' <= hygeia')],
            13: [('card["safe"] and ',''),(' >= limit',' > limit'),('.lower()',''),('unlock(message[1:7:2].lower())',''),('goto(exitTarget)','')],
            14: [('card["safe"] and ',''),(' >= limit',' > limit'),(' <= maxDistance',' < maxDistance'),(' or hygeia',' and hygeia'),(' < hygeia',' <= hygeia')]
        }
        for n, edits in changes.items():
            for variant in (0,1):
                for old,new in edits:
                    with self.subTest(level=n,variant=variant,edit=old):
                        self.assertFalse(engine.evaluate(n,COMBINATION_SOLUTIONS[n].replace(old,new),variant)['passed'])

    def test_no_answer_only_or_empty_programs(self):
        for n in COMBINATION_SOLUTIONS:
            for variant in (0,1):
                for code in ('','print("done")','submit([])','for item in coins:\n    goto(item)'):
                    with self.subTest(level=n,variant=variant,code=code):
                        self.assertFalse(engine.evaluate(n,code,variant)['passed'])

    def test_independent_targets_and_visible_inputs(self):
        for v in (0,1):
            for n in COMBINATION_SOLUTIONS:
                w=engine.World(n,v)
                if n==12:
                    expected=[o.name for o in w.objects if o.attrs['hostile'] and o.attrs['strength'] <= w.limit]
                else:
                    expected=[o.name for o in w.objects if o.kind=='coin' and o.attrs['safe'] and o.attrs['value'] >= w.limit and (n!=11 or o.name.lower().count('star')==1) and (n!=14 or min(w.hero.dTo(o),w.hygeia.dTo(o)) <= w.maxDistance)]
                r=engine.evaluate(n,COMBINATION_SOLUTIONS[n],v)
                self.assertEqual(r['trace'][-1]['defeated' if n==12 else 'collected'],expected)
                self.assertTrue(r['trace'][0]['input'])
                self.assertNotEqual(engine.World(n,0).trace[0],engine.World(n,1).trace[0])
                if n in (12,14):
                    target=w.objects[0]
                    self.assertEqual(w.hero.dTo(target),w.hygeia.dTo(target))
                    acting=next(f for f in r['trace'][1:] if '→' in f['label'])
                    self.assertTrue(acting['label'].startswith('hygeia'))
                if n==13:
                    labels=[f['label'] for f in r['trace']]
                    self.assertLess(labels.index('星门已解锁'),next(i for i,f in enumerate(r['trace']) if f['collected']))
                    self.assertEqual((r['trace'][-1]['actors'][0]['x'],r['trace'][-1]['actors'][0]['y']),w.exit)

if __name__=='__main__':unittest.main(verbosity=2)
