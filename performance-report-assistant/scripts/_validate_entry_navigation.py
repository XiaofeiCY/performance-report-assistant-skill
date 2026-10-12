import ast
import sys
import types
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import Mock, patch

SOURCE = Path(__file__).with_name('collect_wecom_smart_summary.py')
TREE = ast.parse(SOURCE.read_text(encoding='utf-8'))
NAMES = {'_entry_label_matches', '_entry_bounds_valid', '_action_open_smart_summary_entry'}
CODE = compile(ast.Module(body=[n for n in TREE.body if isinstance(n, ast.FunctionDef) and n.name in NAMES], type_ignores=[]), str(SOURCE), 'exec')

class EntryTests(unittest.TestCase):
    def setUp(self):
        self.rect = NS(left=0, top=0, right=1000, bottom=1000)
        self.input = Mock()
        self.trace = Mock()
        self.frame = NS(regions={'app_sidebar': object()})
        self.state = {'state':'summary_input_page', 'in_smart_summary':True}
        self.rows = [([[10,400],[70,400],[70,420],[10,420]], '智能总结', .9)]
        self.ns = dict(wintypes=NS(RECT=object), TraceLogger=object,
            _window_rect=Mock(return_value=self.rect), _root_window=lambda x:x,
            user32=NS(GetForegroundWindow=Mock(return_value=1)),
            capture_trusted_frame=Mock(return_value=self.frame), save_frame_artifacts=Mock(),
            ocr_all=Mock(side_effect=lambda *a:self.rows), _save_ocr_lines=Mock(),
            _verify_foreground_or_fail=Mock(), time=NS(sleep=Mock()),
            classify_page_structured=Mock(side_effect=lambda *a:self.state))
        exec(CODE,self.ns)
        self.ns['_navigation_ocr'] = self.ns['ocr_all']
        self.modules=patch.dict(sys.modules, {'interception':self.input, 'uiautomation':NS(GetRootControl=Mock(side_effect=RuntimeError('unavailable')))})
        self.modules.start()
        self.addCleanup(self.modules.stop)
    def run_entry(self):
        return self.ns['_action_open_smart_summary_entry'](1,self.rect,object(),self.trace)
    def test_reordered(self):
        for y in (50,400,850):
            self.rows=[([[10,y],[70,y],[70,y+20],[10,y+20]],'智能 总结',.9)]
            self.assertEqual(self.run_entry(),'reclassify')
            self.input.move_to.assert_called_with(40,y+10)
    def test_absent(self):
        self.rows=[]
        self.assertEqual(self.run_entry(),'terminal_failure')
        self.input.click.assert_not_called()
    def test_partial_name(self):
        self.rows=[(self.rows[0][0],'智能总结设置',.9)]
        self.assertEqual(self.run_entry(),'terminal_failure')
        self.input.click.assert_not_called()
    def test_ambiguous(self):
        self.rows.append(([[10,600],[70,600],[70,620],[10,620]],'智能总结',.9))
        self.assertEqual(self.run_entry(),'terminal_failure')
        self.input.click.assert_not_called()
    def test_foreground_changed(self):
        self.ns['user32'].GetForegroundWindow.return_value=2
        self.assertEqual(self.run_entry(),'terminal_failure')
        self.input.click.assert_not_called()
    def test_changed_label(self):
        self.ns['ocr_all'].side_effect=[self.rows,[]]
        self.assertEqual(self.run_entry(),'terminal_failure')
        self.input.click.assert_not_called()
    def test_wrong_page(self):
        self.state={'state':'main_page','in_smart_summary':False}
        self.assertEqual(self.run_entry(),'terminal_failure')
        self.input.click.assert_called_once()
        self.assertEqual(self.ns['classify_page_structured'].call_count,3)
    def test_tainted(self):
        self.state={'state':'summary_unknown_page','in_smart_summary':False,'tainted':True}
        self.assertEqual(self.run_entry(),'terminal_failure')
        self.assertEqual(self.ns['classify_page_structured'].call_count,1)
    def test_uia(self):
        control=NS(Name='智能总结',IsOffscreen=False,IsEnabled=True,
                   BoundingRectangle=NS(left=10,top=700,right=70,bottom=720))
        auto=NS(GetRootControl=lambda:NS(GetChildren=lambda:[NS(NativeWindowHandle=1)]),WalkControl=lambda win, *, maxDepth:[(control,1)])
        with patch.dict(sys.modules,{'uiautomation':auto}):
            self.assertEqual(self.run_entry(),'reclassify')
        self.ns['ocr_all'].assert_not_called()
        self.input.move_to.assert_called_with(40,710)

    def test_small_label_coordinates(self):
        helper = next(n for n in TREE.body if isinstance(n, ast.FunctionDef) and n.name == '_navigation_ocr')
        exec(compile(ast.Module(body=[helper], type_ignores=[]), str(SOURCE), 'exec'), self.ns)
        self.ns['_rapid_ocr_all'] = Mock(return_value=[([[30,1500],[150,1500],[150,1560],[30,1560]], '智能总结', .8)])
        img = Mock(width=60, height=1080)
        rows = self.ns['_navigation_ocr'](img, object())
        img.resize.assert_called_once_with((180,3240))
        self.assertEqual(rows[0][0][0],[10,500])
        self.assertEqual(rows[0][0][2],[50,520])
        self.ns['ocr_all'].assert_not_called()

if __name__=='__main__':
    unittest.main()
