"""Original teaching simulator; not an implementation of the official engine.

Public data is read next to this file (including /home/pyex in Pyodide).
This restricted execution environment is not an OS-level security sandbox.
Run untrusted submissions in a disposable worker with a host timeout as well.
"""
import ast
import copy
import json
import math
import operator
from pathlib import Path
import sys

SOURCE_LIMIT = 16000
LINE_LIMIT = 3000
ACTION_LIMIT = 128
STEP_LIMIT = 1024
VALUE_LIMIT = 1000
BIT_LIMIT = 256
FRAME_LIMIT = 150
FILENAME = '<student>'
ACTIONS = frozenset(('move', 'turnLeft', 'turnRight', 'attack', 'press'))
BUILTINS = {'len': len, 'int': int, 'float': float, 'str': str, 'bool': bool,
            'abs': abs, 'min': min, 'max': max, 'sum': sum, 'list': list,
            'tuple': tuple, 'dict': dict, 'sorted': sorted, 'range': range,
            'enumerate': enumerate, 'zip': zip, 'round': round}
METHODS = {
    list: frozenset(('append', 'pop', 'reverse', 'sort', 'count', 'index',
                     'insert', 'remove', 'extend', 'clear', 'copy')),
    dict: frozenset(('get', 'items', 'keys', 'values', 'update', 'clear',
                     'pop', 'setdefault', 'copy')),
    str: frozenset(('split', 'strip', 'upper', 'lower', 'replace', 'find',
                    'count', 'startswith', 'endswith', 'isdigit')),
}
OPERATORS = {'Add': operator.add, 'Sub': operator.sub, 'Mult': operator.mul,
             'Div': operator.truediv, 'FloorDiv': operator.floordiv,
             'Mod': operator.mod, 'Pow': operator.pow, 'BitAnd': operator.and_,
             'BitOr': operator.or_, 'BitXor': operator.xor,
             'LShift': operator.lshift, 'RShift': operator.rshift}
ALLOWED_NODES = (
    ast.Module, ast.Expr, ast.Assign, ast.AugAssign, ast.If, ast.For, ast.While,
    ast.Break, ast.Continue, ast.Pass, ast.Name, ast.Constant, ast.List, ast.Tuple,
    ast.Dict, ast.Subscript, ast.Slice, ast.Call, ast.Attribute, ast.keyword,
    ast.BinOp, ast.UnaryOp, ast.BoolOp, ast.Compare, ast.IfExp,
    ast.Load, ast.Store, ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv,
    ast.Mod, ast.Pow, ast.BitAnd, ast.BitOr, ast.BitXor, ast.LShift, ast.RShift,
    ast.Not, ast.USub, ast.UAdd, ast.Invert, ast.And, ast.Or, ast.Eq, ast.NotEq,
    ast.Lt, ast.LtE, ast.Gt, ast.GtE, ast.In, ast.NotIn, ast.Is, ast.IsNot,
)


class SimulationError(Exception):
    """A friendly student-facing validation/runtime failure."""


class _ActorToken:
    def __init__(self, name):
        self.name = name


def _validate(value, depth=0, seen=None, counter=None):
    """Bound the entire object graph, including cyclic/nested containers."""
    counter = [0] if counter is None else counter
    counter[0] += 1
    if counter[0] > 10000:
        raise SimulationError('数据总量过大，请减少嵌套与重复容器。')
    if depth > 10:
        raise SimulationError('容器嵌套过深；请使用简单列表/字典。')
    if value is None or isinstance(value, _ActorToken):
        return
    if isinstance(value, int):
        if value.bit_length() > BIT_LIMIT:
            raise SimulationError('整数过大，超过本练习数值限制。')
    elif isinstance(value, float):
        if not math.isfinite(value) or abs(value) > 1e50:
            raise SimulationError('浮点数过大或不是有限数值。')
    elif isinstance(value, (str, list, tuple, dict, range)):
        if len(value) > VALUE_LIMIT:
            raise SimulationError('字符串/容器/范围超过1000项限制。')
        if not isinstance(value, (str, range)):
            seen = set() if seen is None else seen
            if id(value) in seen:
                raise SimulationError('不能创建循环引用容器。')
            seen.add(id(value))
            contents = list(value.items()) if isinstance(value, dict) else value
            for item in contents:
                _validate(item, depth + 1, seen, counter)
            seen.remove(id(value))
    else:
        raise SimulationError('本练习只支持基础数字、字符串、列表和字典数据。')


