"""Static, dependency-free contract for the external course guide."""
from html.parser import HTMLParser
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
URLS = {
    'protocol': 'https://protocol-explorer-alpha.vercel.app',
    'electronics': 'https://electronics-101-six.vercel.app',
    'backcountry': 'https://backcountry-101.vercel.app',
    'esp32': 'https://learn-esp32.vercel.app',
    'arduino': 'https://learn-arduino-red.vercel.app',
    'scale': 'https://designed-to-scale.vercel.app',
}

class Document(HTMLParser):
    def __init__(self, source):
        super().__init__(); self.cards = []; self.links = []; self.tags = []
        self.feed(source)
    def handle_starttag(self, tag, attrs):
        a = dict(attrs); self.tags.append(tag)
        if tag == 'article' and 'course-card' in (a.get('class') or '').split(): self.cards.append(a)
        if tag == 'a': self.links.append(a)

class CourseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = ROOT / 'courses/index.html'
        cls.source = cls.path.read_text() if cls.path.exists() else ''
        cls.doc = Document(cls.source)
    def test_static_six_courses(self):
        self.assertEqual(len(self.doc.cards), 6, 'Six usable static course cards must exist before JavaScript runs')
        self.assertEqual({a['id'] for a in self.doc.cards}, set(URLS))
    def test_exact_original_links_are_safe_new_tabs(self):
        for url in URLS.values():
            links = [a for a in self.doc.links if a.get('href') == url]
            self.assertEqual(len(links), 1, url)
            self.assertEqual(links[0].get('target'), '_blank')
            self.assertTrue({'noopener', 'noreferrer'} <= set(links[0].get('rel', '').split()))
    def test_each_course_has_action_prediction_explanation(self):
        for course in URLS:
            if f'id="{course}"' not in self.source: self.fail(f'Missing course {course}')
            card = self.source.split(f'id="{course}"', 1)[1].split('</article>', 1)[0]
            for label in ('动手做', '先预测', '讲清楚', '先会什么', '原站课程'):
                self.assertIn(label, card, f'{course}: {label}')
    def test_attribution_and_honest_boundaries(self):
        for text in ('Dilum Sanjaya', 'Lucas Lab 编辑推荐', '不是原作者的难度分级', '不是完整课程翻译', '需要联网', '进度', '外部域名', '英语', '访问和内容可能变化', '2026-11-17', '凿空创想', '古法编程大师的AI在线交互课程'):
            self.assertIn(text, self.source)
        self.assertIn('https://mp.weixin.qq.com/s/9mUdMT78YCpWuuqDSKU5QQ', self.source)
        self.assertIn('https://x.com/DilumSanjaya', self.source)
        self.assertNotIn('iframe', self.doc.tags)
    def test_safety_and_learning_paths(self):
        for text in ('不食用', '蘑菇', '过滤不等于消毒', '禁火', '独自', '3.3V', '5V', '引脚', '迷路', '装备', '导航', '19', '20', 'ATmega328P', 'Kirchhoff', 'DNS', 'HTTP', 'TCP'):
            self.assertIn(text, self.source)
        self.assertIn('id="paths"', self.source)
    def test_local_styles_and_print(self):
        css = ROOT / 'courses/courses.css'
        self.assertTrue(css.exists(), 'Dedicated responsive stylesheet missing')
        text = css.read_text()
        for rule in ('@media print', ':focus-visible', '[hidden]', 'prefers-reduced-motion'):
            self.assertIn(rule, text)
        self.assertIn('courses.css', self.source)
        self.assertIn('lang="zh-CN"', self.source)

if __name__ == '__main__': unittest.main()
