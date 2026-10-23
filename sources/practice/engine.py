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

LEVELS += [
 {'id':7,'title':'矿石稳定排序','stars':2,'category':'higher','skill':'提高 · 稳定插入排序','goal':'非官方拓展：按value从小到大收集所有矿石；同价值保持coins原来的先后顺序。自己实现插入排序，不用sorted或sort，最后逐个goto行动。','starter':'# coins的原顺序也是同价值时的先后依据。\n# 先排序对象列表，再goto收集。\n','hints':['维护一个已排好序的对象列表。','将新矿石插入合适位置，把较大价值的对象向后移。','只移动严格更大的价值，别移动相等的对象。'],'api':['coins / getDict(coin)["value"]：对象列表与价值','goto(coin)：走到矿石并自动收集，判定顺序','本关禁用sorted与sort；这些规则是自制非官方拓展']},
 {'id':8,'title':'迷宫最短路线','stars':3,'category':'higher','skill':'提高 · BFS · 队列 · 路径','goal':'非官方拓展：自己用BFS求从start到goal的最短路线。submit提交包含起点和终点的坐标列表；验证后hero沿该路线行动，不会自动替你找路。','starter':'# maze[y][x]为"#"表示墙，"."表示路。\n# 坐标用(x,y)；只能上下左右移动。\n# 用列表作队列：append入队，pop(0)出队。\n','hints':['队列先放入起点，同时记录已经发现的格子。','每次取最早入队的格子，检查四个相邻位置。','记录前驱或整条路径，找到goal后submit路径。'],'api':['maze：6行8列字符串列表；#为墙、.为路','start / goal：起点和终点(x,y)','submit(path)：提交完整最短坐标列表，允许任意等长最短路','list.append / list.pop(0)：本练习可用的队列操作；submit是非官方自制API']},
 {'id':9,'title':'递归巡访二叉树','stars':2,'category':'higher','skill':'提高 · 递归 · 前序遍历','goal':'非官方拓展：用真正递归按“根→左子树→右子树”访问二叉树。submit节点编号列表；hero将按顺序巡访。空孩子为None，不能按字母排序或只打印。','starter':'# tree[节点编号]是含left、right的字典。\n# root是根节点编号，None表示没有孩子。\n# 定义递归函数，把访问顺序保存到列表。\n','hints':['遇到None就返回，这是递归终止条件。','先记录当前节点，再处理左孩子，最后右孩子。','在递归外调用根节点，完成后submit列表。'],'api':['tree[node]["left"] / tree[node]["right"]：孩子编号或None','root：本题组根节点编号','submit(order)：提交前序编号列表，必须实际执行递归','tree是输入副本；本关API均为非官方自制拓展']},
 {'id':10,'title':'取石必胜策略','stars':3,'category':'higher','skill':'提高 · 博弈 · 动态规划','goal':'非官方拓展：两人轮流取石，每回合从moves选一个不超过剩余数量的数；不能行动者输。双方最优，submit提交能保证获胜的第一步；若必败提交整数0。验证后播放双方对局。','starter':'# stones为初始石子数，moves为允许取法。\n# 先考虑0颗时当前玩家能不能赢。\n# submit一个整数，不是整场行动列表。\n','hints':['不能行动的局面是必败状态。','如果存在一步能把对方送入必败局面，当前状态就是必胜。','由小到大计算状态，选择使对方必败的一步；无必胜步才提交0。'],'api':['stones：初始石子数；moves：允许的正整数取法列表','submit(take)：提交任一必胜取法；必败时仅接受整数0','取完最后一颗者获胜；自动对手也按最优策略行动','submit与对局回放为非官方自制拓展']}
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
        self.submitted=False; self.input={}; self.visited=[]; self.remaining=None
        self.recursed=False
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
        elif level==7:
            values=[7,2,7,0,2,9] if not variant else [4,8,1,4,0,1]
            for i,(x,y) in enumerate([(6,1),(2,4),(6,4),(4,2),(1,3),(5,3)]):
                self.objects.append(Thing(self,'coins['+str(i)+']',x,y,'coin',value=values[i],safe=True))
            self.input={'values':values}
        elif level==8:
            self.maze=['########','#..#...#','#..#.#.#','#....#.#','#.#....#','########'] if not variant else ['########','#....#.#','###..#.#','#.#....#','#...#..#','########']
            self.start=(1,1) if not variant else (1,4); self.goal=(6,1)
            self.hero.x,self.hero.y=self.start; self.exit=self.goal
            self.walls=[(x,y) for y,row in enumerate(self.maze) for x,c in enumerate(row) if c=='#']
            self.input={'maze':self.maze,'start':self.start,'goal':self.goal}
        elif level==9:
            self.root='A' if not variant else 'K'
            links={'A':('B','C'),'B':('D','E'),'C':(None,'F'),'D':(None,None),'E':(None,None),'F':(None,None)} if not variant else {'K':('M','B'),'M':(None,'Z'),'Z':('C',None),'C':(None,None),'B':('Y',None),'Y':(None,None)}
            self.tree={n:{'left':a,'right':b} for n,(a,b) in links.items()}
            coords=[(4,0),(2,2),(6,2),(1,4),(3,4),(6,4)] if not variant else [(4,0),(2,1),(3,3),(2,5),(6,2),(5,4)]
            for n,(x,y) in zip(links,coords): self.objects.append(Thing(self,n,x,y,'node',**self.tree[n]))
            self.input={'tree':self.tree,'root':self.root}
        elif level==10:
            self.stones=10 if not variant else 12; self.moves=[1,3,4] if not variant else [1,2]
            self.actors.append(self.hygeia);self.remaining=self.stones
            for i in range(self.stones): self.objects.append(Thing(self,'stone'+str(i),i%6+1,i//6+2,'stone'))
            self.input={'stones':self.stones,'moves':self.moves}
        else: raise GameError('未知关卡。')
        self.required=[o.name for o in self.objects if o.kind=='coin' and (level!=6 or o.attrs['safe'] and o.attrs['value']>=self.limit)]
        if level==7:self.required=[o.name for o in sorted(self.objects,key=lambda o:o.attrs['value'])]
        self.frame('初始状态',count=False)
    def frame(self,label,count=True):
        if count:
            self.actions+=1
            if self.actions>160: raise GameError('动作超过160次，程序可能重复执行了太多次。')
        self.trace.append({'label':label,'actors':[a.data() for a in self.actors], 'objects':[o.data() for o in self.objects], 'walls':self.walls[:], 'exit':self.exit,'gate':self.gate,'unlocked':self.unlocked,'message':self.message,'limit':self.limit,'collected':self.collected[:],'defeated':self.defeated[:]})
        if self.level>=7:self.trace[-1].update(input=copy.deepcopy(self.input),visited=self.visited[:],remaining=self.remaining)
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
                if self.level==7 and o.name!=self.required[len(self.collected)]:
                    raise GameError('收集顺序不正确：按价值升序，相同价值保持coins原顺序。')
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
        if self.level in (8,9,10):return self.submitted
        if self.level==7:return self.collected==self.required
        if self.level in (1,5): return (self.hero.x,self.hero.y)==self.exit and (self.level!=5 or self.unlocked)
        if self.level in (2,6):return set(self.collected)==set(self.required)
        return all(not o.active for o in self.objects if o.attrs.get('hostile'))

    def submit(self,result):
        if self.submitted:raise GameError('每次运行只能submit一次。')
        if self.level==8:
            if type(result) is not list or not 1<=len(result)<=48:raise GameError('路线必须是包含起终点的坐标列表。')
            if any(type(p) not in (tuple,list) or len(p)!=2 or any(type(n) is not int for n in p) for p in result):raise GameError('每个坐标必须由两个整数构成。')
            route=[tuple(p) for p in result]
            if route[0]!=self.start or route[-1]!=self.goal:raise GameError('路线必须包含正确的起点和终点。')
            if any(self.blocked(*p) for p in route) or any(abs(a[0]-b[0])+abs(a[1]-b[1])!=1 for a,b in zip(route,route[1:])):raise GameError('路线撞墙、越界或没有逐格相邻。')
            shortest=self.path(self.start,{self.goal},set())
            if shortest is None or len(route)!=len(shortest)+1:raise GameError('路线可达，但不是最短路线。')
            for p in route[1:]:self.step(self.hero,*p)
        elif self.level==9:
            expected=[]
            def walk(n):
                if n is not None:
                    expected.append(n);walk(self.tree[n]['left']);walk(self.tree[n]['right'])
            walk(self.root)
            if type(result) is not list or result!=expected:raise GameError('节点顺序不正确，请按根、左、右访问。')
            if not self.recursed:raise GameError('本关需要实际调用递归函数，不是硬编码节点列表。')
            for name in result:
                node=next(o for o in self.objects if o.name==name)
                self.hero.goto(node);self.visited.append(name);self.frame('访问节点 '+name)
        elif self.level==10:
            win=[False]*(self.stones+1)
            for n in range(1,self.stones+1):win[n]=any(m<=n and not win[n-m] for m in self.moves)
            choices=[m for m in self.moves if m<=self.stones and not win[self.stones-m]]
            if type(result) is not int or (result not in choices if choices else result!=0):raise GameError('不是必胜第一步；只有必败局面才应提交整数0。')
            self.remaining=self.stones;turn=0;first=True
            if result==0:self.frame('判定为必败局面；演示最优对局')
            while any(m<=self.remaining for m in self.moves):
                legal=[m for m in self.moves if m<=self.remaining]
                take=result if first and result else next((m for m in legal if not win[self.remaining-m]),legal[0])
                actor=self.actors[turn]
                for _ in range(take):
                    stone=next((o for o in self.objects if o.active),None)
                    if stone:
                        actor.goto(stone);stone.active=False
                    self.remaining-=1;self.frame(actor.name+' 取石，剩余 '+str(self.remaining))
                first=False;turn=1-turn
            self.frame(self.actors[turn].name+' 无合法取法，输掉对局')
        else:raise GameError('本关请通过地图行动完成，不使用submit。')
        self.submitted=True

ALLOWED_ATTRS={'move','turnLeft','turnRight','goto','attack','dTo','lower','upper','count','append','reverse','pop','clear'}

def evaluate(level,code,variant=0):
    w=World(int(level),int(variant)); error='';line=None; buf=io.StringIO(); tree=None
    try:
        if len(code)>12000:raise GameError('代码过长，请缩短后再运行。')
        tree=ast.parse(code,filename='<student>')
        for node in ast.walk(tree):
            if level==7 and isinstance(node,ast.Name) and node.id=='sorted':raise GameError('本关请自己实现插入排序，不使用sorted。')
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
        if level>=7:ns.update(copy.deepcopy(w.input),submit=w.submit)
        for name in ('move','turnLeft','turnRight','goto','attack'): ns[name]=getattr(w.hero,name)
        ticks=[0]
        def trace(frame,event,arg):
            if frame.f_code.co_filename=='<student>' and event in ('line','call'):
                if event=='call':
                    parent=frame.f_back
                    while parent and parent.f_code.co_filename=='<student>':
                        if parent.f_code is frame.f_code:w.recursed=True
                        parent=parent.f_back
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