def _binary(name, left, right):
    _validate(left)
    _validate(right)
    if name == 'Mult':
        if isinstance(left, (str, list, tuple)) and isinstance(right, int):
            if len(left) * max(0, right) > VALUE_LIMIT:
                raise SimulationError('重复操作结果过大。')
        elif isinstance(right, (str, list, tuple)) and isinstance(left, int):
            if len(right) * max(0, left) > VALUE_LIMIT:
                raise SimulationError('重复操作结果过大。')
    if name in ('Pow', 'LShift', 'RShift'):
        if not isinstance(right, int) or abs(right) > 128:
            raise SimulationError('幂或移位次数过大（限128）。')
        if name == 'Pow' and isinstance(left, int) and left.bit_length() * max(0, right) > BIT_LIMIT:
            raise SimulationError('幂运算结果过大。')
    if name == 'Mod' and isinstance(left, str):
        raise SimulationError('本模拟器不支持字符串百分号格式化，请使用普通字符串操作。')
    result = OPERATORS[name](left, right)
    _validate(result)
    return result


def _check_ast(tree):
    nodes = list(ast.walk(tree))
    if len(nodes) > 1500:
        raise SimulationError('代码结构过多，请缩短程序。')
    call_attributes = {id(n.func) for n in nodes if isinstance(n, ast.Call)}
    protected = ACTIONS | frozenset(BUILTINS) | {'hero', 'luke', 'input', 'print'}
    for node in nodes:
        if not isinstance(node, ALLOWED_NODES):
            raise SimulationError('本练习不允许导入、函数/类定义、反射或高级语法。')
        if isinstance(node, ast.Name):
            if node.id.startswith('_') or '__' in node.id:
                raise SimulationError('禁止双下划线和内部名称访问。')
            if isinstance(node.ctx, ast.Store) and node.id in protected:
                raise SimulationError('不能覆盖游戏角色、动作或内置函数名称。')
        if isinstance(node, ast.Constant):
            _validate(node.value)
        if isinstance(node, ast.Attribute):
            if id(node) not in call_attributes or node.attr.startswith('_') or '__' in node.attr:
                raise SimulationError('只能调用公开方法，不能读取对象内部属性。')
            if node.attr not in ACTIONS | frozenset().union(*METHODS.values()):
                raise SimulationError('未知API或未允许的方法：' + node.attr)
        if isinstance(node, ast.Call):
            if any(k.arg is None for k in node.keywords):
                raise SimulationError('不支持展开关键字参数。')
            if isinstance(node.func, ast.Name):
                if node.func.id not in protected - {'hero', 'luke'}:
                    raise SimulationError('未知API或未允许的函数：' + node.func.id)
            elif not isinstance(node.func, ast.Attribute):
                raise SimulationError('不允许动态构造函数调用。')
        if isinstance(node, (ast.Assign, ast.AugAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Attribute):
                    raise SimulationError('不能修改角色内部属性。')


def _feature(tree, required):
    nodes = list(ast.walk(tree))
    if required == 'sequence':
        return not any(isinstance(n, (ast.For, ast.While, ast.If)) for n in nodes)
    if required in ('for', 'while', 'if', 'slice'):
        cls = {'for': ast.For, 'while': ast.While, 'if': ast.If, 'slice': ast.Slice}[required]
        return any(isinstance(n, cls) for n in nodes)
    methods = {'dict': {'get', 'items', 'keys', 'values', 'update'},
               'list': {'append', 'pop', 'reverse', 'insert', 'remove', 'extend', 'sort'}}
    return any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
               and n.func.attr in methods.get(required, set()) for n in nodes)


def _inplace(name, left, right):
    result = _binary(name, left, right)
    if isinstance(left, list) and name in ('Add', 'Mult'):
        left[:] = result
        return left
    return result


