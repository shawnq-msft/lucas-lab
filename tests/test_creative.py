"""Evidence and release contracts for the creative-project field guide."""
import json
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[1]

class CreativeGuide(unittest.TestCase):
    def test_six_tracks_and_evidence_boundaries(self):
        data = json.loads((ROOT/'creative/contests.json').read_text())
        self.assertEqual(len(data['contests']), 6)
        self.assertEqual(len({c['id'] for c in data['contests']}), 6)
        for c in data['contests']:
            for field in ['id','name','evidence','eligibility','team','theme','deliverables','platform','fit','unknown','source']:
                self.assertTrue(c[field], (c['id'],field))
            self.assertTrue(c['source'].startswith('https://'))
        school = next(c for c in data['contests'] if c['id']=='school-ai')
        self.assertIn('附件未读', school['evidence'])
        future = next(c for c in data['contests'] if c['id']=='future-app')
        self.assertIn('科学建议', future['deliverables'])
        self.assertIn('科学研究', future['deliverables'])
        art = next(c for c in data['contests'] if c['id']=='future-art')
        self.assertIn('歌曲不向小学组开放', art['eligibility'])
        self.assertIn('至少3', art['deliverables'])

    def test_guide_contains_comparison_strategy_and_caveats(self):
        text=(ROOT/'creative/index.html').read_text()
        for label in ['共同点','差异','作品复用','11月21','12月19','原创','平台','家长','测试','隐私','不是报名系统']:
            self.assertIn(label,text)
        for anchor in ['compare','projects','platforms','playbook','checklist','sources']:
            self.assertIn(f'id="{anchor}"',text)
        self.assertNotIn('qiushuo@',text)

    def test_entry_staging_and_ci(self):
        self.assertIn('href="creative/"',(ROOT/'index.html').read_text())
        workflow=(ROOT/'.github/workflows/pages.yml').read_text()
        for part in ['creative _site/','test_creative.py','tests/creative_browser.py']:
            self.assertIn(part,workflow)
        for f in ['index.html','guide.css','app.mjs','contests.json']:
            self.assertTrue((ROOT/'creative'/f).is_file())

if __name__=='__main__':
    unittest.main(verbosity=2)
