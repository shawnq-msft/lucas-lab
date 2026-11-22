import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class TypingExpansionIntegration(unittest.TestCase):
    def test_home_advertises_all_six_missions(self):
        page = (ROOT / 'index.html').read_text()
        start = page.index('href="typing/"')
        block_start = page.rfind('<article', 0, start)
        block = page[block_start:page.index('</article>', start)]
        for name in ['星矿补给站', '太空防御', '星际反击', '矿带采集', '太空救援', '星际竞速']:
            self.assertIn(name, block)
        self.assertIn('星级', block)
        self.assertEqual(page.count('href="typing/"'), 1)
        self.assertIn('Cookie', block)

    def test_ci_includes_expansion_and_integration(self):
        workflow = (ROOT / '.github/workflows/pages.yml').read_text()
        for suite in ['tests/typing_expansion.test.mjs', 'tests/typing_expansion_browser.py', 'test_typing_expansion_integration.py']:
            self.assertIn(suite, workflow)

if __name__ == '__main__':
    unittest.main()