def _aug(receiver, key, name, old_value, value):
    receiver[key] = _inplace(name, old_value, value)
    _validate(receiver)


class _Transform(ast.NodeTransformer):
    """Route operations through size guards; no native function introspection."""
    def visit_Call(self, node):
        node = self.generic_visit(node)
        assert isinstance(node, ast.Call)
        if isinstance(node.func, ast.Name):
            name, receiver = node.func.id, ast.Constant(None)
        else:
            assert isinstance(node.func, ast.Attribute)
            name, receiver = node.func.attr, node.func.value
        return ast.copy_location(ast.Call(func=ast.Name(id='_call', ctx=ast.Load()),
            args=[ast.Constant(name), receiver] + node.args, keywords=node.keywords), node)

    def visit_BinOp(self, node):
        node = self.generic_visit(node)
        assert isinstance(node, ast.BinOp)
        return ast.copy_location(ast.Call(func=ast.Name(id='_binary', ctx=ast.Load()),
            args=[ast.Constant(type(node.op).__name__), node.left, node.right], keywords=[]), node)

    def visit_AugAssign(self, node):
        # Evaluate a subscript receiver/key once, before RHS, as CPython does.
        if isinstance(node.target, ast.Subscript):
            if isinstance(node.target.slice, ast.Slice):
                raise SimulationError('增强赋值支持变量或普通下标，不支持切片目标。')
            def temp(name, value):
                return ast.copy_location(ast.Assign(
                    targets=[ast.Name(id=name, ctx=ast.Store())], value=value), node)
            receiver = ast.Name(id='_aug_receiver', ctx=ast.Load())
            key = ast.Name(id='_aug_key', ctx=ast.Load())
            call = ast.Call(func=ast.Name(id='_aug', ctx=ast.Load()),
                args=[receiver, key, ast.Constant(type(node.op).__name__),
                      ast.Name(id='_aug_old', ctx=ast.Load()), self.visit(node.value)], keywords=[])
            return [temp('_aug_receiver', self.visit(node.target.value)),
                    temp('_aug_key', self.visit(node.target.slice)),
                    temp('_aug_old', ast.Subscript(value=receiver, slice=key, ctx=ast.Load())),
                    ast.copy_location(ast.Expr(value=call), node)]
        assert isinstance(node.target, ast.Name)
        rhs = ast.Call(func=ast.Name(id='_inplace', ctx=ast.Load()),
            args=[ast.Constant(type(node.op).__name__),
                  ast.Name(id=node.target.id, ctx=ast.Load()), self.visit(node.value)], keywords=[])
        assign = ast.Assign(targets=[node.target], value=rhs)
        return ast.copy_location(assign, node)


