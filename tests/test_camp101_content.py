"""Independent checks on original diagnostic content and its publication contract."""
import contextlib
import io
import itertools
import json
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[1]
class CampContent(unittest.TestCase):
    def load(self):
        path = ROOT/'camp101/content.json'
        self.assertTrue(path.is_file(), 'diagnostic content must exist')
        return json.loads(path.read_text())
    def test_structure_and_scope(self):
        d=self.load(); qs=[q for s in d['sections'] for q in s['questions']]
        self.assertEqual(len(qs),18); self.assertEqual(sum(q['points'] for q in qs),100)
        self.assertEqual([len(s['questions']) for s in d['sections']],[10,4,4])
        self.assertEqual([sum(q['points'] for q in s['questions']) for s in d['sections']],[60,20,20])
        self.assertEqual(sum(s['minutes'] for s in d['sections']),d['minutes'])
        self.assertEqual(len({q['id'] for q in qs}),18)
        self.assertIn('非官方真题',d['disclaimer'])
        for q in qs:
            self.assertEqual(q['provenance'],'自编参考题')
            self.assertTrue(q['explanation']); self.assertTrue(q['skill'])
            self.assertIn(q['stars'],[1,2,3])
            if q['type']=='manual':self.assertEqual(sum(x['points'] for x in q['rubric']),q['points'])
            else:self.assertTrue(q.get('answers') or q.get('answer'))
    def test_independent_math_and_displayed_code(self):
        qs={q['id']:q for s in self.load()['sections'] for q in s['questions']}
        self.assertEqual(qs['m01']['answers'],[str(min(n for n in range(51,100) if n%5==2 and n%7==3))])
        vals=[100*a+10*b+c for a,b,c in itertools.permutations([1,2,3,4],3)]
        self.assertEqual(qs['m02']['answers'],[str(sum(v%4==0 for v in vals))])
        paths=0
        for right in itertools.combinations(range(6),3):
            x=y=0;bad=False
            for i in range(6):
                if i in right:x+=1
                else:y+=1
                bad |= (x,y)==(1,1)
            paths+=not bad
        self.assertEqual(qs['m03']['answers'],[str(paths)])
        self.assertEqual(qs['m04']['answers'],[str(sum(sum(c)%2==1 for c in itertools.combinations(range(1,7),3)))])
        n=6
        for _ in range(4):n=n//2 if n%2==0 else 3*n+1
        self.assertEqual(qs['m05']['answers'],[str(n)])
        self.assertEqual(qs['m06']['answers'],[str(360//(5-3))])
        self.assertEqual(qs['m07']['answer'],'B')
        self.assertEqual((200*20+100*80)//300,40)
        for qid,expected in [('m09','3'),('m10','10')]:
            q=qs[qid];out=io.StringIO()
            with contextlib.redirect_stdout(out):exec(q['referenceCode'],{})
            self.assertEqual(out.getvalue().strip(),expected)
            self.assertEqual(q['answers'],[expected])
            self.assertIn(q['referenceCode'],q['prompt'])
    def test_sources_and_limits(self):
        d=self.load()
        self.assertGreaterEqual(len(d['sources']),3)
        self.assertTrue(all(s['url'].startswith('https://') for s in d['sources']))
        self.assertIn('回忆',d['evidenceNote'])
        self.assertIn('不代表',d['coverageNote'])
    def test_reference_resources(self):
        page=(ROOT/'camp101/resources.html').read_text()
        for text in ['不是 101','2020 年重庆','nrich.maths.org/problems/seven-nine','cambridgeenglish.org','openstax.org','cnblogs.com/myeln','n = 19','12 种']:
            self.assertIn(text,page)
        self.assertIn('resources.html',(ROOT/'camp101/index.html').read_text())
    def test_published_and_ci_contract(self):
        self.assertIn('href="camp101/"',(ROOT/'index.html').read_text())
        w=(ROOT/'.github/workflows/pages.yml').read_text()
        for x in ['cp -r camp101 _site/','tests/camp101.test.mjs','tests/camp101_browser.py','test_camp101_content.py']:self.assertIn(x,w)
if __name__=='__main__':unittest.main(verbosity=2)
