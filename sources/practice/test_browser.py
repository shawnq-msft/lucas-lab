from pathlib import Path
import json
import unittest
from playwright.sync_api import sync_playwright
from test_engine import SOLUTIONS

ROOT=Path(__file__).parent
HTML=ROOT/'dist'/'星矿探险_Python模拟闯关.html'

class BrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pw=sync_playwright().start()
        paths=sorted((Path.home()/'.cache/ms-playwright').glob('chromium-*/chrome-linux*/chrome'))
        cls.browser=cls.pw.chromium.launch(executable_path=str(paths[-1]),headless=True,args=['--no-sandbox'])
        cls.context=cls.browser.new_context(viewport={'width':1440,'height':1000},accept_downloads=True)
        cls.page=cls.context.new_page()
        cls.errors=[]
        cls.page.on('pageerror',lambda e:cls.errors.append(str(e)))
    @classmethod
    def tearDownClass(cls):
        cls.browser.close();cls.pw.stop()
    def test_playable_artifact(self):
        self.assertTrue(HTML.exists(),'Missing playable HTML artifact')
        import os
        p=self.page;p.goto(os.environ.get('QUEST_TEST_URL', HTML.as_uri()))
        p.wait_for_function("document.querySelector('#runtime').dataset.state==='ready'",timeout=180000)
        self.assertEqual(p.locator('#levels button').count(),6)
        self.assertEqual(p.locator('svg .actor').count(),1)
        for n,source in SOLUTIONS.items():
            p.locator(f'#levels button[data-id="{n}"]').click()
            p.locator('#editor').fill(source)
            p.locator('#run').click()
            p.wait_for_function("document.querySelector('#result').dataset.status==='passed'",timeout=30000)
            self.assertIn('通过',p.locator('#result').inner_text())
        p.locator('#levels button[data-id="1"]').click()
        p.locator('#editor').fill('move(4)');p.locator('#run').click()
        p.wait_for_function("document.querySelector('#result').dataset.status==='failed'",timeout=15000)
        self.assertIn('墙',p.locator('#result').inner_text())
        p.locator('#editor').fill('while True:\n    pass');p.locator('#run').click()
        p.wait_for_function("document.querySelector('#result').dataset.status==='failed'",timeout=15000)
        self.assertIn('执行',p.locator('#result').inner_text())
        p.locator('#hint').click();self.assertIn('朝向',p.locator('#hints').inner_text())
        p.locator('#levels button[data-id="4"]').click()
        p.locator('#variant').select_option('1')
        p.locator('#editor').fill(SOLUTIONS[4]);p.locator('#run').click()
        p.wait_for_function("document.querySelector('#result').dataset.status==='passed'",timeout=15000)
        p.locator('#replay').click();p.locator('#pauseReplay').click();p.locator('#step').click()
        self.assertGreaterEqual(int(p.locator('#frameCounter').get_attribute('data-frame')),1)
        with p.expect_download() as dl:
            p.locator('#export').click()
        dest=ROOT/'test-progress.json';dl.value.save_as(dest)
        data=json.loads(dest.read_text())
        self.assertEqual(data['type'],'maodou-python-quest-progress')
        self.assertTrue(any(x['hints']>0 for x in data['records'].values()))
        self.assertTrue(all(len(data['records'][f'{i}:0']['attempts'])>0 for i in range(1,7)))
        p.reload();p.wait_for_selector('#editor')
        p.locator('#levels button[data-id="1"]').click();p.locator('#variant').select_option('0')
        self.assertEqual(p.locator('#editor').input_value(),'while True:\n    pass')
        p.screenshot(path=str(ROOT/'desktop.png'),full_page=True)
        p.set_viewport_size({'width':390,'height':844})
        self.assertTrue(p.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'))
        p.screenshot(path=str(ROOT/'mobile.png'),full_page=True)
        self.assertEqual(self.errors,[])
        print(json.dumps({'browser':'Chromium','six_levels_passed':True,'error_infinite_loop_hint_variant_replay_export_persistence_mobile_checked':True,'console_errors':self.errors},ensure_ascii=False))

if __name__=='__main__':unittest.main(verbosity=2)