class _World:
    def __init__(self, task):
        self.task = task
        self.scene = copy.deepcopy(task['scenario'])
        self.trace = []
        self.action_count = 0
        self.steps = 0
        self.output_size = 0
        self.inputs = iter(copy.deepcopy(task['inputs'].get('stdin', [])))
        self.frame('初始地图（自编模拟）。')

    def frame(self, message):
        frame = {k: copy.deepcopy(self.scene[k]) for k in
                 ('width', 'height', 'actors', 'switches', 'enemies', 'walls')}
        frame['message'] = str(message)[:400]
        if len(self.trace) >= FRAME_LIMIT:
            self.trace[-1] = frame
        else:
            self.trace.append(frame)

    def action(self, name, receiver, args, kwargs):
        actor_name = 'hero' if receiver is None else receiver.name
        actor = next((a for a in self.scene['actors'] if a['name'] == actor_name), None)
        if actor is None:
            raise SimulationError('本题地图没有角色：' + actor_name)
        self.action_count += 1
        if self.action_count > ACTION_LIMIT:
            raise SimulationError('动作超过128次，程序已停止。')
        if kwargs or len(args) != (1 if name == 'move' else 0):
            raise SimulationError(name + ' 参数数量不正确；动作不接受关键字参数。')
        x, y = actor['x'], actor['y']
        dx, dy = ((1, 0), (0, 1), (-1, 0), (0, -1))[actor['direction']]
        if name == 'move':
            n = args[0]
            if type(n) is not int:
                raise SimulationError('move(n) 的n必须是整数，不接受字符串、浮点数或bool。')
            if abs(n) > 128 or self.steps + abs(n) > STEP_LIMIT:
                raise SimulationError('单次移动最多128格，总移动最多1024格。')
            sign = 1 if n >= 0 else -1
            for _ in range(abs(n)):
                nx, ny = actor['x'] + sign * dx, actor['y'] + sign * dy
                if not (0 <= nx < self.scene['width'] and 0 <= ny < self.scene['height']):
                    raise SimulationError('移动越出地图边界。')
                if [nx, ny] in self.scene['walls']:
                    raise SimulationError('移动遇到墙，不能穿过。')
                if any(e['active'] and (e['x'], e['y']) == (nx, ny) for e in self.scene['enemies']):
                    raise SimulationError('移动遇到活跃敌人，请在相邻格面向它攻击。')
                actor['x'], actor['y'] = nx, ny
                self.steps += 1
        elif name == 'turnLeft':
            actor['direction'] = (actor['direction'] - 1) % 4
        elif name == 'turnRight':
            actor['direction'] = (actor['direction'] + 1) % 4
        elif name == 'attack':
            enemy = next((e for e in self.scene['enemies'] if e['active'] and
                          (e['x'], e['y']) == (x + dx, y + dy)), None)
            if enemy is None:
                raise SimulationError('正前方相邻格没有活跃敌人，不能空击。')
            enemy['active'] = False
        elif name == 'press':
            switch = next((s for s in self.scene['switches'] if (s['x'], s['y']) == (x, y)), None)
            if switch is None or not switch['required'] or switch['pressed']:
                raise SimulationError('脚下不是可按的未按开关；禁止误按、禁按或重复按。')
            switch['pressed'] = True
        self.frame(actor_name + '.' + name + '(' + ', '.join(map(str, args)) + ')')

    def call(self, name, receiver, *args, **kwargs):
        for value in args:
            _validate(value)
        for value in kwargs.values():
            _validate(value)
        if name in ACTIONS:
            if receiver is not None and not isinstance(receiver, _ActorToken):
                raise SimulationError('游戏动作必须由hero或luke执行。')
            return self.action(name, receiver, args, kwargs)
        if receiver is None:
            if name == 'input':
                if len(args) > 1 or kwargs:
                    raise SimulationError('input参数不正确。')
                try:
                    return str(next(self.inputs))
                except StopIteration:
                    raise SimulationError('公开stdin已读完；本题无需额外隐藏输入。') from None
            if name == 'print':
                if kwargs.keys() - {'sep', 'end'}:
                    raise SimulationError('print只支持sep/end参数。')
                message = kwargs.get('sep', ' ').join(str(v) for v in args) + kwargs.get('end', '\n')
                self.output_size += len(message)
                if self.output_size > 4000:
                    raise SimulationError('输出过多，请删除重复print。')
                # Output does not count as an action and cannot satisfy map goals.
                return None
            if name == 'range':
                result = range(*args, **kwargs)
            elif name == 'enumerate':
                result = list(enumerate(*args, **kwargs))
            elif name == 'zip':
                result = list(zip(*args, **kwargs))
            else:
                result = BUILTINS[name](*args, **kwargs)
        else:
            _validate(receiver)
            if name not in METHODS.get(type(receiver), frozenset()):
                raise SimulationError('该数据类型不支持方法：' + name)
            if isinstance(receiver, str) and name == 'replace' and len(args) >= 2:
                old, new = args[0], args[1]
                if not isinstance(old, str) or not isinstance(new, str):
                    raise SimulationError('replace需要字符串参数。')
                if len(receiver) + receiver.count(old) * max(0, len(new) - len(old)) > VALUE_LIMIT:
                    raise SimulationError('replace结果过大。')
            result = getattr(receiver, name)(*args, **kwargs)
            if isinstance(receiver, dict) and name in ('items', 'keys', 'values'):
                result = list(result)
            _validate(receiver)
        _validate(result)
        return result

    def goal(self):
        if any(s['pressed'] != s['required'] for s in self.scene['switches']):
            return False, '目标未完成：检查每个必按开关是否点亮。'
        if any(e['active'] for e in self.scene['enemies']):
            return False, '目标未完成：仍有活跃敌人。'
        for name, endpoint in self.scene['endpoints'].items():
            actor = next(a for a in self.scene['actors'] if a['name'] == name)
            if [actor['x'], actor['y']] != endpoint:
                return False, '目标未完成：' + name + '还未到指定终点。'
        return True, '地图目标已完成。'


