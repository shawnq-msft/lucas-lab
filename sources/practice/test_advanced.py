"""Independent contest-extension oracles; never included in student payload."""
import unittest
from collections import deque
import engine

ADVANCED_SOLUTIONS = {
7: '''ordered = []
for coin in coins:
    i = len(ordered)
    ordered.append(coin)
    while i > 0 and getDict(ordered[i-1])["value"] > getDict(coin)["value"]:
        ordered[i] = ordered[i-1]
        i -= 1
    ordered[i] = coin
for coin in ordered:
    goto(coin)''',
8: '''queue = [[start]]
seen = [start]
while queue:
    path = queue.pop(0)
    x, y = path[-1]
    if (x, y) == goal:
        submit(path)
        break
    for dx, dy in [(1,0),(0,1),(-1,0),(0,-1)]:
        nx, ny = x+dx, y+dy
        if 0 <= nx < len(maze[0]) and 0 <= ny < len(maze) and maze[ny][nx] != "#" and (nx,ny) not in seen:
            seen.append((nx,ny))
            queue.append(path+[(nx,ny)])''',
9: '''order = []
def visit(node):
    if node is None:
        return
    order.append(node)
    visit(tree[node]["left"])
    visit(tree[node]["right"])
visit(root)
submit(order)''',
10: '''win = [False] * (stones+1)
for n in range(1, stones+1):
    for take in moves:
        if take <= n and not win[n-take]:
            win[n] = True
choice = 0
for take in moves:
    if take <= stones and not win[stones-take] and choice == 0:
        choice = take
submit(choice)'''
}

def bfs(maze, start, goal):
    queue=deque([(start,[start])]); seen={start}
    while queue:
        p,path=queue.popleft()
        if p==goal:return path
        for dx,dy in [(0,-1),(-1,0),(0,1),(1,0)]:
            q=(p[0]+dx,p[1]+dy)
            if 0<=q[1]<len(maze) and 0<=q[0]<len(maze[0]) and maze[q[1]][q[0]]!='#' and q not in seen:
                seen.add(q);queue.append((q,path+[q]))

class AdvancedTests(unittest.TestCase):
    def test_original_catalog_preserved_and_stars(self):
        c=[x for x in engine.catalog() if x['id']<=10]
        self.assertEqual([x['id'] for x in c],list(range(1,11)))
        self.assertEqual([x['stars'] for x in c[6:]],[2,3,2,3])
        for item in c[6:]:
            self.assertEqual(item['category'],'higher')
            self.assertIn('非官方',item['goal'])
            self.assertNotIn('solution',item)

    def test_twenty_reference_cases(self):
        from test_engine import SOLUTIONS
        for n,code in {**SOLUTIONS,**ADVANCED_SOLUTIONS}.items():
            for variant in (0,1):
                with self.subTest(n=n,variant=variant):
                    result=engine.evaluate(n,code,variant)
                    self.assertTrue(result['passed'],result['error'])
                    self.assertGreater(result['actions'],0)
                    if n>=7:self.assertNotEqual(result['trace'][0]['actors'],result['trace'][-1]['actors'])

    def test_wrong_empty_malformed_and_wrong_variant(self):
        for n in range(7,11):
            for code in ['', 'print(123)', 'submit(None)', 'submit(True)', 'submit([999])', 'import os', 'hero.__dict__', 'while True:\n    pass']:
                with self.subTest(n=n,code=code):self.assertFalse(engine.evaluate(n,code)['passed'])
        self.assertFalse(engine.evaluate(7,'for coin in coins:\n    goto(coin)')['passed'])
        self.assertFalse(engine.evaluate(7,ADVANCED_SOLUTIONS[7].replace(' > ', ' >= '))['passed'])
        for n in (8,9,10):
            w=engine.World(n,0)
            if n==8: answer=bfs(w.maze,w.start,w.goal)
            elif n==9: answer=['A','B','D','E','C','F']
            else: answer=1
            self.assertFalse(engine.evaluate(n,'submit('+repr(answer)+')',1)['passed'])

    def test_bfs_independent_shortest_and_invalid_paths(self):
        for v in (0,1):
            w=engine.World(8,v); path=bfs(w.maze,w.start,w.goal)
            self.assertTrue(engine.evaluate(8,'submit('+repr(path)+')',v)['passed'])
            for bad in [path[:-1],path+[path[-1]], [path[0],path[-1]], [[True,1]]]:
                self.assertFalse(engine.evaluate(8,'submit('+repr(bad)+')',v)['passed'])
            detour=path[:1]+[path[1],path[0]]+path[1:]
            self.assertFalse(engine.evaluate(8,'submit('+repr(detour)+')',v)['passed'])

    def test_recursive_tree_required(self):
        self.assertFalse(engine.evaluate(9,"submit(['A','B','D','E','C','F'])")['passed'])
        self.assertFalse(engine.evaluate(9,ADVANCED_SOLUTIONS[9].replace('order.append(node)','order.append(root)'))['passed'])

    def test_game_all_states_independent_minimax_and_edges(self):
        def winning(n,moves):return any(m<=n and not winning(n-m,moves) for m in moves)
        for moves in ([1,2],[1,3,4],[2,3]):
            for n in range(0,18):
                expected=[m for m in moves if m<=n and not winning(n-m,moves)]
                for choice in [0]+list(moves):
                    w=engine.World(10,0);w.stones=n;w.moves=list(moves)
                    try:w.submit(choice); accepted=w.passed()
                    except engine.GameError:accepted=False
                    self.assertEqual(accepted,choice in expected if expected else choice==0,(n,moves,choice))
        for v in (0,1):
            for bad in (-1,99,1.0,True,'1',[],None):
                self.assertFalse(engine.evaluate(10,'submit('+repr(bad)+')',v)['passed'])

    def test_input_copy_and_double_submit(self):
        self.assertFalse(engine.evaluate(8,'maze[0] = "........"\nsubmit([start,goal])')['passed'])
        self.assertFalse(engine.evaluate(10,ADVANCED_SOLUTIONS[10]+'\nsubmit(choice)')['passed'])
        self.assertFalse(engine.evaluate(9,'tree.clear()\nsubmit([])')['passed'])

if __name__=='__main__':unittest.main(verbosity=2)
