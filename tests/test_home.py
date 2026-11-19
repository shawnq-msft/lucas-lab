"""Homepage inventory, accessibility, packaging and public illustration integrity."""
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
import hashlib
import json
import os
import struct
import unittest

ROOT = Path(__file__).resolve().parents[1]
DESTINATIONS = {'practice', 'algorithms', 'tokamak', 'typing', 'computer', 'mali', 'creative', 'camp101', 'school-admissions', 'robotics', 'courses'}
COVERS = {'robotics', 'python', 'tokamak', 'creative', 'algorithms', 'courses'}

class HomeParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.entries, self.images, self.filters = [], [], []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'article' and 'data-category' in attrs:
            self.entries.append(attrs)
        if tag == 'img':
            self.images.append(attrs)
        if tag == 'button' and 'data-filter' in attrs:
            self.filters.append(attrs)

def webp_dimensions(data):
    """Read canvas dimensions from the actual RIFF WebP header, no dependencies."""
    if data[:4] != b'RIFF' or data[8:12] != b'WEBP':
        raise ValueError('Not a WebP image')
    kind = data[12:16]
    if kind == b'VP8X':
        return (int.from_bytes(data[24:27], 'little') + 1, int.from_bytes(data[27:30], 'little') + 1)
    if kind == b'VP8 ' and data[23:26] == b'\x9d\x01\x2a':
        return tuple(v & 0x3fff for v in struct.unpack('<HH', data[26:30]))
    if kind == b'VP8L' and data[20] == 0x2f:
        value = int.from_bytes(data[21:25], 'little')
        return ((value & 0x3fff) + 1, ((value >> 14) & 0x3fff) + 1)
    raise ValueError('Unrecognized WebP header')

class HomeMagazine(unittest.TestCase):
    def parse(self):
        text = (ROOT / 'index.html').read_text()
        parser = HomeParser()
        parser.feed(text)
        return text, parser
    def test_all_eleven_destinations_and_category_counts(self):
        text, parser = self.parse()
        self.assertEqual(len(parser.entries), 11)
        self.assertEqual(Counter(x['data-category'] for x in parser.entries), {'code': 4, 'science': 3, 'contests': 3, 'family': 1})
        for destination in DESTINATIONS:
            self.assertEqual(text.count(f'href="{destination}/"'), 1, destination)
        self.assertEqual({x['data-filter'] for x in parser.filters}, {'all', 'code', 'science', 'contests', 'family'})
    def test_six_local_image_headers_and_disclosures(self):
        text, parser = self.parse()
        self.assertEqual(len(parser.images), 6)
        self.assertEqual({Path(x['src']).stem for x in parser.images}, COVERS)
        self.assertEqual(text.count('<figcaption>AI 生成概念插画'), 6)
        for image in parser.images:
            self.assertEqual(image['src'], f"assets/home/{Path(image['src']).stem}.webp")
            self.assertTrue(image.get('alt'))
            self.assertEqual((int(image['width']), int(image['height'])), (1200, 800))
    def test_public_webp_dimensions_and_manifest_sha(self):
        _, parser = self.parse()
        manifest_path = ROOT / 'assets/home/manifest.json'
        missing = [image['src'] for image in parser.images if not (ROOT / image['src']).is_file()]
        if not manifest_path.is_file() or missing:
            if os.environ.get('HOME_REQUIRE_ASSETS') == '1':
                self.fail(f'Illustration handoff incomplete: {missing}; manifest={manifest_path.is_file()}')
            self.skipTest('Parent illustration handoff pending; CI requires HOME_REQUIRE_ASSETS=1')
        manifest = json.loads(manifest_path.read_text())
        self.assertEqual(set(manifest['images']), COVERS)
        self.assertEqual(manifest['verified_count'], 6)
        for image in parser.images:
            with self.subTest(image=image['src']):
                path = ROOT / image['src']
                data = path.read_bytes()
                record = manifest['images'][path.stem]
                self.assertGreater(len(data), 5000)
                self.assertEqual(webp_dimensions(data), (int(image['width']), int(image['height'])))
                self.assertEqual((record['width'], record['height']), webp_dimensions(data))
                self.assertEqual(record['sha256'], hashlib.sha256(data).hexdigest())
                self.assertEqual(record['file'], path.name)
                self.assertEqual(record['bytes'], len(data))
    def test_visible_boundaries_and_original_content(self):
        text, _ = self.parse()
        for phrase in ['第一组：基础六关', '第二组：综合四题', '第三组：算法拓展四题', 'A/B题目版本', '归并', '快速', '堆排序', '递归', '二叉树', '博弈', '星矿补给站', '太空防御', '太空反攻', '起始速度', 'Cookie', '学校AI赛完整附件仍待核实', '非官方真题', '不是工程设计或真实运行模拟', '不是完整装配教程、采购报价或运动能力承诺', '非招生通知', '2026 年比赛总体方案', '2026 年 10 月家长考情分享', '六套互动课程', 'Dilum Sanjaya', '外部网站', '需要联网', '进度不与 Lucas Lab 同步', '户外内容仅作安全常识启蒙', '首次独立记录', '本站没有账号', '旧站记录不会自动迁移', '不是密码保护']:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)
        # Safety/evidence boundaries stay outside optional details.
        visible_text = __import__('re').sub(r'<details>.*?</details>', '', text, flags=__import__('re').S)
        for phrase in ['Cookie', '学校AI赛完整附件仍待核实', '非官方真题', '不是工程设计或真实运行模拟', '外部网站', '项目计划，尚未实测', '非招生通知']:
            self.assertIn(phrase, visible_text)
    def test_accessibility_and_deployment(self):
        text, parser = self.parse()
        for phrase in ['id="search"', 'aria-pressed="true"', 'role="status"', 'id="emptyState"', 'home/app.mjs', 'home/home.css', '<noscript>', 'class="skip-link"']:
            self.assertIn(phrase, text)
        self.assertTrue(all('disabled' in x for x in parser.filters))
        workflow = (ROOT / '.github/workflows/pages.yml').read_text()
        for phrase in ['cp -r home assets _site/', 'tests/home.test.mjs', 'test_home.py', 'HOME_REQUIRE_ASSETS=1', 'tests/home_browser.py', 'cp -r courses _site/', 'cp -r practice algorithms tokamak typing _site/']:
            self.assertIn(phrase, workflow)
        self.assertNotIn('qiushuo@', text)

if __name__ == '__main__':
    unittest.main(verbosity=2)
