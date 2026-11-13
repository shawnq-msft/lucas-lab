"""Publishing contracts for the user-approved robot roadmap, not hardware results."""
from pathlib import Path
import unittest
from html.parser import HTMLParser
ROOT=Path(__file__).resolve().parents[1]
class Document(HTMLParser):
    def __init__(self,text):
        super().__init__();self.ids=[];self.hrefs=[];self.feed(text)
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a:self.ids.append(a['id'])
        if tag=='a':self.hrefs.append(a.get('href',''))
class RobotRoadmap(unittest.TestCase):
    def text(self):
        p=ROOT/'robotics/index.html';self.assertTrue(p.is_file(),'robot roadmap missing');return p.read_text()
    def test_three_stages_in_user_order(self):
        text=self.text();doc=Document(text)
        self.assertEqual([x for x in doc.ids if x.startswith('stage-')],['stage-1','stage-2','stage-3'])
        for label in ['2DOF','视觉','语音','ToF','RL','3DOF','动作更丰富','尚未实测']:
            self.assertIn(label,text)
    def test_local_links_and_unique_ids(self):
        doc=Document(self.text());self.assertEqual(len(doc.ids),len(set(doc.ids)))
        for href in doc.hrefs:
            if href.startswith('#'):self.assertIn(href[1:],doc.ids)
        self.assertTrue((ROOT/'robotics/roadmap.css').is_file())
    def test_safety_and_scope(self):
        text=self.text()
        for label in ['不等于触地','失联','不直接控制','重新训练','待选型','采购报价']:
            self.assertIn(label,text)
        self.assertNotIn('qiushuo@',text)
    def test_home_and_deployment(self):
        self.assertIn('href="robotics/"',(ROOT/'index.html').read_text())
        workflow=(ROOT/'.github/workflows/pages.yml').read_text()
        for label in ['robotics _site/','test_robotics.py','tests/robotics_browser.py']:
            self.assertIn(label,workflow)
if __name__=='__main__':unittest.main(verbosity=2)
