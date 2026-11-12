import unittest
from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]

class Document(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.ids = []
        self.hrefs = []
        self.schools = []
        self.feed(text)
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'id' in a: self.ids.append(a['id'])
        if 'href' in a: self.hrefs.append(a['href'])
        if 'data-school' in a: self.schools.append(a['data-school'])

class SchoolSummaryTests(unittest.TestCase):
    def test_summary_is_published_content(self):
        page = ROOT / 'school-admissions/index.html'
        self.assertTrue(page.exists(), 'School admissions summary page is missing')
        text = page.read_text()
        for item in ['2026', '本校', '华清', '百旺', '万泉河', '一派', '二派', '中签率', '第一志愿', '借址', '证据', '未核实', '不是个人志愿资格确认']:
            self.assertIn(item, text)
        doc = Document(text)
        self.assertEqual(len(doc.schools), 6)
        self.assertEqual(len(set(doc.schools)), 6)
        self.assertEqual(len(doc.ids), len(set(doc.ids)))
        for href in doc.hrefs:
            if href.startswith('#'): self.assertIn(href[1:], doc.ids)
            elif not href.startswith(('https://', 'http://')):
                self.assertTrue((page.parent / href).exists(), href)
        self.assertIn('https://www.bjhdedu.cn/zxfw/fwrxzc/202604/t20260428_91420.html', doc.hrefs)
        self.assertIn('https://hdks.bjhdedu.cn/czrx/zxtz/202605/P020260525805369815808.png', doc.hrefs)
        self.assertNotIn('xscxx.com', text)
        self.assertNotIn('邱思澄', text)
        self.assertIn('noindex,nofollow', text)

    def test_home_and_deploy_include_summary(self):
        self.assertIn('href="school-admissions/"', (ROOT / 'index.html').read_text())
        workflow = (ROOT / '.github/workflows/pages.yml').read_text()
        self.assertIn('cp -r school-admissions _site/', workflow)
        self.assertIn('test_school_admissions.py', workflow)

if __name__ == '__main__': unittest.main()
