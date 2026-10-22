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
    def test_integrated_modules_have_home_link(self):
        for name in ['practice','tokamak']:
            self.assertIn('href="../"',(ROOT/name/'index.html').read_text())
if __name__=='__main__':unittest.main(verbosity=2)
