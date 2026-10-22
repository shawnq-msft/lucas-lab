"""Self-authored educational simulator, not the official game engine."""
import ast
import copy
import io
import sys
import traceback
from collections import deque
from contextlib import redirect_stdout

LEVELS = [
 {'id':1,'title':'绕过岩壁','skill':'顺序 · 参数 · 方向','goal':'让hero从起点到绿色终点(5,1)，不要撞墙。只能用move和转向方法。','starter':'# hero开始朝右。坐标从0开始。\n# 先画出路线，再写代码。\n','hints':['先看hero三角形朝向。move(n)沿当前朝向前进n格。','墙占据(3,1)和(3,2)，可以从第3行绕过去。','把路线分成：向下、向右、向上。每次转弯后再移动。'],'api':['move(n) / hero.move(n)：向当前方向走n格','turnLeft() / turnRight()：原地转90度','坐标(x,y)：向右x增大，向下y增大']},
 {'id':2,'title':'收集星矿','skill':'列表 · for · 对象','goal':'用for遍历coins，收集全部三颗星矿。走到矿石所在格会自动收集。','starter':'# coins是矿石对象列表，不是字符串列表。\n# 点击地图上的矿石可查看名称。\n','hints':['coins[0]是列表中的第一个矿石对象。','for中的变量每轮代表一个对象。','把goto(当前对象)放到循环体里，注意冒号与缩进。'],'api':['coins：按编号排列的对象列表','goto(obj) / hero.goto(obj)：自动绕墙走向对象','本模拟goto会避开其他对象；到矿石格自动收集','for item in coins：遍历每一个矿石对象']},
 {'id':3,'title':'分清敌友','skill':'字典 · if · for','goal':'只击败hostile为True的守卫，保护友好守卫。攻击前先走近。','starter':'# monsters里既有敌人，也有朋友。\n# getDict(对象)可以读属性，返回的是副本。\n','hints':['点击每个守卫，看看hostile字段。','getDict(monster)["hostile"]可作为if条件。','只有敌人才需要goto和attack，这两句都应在if里面。'],'api':['monsters：守卫对象列表','getDict(obj)：返回对象属性字典副本','goto(monster)：走到守卫的相邻格','attack() / actor.attack()：攻击刚靠近的守卫一次']},
 {'id':4,'title':'派谁出发','skill':'函数 · 参数 · 返回对象','goal':'定义一个函数返回离目标更近的角色；遍历monsters，让选出的角色去攻击。相同距离时选hygeia。距离按当前格的曼哈顿距离计算。','starter':'# hero是青色角色，hygeia是橙色伙伴。\n# 每次选人时重新比较距离。\n','hints':['hero.dTo(target)和hygeia.dTo(target)分别返回距离。','函数应return hero或return hygeia，而不是返回角色名字的字符串。','把返回的角色存进变量，再由该变量调用goto和attack。'],'api':['actor.dTo(target)：横向格数差＋纵向格数差','return hero / return hygeia：返回角色对象','actor.goto(target)、actor.attack()：由指定角色行动','本关要求使用自定义函数和return；平局选hygeia']},
 {'id':5,'title':'解开星门','skill':'字符串 · 切片 · lower','goal':'取message索引1、3、5处的字符，转成小写，用unlock提交口令；门开后让hero前进到终点。','starter':'# message显示在任务面板里。\n# unlock是本模拟新增的关卡方法。\n','hints':['切片的结束位置不包含在结果中。','索引1、3、5可以用起点1、结束7、步长2取出。','先把截取结果lower()，交给unlock，再前进。'],'api':['message：本关密码原文字符串','message[start:stop:step]：字符串切片','text.lower()：转成小写','unlock(text)：本模拟专用，提交星门口令']},
 {'id':6,'title':'安全采集任务','skill':'函数 · 列表 · 字典 · 组合条件','goal':'定义筛选函数，返回safe为True且value不少于limit的矿石对象列表；再遍历结果收集。不要收集其他矿石。','starter':'# 可用coins、limit、getDict、goto。\n# 函数应返回对象列表，而不是打印名称。\n','hints':['新建一个空列表，用for逐个读getDict(item)。','safe与value两个条件都必须满足；注意“不少于”包括等于。','用append保存对象；遍历结束后return列表，再在函数外遍历返回结果。'],'api':['getDict(item)：包括name、safe、value等属性','limit：本关价值门槛','list.append(item)：保存对象供后面行动','本关要求使用自定义函数和return；getDict返回副本']}
]

