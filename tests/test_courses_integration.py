"""Publication contract for the external guided-course library."""
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[1]

class CourseIntegration(unittest.TestCase):
    def test_home_has_one_library_entry(self):
        home = (ROOT / 'index.html').read_text()
        self.assertEqual(home.count('href="courses/"'), 1)
        self.assertIn('互动课程', home)

    def test_courses_are_staged_and_tested(self):
        workflow = (ROOT / '.github/workflows/pages.yml').read_text()
        for item in ['cp -r courses _site/', 'test_courses.py', 'test_courses_integration.py', 'tests/courses_browser.py']:
            with self.subTest(item=item):
                self.assertIn(item, workflow)

if __name__ == '__main__':
    unittest.main(verbosity=2)