def _friendly(error):
    if isinstance(error, SimulationError):
        return str(error)
    if isinstance(error, SyntaxError):
        return '语法错误：检查第' + str(error.lineno or '?') + '行的缩进、括号和冒号。'
    names = {ZeroDivisionError: '除数不能为0。', NameError: '使用了未定义的变量或名称。',
             IndexError: '索引越界，请检查长度与循环边界。', KeyError: '字典没有该键，可检查键名或使用get。',
             TypeError: '参数类型或数量不正确。', ValueError: '数值转换或方法参数不正确。',
             OverflowError: '数值过大。', RecursionError: '代码嵌套过深。',
             MemoryError: '程序数据过大，已停止。'}
    return names.get(type(error), '程序运行失败，请检查本模拟器允许的语法和参数。')


def evaluate(exam_id, task_id, code):
    """Return only JSON-serializable grading and public replay data."""
    result = {'passed': False, 'stars': 0, 'error': '', 'reason': '', 'actionCount': 0, 'trace': []}
    world = None
    try:
        catalog = json.loads(Path(__file__).with_name('exams.json').read_text(encoding='utf-8'))
        task = next((t for e in catalog['exams'] if e['id'] == exam_id
                     for t in e['tasks'] if t['id'] == task_id), None)
        if task is None:
            raise SimulationError('未知试卷或题号。')
        world = _World(task)
        if not isinstance(code, str):
            raise SimulationError('程序必须是文本。')
        if len(code) > SOURCE_LIMIT:
            raise SimulationError('代码超过16000字符限制。')
        if not code.strip():
            raise SimulationError('还没有提交程序，请先编写动作。')
        tree = ast.parse(code, filename=FILENAME)
        _check_ast(tree)
        has_feature = _feature(tree, task['required'])
        if task.get('maxStatements') is not None:
            has_feature = has_feature and sum(isinstance(n, ast.stmt) for n in ast.walk(tree)) <= task['maxStatements']
        transformed = ast.fix_missing_locations(_Transform().visit(tree))
        compiled = compile(transformed, FILENAME, 'exec')
        env = copy.deepcopy(task['inputs'])
        _validate(env)
        env.update({'__builtins__': {}, '_call': world.call, '_binary': _binary, '_aug': _aug,
                    '_inplace': _inplace,
                    'hero': _ActorToken('hero'), 'luke': _ActorToken('luke')})
        lines = 0
        def tracer(frame, event, arg):
            nonlocal lines
            if frame.f_code.co_filename == FILENAME and event in ('line', 'return'):
                if event == 'line':
                    lines += 1
                    if lines > LINE_LIMIT:
                        raise SimulationError('运行超过3000行次，可能是无限循环；检查循环变量。')
                for name, value in frame.f_locals.items():
                    if not name.startswith('_'):
                        _validate(value)
            return tracer
        previous_trace = sys.gettrace()
        try:
            sys.settrace(tracer)
            exec(compiled, env, env)
        finally:
            sys.settrace(previous_trace)
        passed, reason = world.goal()
        result['passed'] = passed
        if passed:
            result['stars'] = 1 + int(has_feature) + int(world.action_count <= task['budget'])
            reason += f"获得{result['stars']}星。"
            if not has_feature:
                reason += '未用指定知识结构，扣1星（语法结构近似判断）。'
            if world.action_count > task['budget']:
                reason += '超出行动预算，扣1星。'
        result['reason'] = reason
    except Exception as error:
        result['error'] = _friendly(error)
        result['reason'] = result['error']
    if world is not None:
        world.frame(result['reason'])
        result['trace'] = world.trace
        result['actionCount'] = world.action_count
    return result