def catalog():
    return copy.deepcopy(LEVELS)

class GameError(Exception): pass

class Thing:
    def __init__(self, world, name, x, y, kind, **attrs):
        self._world=world; self.name=name; self.x=x; self.y=y; self.kind=kind
        self.active=True; self.attrs=attrs
    def data(self):
        return dict(name=self.name,x=self.x,y=self.y,kind=self.kind,active=self.active,**self.attrs)

class Actor(Thing):
    def __init__(self,world,name,x,y,direction=0):
        super().__init__(world,name,x,y,'actor')
        self.direction=direction; self._target=None
    def data(self):
        return dict(super().data(),direction=self.direction)
    def move(self,n):
        if type(n) is not int or not 0<=n<=80:
            raise GameError('move参数必须是0到80的非负整数。')
        for _ in range(n):
            dx,dy=((1,0),(0,1),(-1,0),(0,-1))[self.direction]
            self._world.step(self,self.x+dx,self.y+dy)
    def turnLeft(self):
        self.direction=(self.direction-1)%4; self._world.frame(self.name+' 左转')
    def turnRight(self):
        self.direction=(self.direction+1)%4; self._world.frame(self.name+' 右转')
    def dTo(self,target):
        if not isinstance(target,Thing): raise GameError('dTo需要一个对象，不是对象名字字符串。')
        return abs(self.x-target.x)+abs(self.y-target.y)
    def goto(self,target):
        w=self._world
        if w.level==1: raise GameError('第一关请使用move和转向，不使用goto。')
        if not isinstance(target,Thing): raise GameError('goto需要对象，例如coins[0]，不能传名称字符串。')
        if not target.active: raise GameError(target.name+' 已完成，不需要再次前往。')
        if w.level==4:
            expected=w.hero if w.hero.dTo(target)<w.hygeia.dTo(target) else w.hygeia
            if self is not expected: raise GameError('这次应由更近的 '+expected.name+' 行动（相同距离选hygeia）。')
        blocked={(o.x,o.y) for o in w.objects if o.active and o is not target}
        if target.kind=='monster':
            blocked.add((target.x,target.y))
            goals={(target.x+dx,target.y+dy) for dx,dy in ((1,0),(0,1),(-1,0),(0,-1))}
        else: goals={(target.x,target.y)}
        path=w.path((self.x,self.y),goals,blocked)
        if path is None: raise GameError('找不到可通行路线，请检查地图。')
        for x,y in path:
            dx,dy=x-self.x,y-self.y
            self.direction=((1,0),(0,1),(-1,0),(0,-1)).index((dx,dy))
            w.step(self,x,y)
        self._target=target
        w.frame(self.name+' 已靠近 '+target.name)
    def attack(self):
        w=self._world; target=self._target
        if target is None or target.kind!='monster' or not target.active or self.dTo(target)>1:
            raise GameError('攻击前请先goto一个仍在场的守卫，并站在相邻格。')
        if not target.attrs.get('hostile',False): raise GameError('不能攻击友好守卫 '+target.name+'。')
        target.active=False; w.defeated.append(target.name)
        w.frame(self.name+' 击败 '+target.name)

