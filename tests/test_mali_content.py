"""Curriculum schema, coverage, and actual C++17 reference-program execution."""
import json,os,subprocess,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class CourseContent(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.lessons=sum((json.loads((ROOT/'mali'/f'content-{c}.json').read_text()) for c in 'abc'),[])
  cls.exams=json.loads((ROOT/'mali/exams.json').read_text())
 def test_complete_primary_curriculum(self):
  self.assertEqual([x['id'] for x in self.lessons],[f'l{i:02}' for i in range(1,13)])
  self.assertEqual(len([l for l in self.lessons if l.get('coding')]),9)
  for l in self.lessons:
   with self.subTest(lesson=l['id']):
    self.assertGreaterEqual(len(l['slides']),5);self.assertGreaterEqual(len(l['goals']),2)
    self.assertEqual(len(l['questions']),4)
    self.assertEqual(sum(q['type']=='choice' for q in l['questions']),3)
    for s in l['slides']:
     self.assertTrue(s['title']);self.assertIsInstance(s['body'],list)
     self.assertGreater(len(''.join(s['body'])),35)
     if s.get('trace'):
      self.assertTrue(s['trace']['headers'])
      for row in s['trace']['rows']:self.assertEqual(len(row),len(s['trace']['headers']))
  text=json.dumps(self.lessons,ensure_ascii=False)
  for term in ['CPU','内存','编译','解释','隐私','人工智能','集合','栈','队列','冒泡','选择排序','快速排序','二分','枚举','递推','递归','贪心','复杂度']:
   self.assertIn(term,text)
 def test_questions_and_exam_composition(self):
  questions=[q for l in self.lessons for q in l['questions']]+[q for e in self.exams for q in e['questions']]
  self.assertEqual(len(questions),88);self.assertEqual(len({q['id'] for q in questions}),88)
  for q in questions:
   with self.subTest(q=q['id']):
    self.assertGreater(len(q['explanation']),12)
    if q['type']=='choice':
     self.assertEqual(len(q['options']),4);self.assertEqual(len(set(q['options'])),4)
     self.assertIs(type(q['answer']),int);self.assertIn(q['answer'],range(4))
    else:
     self.assertEqual(q['type'],'fill');self.assertIsInstance(q['answer'],str);self.assertTrue(q['answer'].strip())
  self.assertEqual([(e['id'],e['minutes']) for e in self.exams],[('stage1',40),('stage2',120)])
  self.assertTrue(all(q['type']=='choice' for q in self.exams[0]['questions']))
  self.assertEqual(sum(q['type']=='choice' for q in self.exams[1]['questions']),12)
  self.assertEqual(sum(q['type']=='fill' for q in self.exams[1]['questions']),8)
 def test_cpp_reference_solutions_with_every_case(self):
  scratch=Path.home()/'.hermes/cache/scratch';scratch.mkdir(parents=True,exist_ok=True)
  total=0
  with tempfile.TemporaryDirectory(prefix='mali-cpp-',dir=scratch) as tmp:
   tmp=Path(tmp)
   for l in self.lessons:
    if not l.get('coding'):continue
    c=l['coding'];self.assertGreaterEqual(len(c['tests']),4)
    for field in ['starter','solution']:
     src=tmp/f'{l["id"]}-{field}.cpp';exe=src.with_suffix('');src.write_text(c[field])
     build=subprocess.run(['g++','-std=c++17','-O2','-Wall','-Wextra',str(src),'-o',str(exe)],capture_output=True,text=True,timeout=25)
     self.assertEqual(build.returncode,0,f'{src.name}: {build.stderr}')
     if field=='starter':continue
     for t in c['tests']:
      run=subprocess.run([str(exe)],input=t['input'],capture_output=True,text=True,timeout=3)
      self.assertEqual(run.returncode,0,l['id']);self.assertEqual(run.stdout.split(),t['output'].split(),f'{l["id"]} input {t["input"]!r}');total+=1
    self.assertTrue(any(t['output'].strip() not in ('','0') for t in c['tests']))
  print(f'Executed {total} reference C++ test cases across nine programming tasks.')
if __name__=='__main__':unittest.main()
