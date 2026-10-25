from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
class SiteBuild(unittest.TestCase):
    def test_all_entrypoints_and_assets_exist(self):
        for name in ['index.html','favicon.svg','practice/index.html','tokamak/index.html','algorithms/index.html','algorithms/app.mjs','algorithms/model.mjs']:
            with self.subTest(name=name):self.assertTrue((ROOT/name).is_file(),name)
    def test_practice_uses_local_runtime_and_distinct_storage(self):
        text=(ROOT/'practice/index.html').read_text()
        self.assertNotIn('https://cdn.jsdelivr.net',text)
        self.assertIn('lucas-lab-python-quest-v1',text)
        for name in ['pyodide.js','pyodide.asm.js','pyodide.asm.wasm','python_stdlib.zip','pyodide-lock.json']:
            self.assertTrue((ROOT/'practice/runtime'/name).is_file(),name)
    def test_home_describes_three_practice_groups(self):
        text=(ROOT/'index.html').read_text()
        for label in ['第一组：基础六关','第二组：综合四题','第三组：算法拓展四题','A/B题目版本']:
            self.assertIn(label,text)
    def test_home_describes_graded_advanced_algorithms(self):
        text=(ROOT/'index.html').read_text()
        for label in ['★', '归并', '快速', '堆排序', '递归', '二叉树', '博弈']:
            with self.subTest(label=label):self.assertIn(label,text)
    def test_typing_has_home_entry_and_deploy_staging(self):
        home=(ROOT/'index.html').read_text()
        self.assertIn('href="typing/"',home)
        self.assertIn('Cookie',home)
        for scene in ['星矿补给站','太空防御','太空反攻']:
            self.assertIn(scene,home)
        self.assertNotIn('星际修桥',home)
        self.assertIn('起始速度',home)
        self.assertIn('tokamak typing _site/',(ROOT/'.github/workflows/pages.yml').read_text())
    def test_computer_is_linked_staged_and_tested(self):
        self.assertIn('href="computer/"',(ROOT/'index.html').read_text())
        workflow=(ROOT/'.github/workflows/pages.yml').read_text()
        self.assertIn('computer _site/',workflow)
        self.assertIn('tests/computer.test.mjs',workflow)
        for name in ['index.html','app.mjs','model.mjs','computer.css']:
            self.assertTrue((ROOT/'computer'/name).is_file())
    def test_integrated_modules_have_home_link(self):
        for name in ['practice','tokamak']:
            self.assertIn('href="../"',(ROOT/name/'index.html').read_text())
if __name__=='__main__':unittest.main(verbosity=2)