class World:
    def __init__(self,level,variant):
        self.level=level; self.variant=variant; self.walls=[]; self.objects=[]; self.trace=[]
        self.collected=[]; self.defeated=[]; self.unlocked=False; self.message=''; self.limit=10
        self.exit=None; self.gate=None; self.actions=0
        self.hero=Actor(self,'hero',1,1); self.hygeia=Actor(self,'hygeia',6,4)
        self.actors=[self.hero]
        if level==1:
            self.walls=[(3,1),(3,2)]; self.exit=(5,1)
        elif level==2:
            coords=[(5,1),(2,4),(6,4)] if not variant else [(6,1),(1,4),(5,4)]
            self.walls=[(3,2),(3,3)]
            for i,(x,y) in enumerate(coords): self.objects.append(Thing(self,'coins['+str(i)+']',x,y,'coin',value=1,safe=True))
        elif level==3:
            for i,(x,y) in enumerate([(5,1),(2,4),(6,4)]):
                self.objects.append(Thing(self,'monsters['+str(i)+']',x,y,'monster',hostile=(i != (0 if variant else 1))))
        elif level==4:
            self.actors.append(self.hygeia)
            if variant: self.hero.x,self.hero.y=6,1; self.hygeia.x,self.hygeia.y=1,4
            for i,(x,y) in enumerate([(5,4),(2,1)]): self.objects.append(Thing(self,'monsters['+str(i)+']',x,y,'monster',hostile=True))
        elif level==5:
            self.message='xMuOwOn' if variant else 'xSuUxNq'; self.gate=(3,1); self.exit=(5,1)
            self.walls=[(x,y) for x in range(8) for y in range(6) if y!=1]
        elif level==6:
            self.limit=8 if variant else 10
            values=[12,10,20,3,8] if not variant else [7,8,15,9,2]
            for i,(x,y) in enumerate([(5,1),(1,4),(6,4),(4,3),(6,2)]):
                self.objects.append(Thing(self,'coins['+str(i)+']',x,y,'coin',value=values[i],safe=i!=2))
        else: raise GameError('未知关卡。')
        self.required=[o.name for o in self.objects if o.kind=='coin' and (level!=6 or o.attrs['safe'] and o.attrs['value']>=self.limit)]
        self.frame('初始状态',count=False)
    def frame(self,label,count=True):
        if count:
            self.actions+=1
            if self.actions>160: raise GameError('动作超过160次，程序可能重复执行了太多次。')
        self.trace.append({'label':label,'actors':[a.data() for a in self.actors], 'objects':[o.data() for o in self.objects], 'walls':self.walls[:], 'exit':self.exit,'gate':self.gate,'unlocked':self.unlocked,'message':self.message,'limit':self.limit,'collected':self.collected[:],'defeated':self.defeated[:]})
    def blocked(self,x,y):
        return not(0<=x<8 and 0<=y<6) or (x,y) in self.walls or (self.gate==(x,y) and not self.unlocked)
    def step(self,actor,x,y):
        if not(0<=x<8 and 0<=y<6): raise GameError('走出了地图边界。')
        if (x,y) in self.walls: raise GameError('撞墙了，检查朝向和步数。')
        if self.gate==(x,y) and not self.unlocked: raise GameError('星门还没打开，请先unlock正确口令。')
        if any(o.active and o.kind=='monster' and (o.x,o.y)==(x,y) for o in self.objects): raise GameError('守卫占据这个格子；请用goto靠近，再attack。')
        actor.x=x;actor.y=y
        for o in self.objects:
            if o.active and o.kind=='coin' and (o.x,o.y)==(x,y):
                if self.level==6 and o.name not in self.required:
                    raise GameError('收集了不符合条件的矿石 '+o.name+'，重新检查safe和门槛。')
                o.active=False; self.collected.append(o.name)
        self.frame(actor.name+' → ('+str(x)+','+str(y)+')')
    def path(self,start,goals,blocked):
        q=deque([(start,[])]); seen={start}
        while q:
            point,path=q.popleft()
            if point in goals:return path
            for dx,dy in ((1,0),(0,1),(-1,0),(0,-1)):
                nxt=(point[0]+dx,point[1]+dy)
                if nxt in seen or nxt in blocked or self.blocked(*nxt):continue
                seen.add(nxt);q.append((nxt,path+[nxt]))
        return None
    def unlock(self,password):
        if self.level!=5:raise GameError('本关没有密码门。')
        if password!=self.message[1:7:2].lower():raise GameError('口令不正确，检查切片位置和大小写。')
        self.unlocked=True;self.frame('星门已解锁')
    def passed(self):
        if self.level in (1,5): return (self.hero.x,self.hero.y)==self.exit and (self.level!=5 or self.unlocked)
        if self.level in (2,6):return set(self.collected)==set(self.required)
        return all(not o.active for o in self.objects if o.attrs.get('hostile'))

