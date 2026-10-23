"""Execute the exact Python examples shown to children, not a reimplementation."""
import contextlib
import io
import json
import random
import subprocess
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
TOPICS=json.loads(subprocess.check_output(['node','--input-type=module','-e',"import {topics} from './algorithms/model.mjs';console.log(JSON.stringify(topics))"],cwd=ROOT))
CODE={t['id']:t['python'] for t in TOPICS}
def load(topic):
    ns={}
    with contextlib.redirect_stdout(io.StringIO()):exec(CODE[topic],ns)
    return ns
class Examples(unittest.TestCase):
    def test_sort_examples(self):
        rng=random.Random(84)
        cases=[[],[1],[2,2,1],[-3,4,-3,0],list(range(9)),list(range(9,-1,-1))]+[[rng.randrange(-8,9) for _ in range(rng.randrange(15))] for _ in range(80)]
        for topic,name in [('insertion','insertion'),('merge','merge_sort'),('quick','quick_sort'),('heap','heap_sort')]:
            fn=load(topic)[name]
            for a in cases:self.assertEqual(fn(a[:]),sorted(a),(topic,a))
    def test_factorial_example(self):
        import math
        fn=load('recursion')['factorial']
        for n in range(9):self.assertEqual(fn(n),math.factorial(n))
    def test_tree_example_emits_in_the_named_order(self):
        # Observe value accesses as well as returned order. A traversal should
        # visit/output its root at the advertised moment, not collect afterward.
        expected={'preorder':['A','B','D','E','C'],'inorder':['D','B','E','A','C'],'postorder':['D','E','B','C','A']}
        for topic,order in expected.items():
            reads=[]
            class Node(dict):
                def __getitem__(self,key):
                    v=super().__getitem__(key)
                    if key=='value':reads.append(v)
                    return v
            tree=Node(value='A',left=Node(value='B',left=Node(value='D'),right=Node(value='E')),right=Node(value='C'))
            fn=load(topic)['traverse']
            self.assertEqual(fn(tree),order)
            self.assertEqual(reads,order,topic+' visits root at the right time')
            self.assertEqual(fn(None),[])
    def test_stone_strategy(self):
        fn=load('stones')['winning_moves']
        # For this consecutive 1..k ruleset, losing positions are multiples of k+1.
        for k in range(1,5):
            for n in range(30):self.assertEqual(fn(n,k),[t for t in range(1,min(n,k)+1) if (n-t)%(k+1)==0])
    def test_minimax_example(self):
        fn=load('minimax')['minimax'];rng=random.Random(8)
        for _ in range(80):
            tree=[[rng.randrange(-20,21) for _ in range(2)] for _ in range(2)]
            self.assertEqual(fn(tree),max(min(p) for p in tree))
            self.assertEqual(fn(tree,False),min(max(p) for p in tree))
        self.assertEqual(fn(-5),-5)
if __name__=='__main__':unittest.main(verbosity=2)