ALLOWED_ATTRS={'move','turnLeft','turnRight','goto','attack','dTo','lower','upper','count','append','reverse','pop','clear'}

def evaluate(level,code,variant=0):
    w=World(int(level),int(variant)); error='';line=None; buf=io.StringIO(); tree=None
    try:
        if len(code)>12000:raise GameError('代码过长，请缩短后再运行。')
        tree=ast.parse(code,filename='<student>')
        for node in ast.walk(tree):
            if isinstance(node,(ast.Import,ast.ImportFrom,ast.ClassDef,ast.Global,ast.Nonlocal,ast.With,ast.AsyncFunctionDef)):
                raise GameError('本练习不需要导入库、定义类或访问外部资源。')
            if isinstance(node,ast.Name) and node.id.startswith('__'):raise GameError('不能访问解释器内部名称。')
            if isinstance(node,ast.Attribute) and (node.attr not in ALLOWED_ATTRS or not isinstance(node.ctx,ast.Load)):
                raise GameError('请使用面板列出的方法；对象属性请用getDict读取。')
        def get_dict(obj):
            if not isinstance(obj,Thing):raise GameError('getDict需要一个对象。')
            return copy.deepcopy(obj.data())
        safe={'print':print,'range':range,'len':len,'str':str,'int':int,'float':float,'bool':bool,'list':list,'dict':dict,'min':min,'max':max,'sum':sum,'abs':abs,'enumerate':enumerate,'sorted':sorted}
        ns={'__builtins__':safe,'hero':w.hero,'hygeia':w.hygeia,'coins':[o for o in w.objects if o.kind=='coin'],'monsters':[o for o in w.objects if o.kind=='monster'],'getDict':get_dict,'message':w.message,'limit':w.limit,'unlock':w.unlock}
        for name in ('move','turnLeft','turnRight','goto','attack'): ns[name]=getattr(w.hero,name)
        ticks=[0]
        def trace(frame,event,arg):
            if frame.f_code.co_filename=='<student>' and event in ('line','call'):
                ticks[0]+=1
                if ticks[0]>12000:raise GameError('执行步骤过多，可能出现无限循环。')
            return trace
        oldtrace=sys.gettrace()
        try:
            sys.settrace(trace)
            with redirect_stdout(buf):exec(compile(tree,'<student>','exec'),ns)
        finally:sys.settrace(oldtrace)
        if not w.passed(): error='程序运行完毕，但任务还没完成。请检查剩余目标或终点。'
        elif level in (2,3,4,6) and not any(isinstance(n,ast.For) for n in ast.walk(tree)):
            error='地图任务完成了；本关还要求使用for遍历对象，不能逐个硬编码。'
        elif level in (4,6) and not(any(isinstance(n,ast.FunctionDef) for n in ast.walk(tree)) and any(isinstance(n,ast.Return) for n in ast.walk(tree))):
            error='地图任务完成了；本关还要求自定义函数并用return返回结果。'
    except Exception as e:
        error=type(e).__name__+': '+str(e)
        if isinstance(e,SyntaxError):line=e.lineno
        else:
            frames=traceback.extract_tb(e.__traceback__)
            for f in frames:
                if f.filename=='<student>':line=f.lineno
    return {'passed':not bool(error),'error':error,'errorLine':line,'stdout':buf.getvalue()[:5000],'trace':w.trace,'actions':w.actions}
