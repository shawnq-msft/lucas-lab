// Pure, deterministic traces. Every frame owns its snapshot; no DOM or storage here.
const clone=x=>JSON.parse(JSON.stringify(x));
function recorder(){const frames=[];return {frames,add:(items,caption,active=[],extra={})=>frames.push(clone({items,caption,active,...extra}))};}
export function sortTrace(kind,input){
 const a=[...input],{frames,add}=recorder();
 add(a,'从这排数据开始。绿色框是当前比较或写入的位置。');
 if(kind==='insertion'){
  for(let i=1;i<a.length;i++){
   const key=a[i];let j=i-1;add(a,`暂存 ${key}，左边 [0, ${i-1}] 已经有序。`,[i],{held:key,prefix:i});
   while(j>=0){add(a,`比较 ${a[j]} 与暂存的 ${key}。`,[j],{held:key,prefix:i});if(a[j]<=key)break;a[j+1]=a[j];add(a,`${a[j]} 右移一格；空位移到编号 ${j}。`,[j+1],{held:key,hole:j,prefix:i});j--;}
   a[j+1]=key;add(a,`把暂存的 ${key} 插入编号 ${j+1}。`,[j+1],{prefix:i+1});
  }
 }else if(kind==='merge'){
  const merge=(lo,hi)=>{if(hi-lo<=1)return;const mid=Math.floor((lo+hi)/2);add(a,`拆分 [${lo}, ${hi}) 为 [${lo}, ${mid}) 和 [${mid}, ${hi})。`,Array.from({length:hi-lo},(_,i)=>lo+i),{range:[lo,mid,hi]});merge(lo,mid);merge(mid,hi);
   const left=a.slice(lo,mid),right=a.slice(mid,hi);let i=0,j=0,k=lo;
   add(a,`合并两个有序小队：[${left}] 与 [${right}]。`,[],{left,right});
   while(i<left.length||j<right.length){const takeLeft=j===right.length||(i<left.length&&left[i]<=right[j]);const v=takeLeft?left[i++]:right[j++];a[k]=v;add(a,`取${takeLeft?'左':'右'}队当前最小值 ${v}，写入编号 ${k}。`,[k],{left:left.slice(i),right:right.slice(j),range:[lo,mid,hi]});k++;}
  };merge(0,a.length);
 }else if(kind==='quick'){
  const quick=(lo,hi)=>{if(lo>=hi)return;const pivot=a[hi];let i=lo;add(a,`选择末尾 ${pivot} 为基准；扫描 [${lo}, ${hi})。`,[hi],{pivot,range:[lo,hi]});
   for(let j=lo;j<hi;j++){add(a,`比较 ${a[j]} < 基准 ${pivot}？`,[j,hi],{pivot,boundary:i});if(a[j]<pivot){[a[i],a[j]]=[a[j],a[i]];add(a,`放进“小于基准”的左区，边界右移。`,[i,j],{pivot,boundary:i+1});i++;}}
   [a[i],a[hi]]=[a[hi],a[i]];add(a,`基准 ${pivot} 就位于编号 ${i}，两侧分别递归。`,[i],{pivot,settled:i});quick(lo,i-1);quick(i+1,hi);
  };quick(0,a.length-1);
 }else if(kind==='heap'){
  const sift=(root,size)=>{while(2*root+1<size){let child=2*root+1;if(child+1<size){add(a,'比较左右孩子，选择较大的孩子。',[child,child+1],{heapSize:size});if(a[child+1]>a[child])child++;}add(a,`比较父节点 ${a[root]} 与较大孩子 ${a[child]}。`,[root,child],{heapSize:size});if(a[root]>=a[child])break;[a[root],a[child]]=[a[child],a[root]];add(a,'较大孩子上浮，继续向下修复堆。',[root,child],{heapSize:size});root=child;}};
  for(let root=Math.floor(a.length/2)-1;root>=0;root--)sift(root,a.length);
  add(a,'大顶堆建好：父节点不小于孩子，堆顶是最大值。',a.length?[0]:[],{heapSize:a.length});
  for(let end=a.length-1;end>0;end--){[a[0],a[end]]=[a[end],a[0]];add(a,`堆顶最大值移到编号 ${end}；右侧不再参加堆调整。`,[0,end],{heapSize:end});sift(0,end);}
 }else throw Error('Unknown sort');
 add(a,'排序完成：从小到大。',[],{done:true});return frames;
}
export function recursionTrace(n){
 const {frames,add}=recorder(),stack=[];
 const fact=x=>{stack.push(x);add([...stack],`调用 factorial(${x})，新任务压入调用栈。`,[stack.length-1],{stack,phase:'call'});let result;
  if(x===0){result=1;add([...stack],'基例 n == 0：直接返回 1，不再调用自己。',[stack.length-1],{stack,phase:'base',result});}
  else {const child=fact(x-1);result=x*child;add([...stack],`收到子调用返回的 ${child}，计算 ${x} × ${child} = ${result}。`,[stack.length-1],{stack,phase:'multiply',result});}
  stack.pop();add([...stack],`factorial(${x}) 返回 ${result}，这一层离开调用栈。`,stack.length?[stack.length-1]:[],{stack,phase:'return',result});return result;};fact(n);return frames;
}
export function treeLayout(tree){
 const nodes=[],edges=[];const visit=(t,x=160,y=30,gap=76,depth=0,parent=null)=>{if(!t)return;const key=String(t.value);nodes.push({key,label:key,x,y,depth});if(parent!==null)edges.push([parent,key]);visit(t.left,x-gap,y+64,gap/2,depth+1,key);visit(t.right,x+gap,y+64,gap/2,depth+1,key);};visit(tree);return {nodes,edges};
}
export function treeTrace(tree,mode){
 if(!['preorder','inorder','postorder'].includes(mode))throw Error('Unknown traversal');
 const layout=treeLayout(tree),items=layout.nodes.map(n=>n.key),visited=[],path=[],{frames,add}=recorder();
 const push=(caption,node)=>add(items,caption,node?[items.indexOf(String(node.value))]:[],{...layout,visited,path,kind:'tree'});
 push('遵守左右方向；“访问”时才把节点写进输出。');
 const walk=t=>{if(!t)return;path.push(String(t.value));push(`进入节点 ${t.value}，沿调用路径向下。`,t);
  const emit=()=>{visited.push(t.value);push(`访问 ${t.value}，输出：[${visited.join(' → ')}]。`,t);};
  if(mode==='preorder')emit();walk(t.left);if(mode==='inorder')emit();walk(t.right);if(mode==='postorder')emit();path.pop();push(`节点 ${t.value} 的子任务完成，返回上一层。`,t);
 };walk(tree);push('遍历完成，每个节点恰好访问一次。');return frames;
}
export function stoneTrace(n,limit=3){
 const {frames,add}=recorder(),winning=Array(n+1).fill(null),items=Array.from({length:n+1},(_,i)=>i);winning[0]=false;
 const push=(caption,active=[],extra={})=>add(items,caption,active,{winning,kind:'stones',limit,...extra});
 push('规则：每次取 1 到上限颗，取到最后一颗获胜。0 颗时轮到你，已经输了。',[0]);
 for(let count=1;count<=n;count++){
  winning[count]=false;
  for(let take=1;take<=Math.min(count,limit);take++){
   push(`${count} 颗取 ${take} 颗，把 ${count-take} 颗留给对手：${winning[count-take]?'对手有必胜策略':'对手是必败状态'}。`,[count,count-take],{take});
   if(!winning[count-take]){winning[count]=true;push(`找到走法！${count} 颗是必胜态，因为可以送给对手一个必败态。`,[count],{take});break;}
  }
  if(!winning[count])push(`${count} 颗是必败态：每种合法走法都会把必胜态交给对手。`,[count]);
 }
 const moves=Array.from({length:Math.min(n,limit)},(_,i)=>i+1).filter(k=>!winning[n-k]);push(`推理完成：${n} 颗是${winning[n]?'必胜':'必败'}态。${moves.length?'可取 '+moves.join('、')+' 颗。':'双方最优时没有必胜走法。'}`,[n],{moves,done:true});return frames;
}
export function minimaxTrace(tree){
 const {frames,add}=recorder(),nodes=[],edges=[],values={},path=[];
 const layout=(t,key='R',depth=0,x=160,gap=80,parent=null)=>{nodes.push({key,label:Array.isArray(t)?(depth%2?'MIN':'MAX'):String(t),x,y:30+depth*64,depth,leaf:!Array.isArray(t)});if(parent)edges.push([parent,key]);if(Array.isArray(t))t.forEach((c,i)=>layout(c,key+i,depth+1,x+(i-(t.length-1)/2)*gap*2,gap/2,key));};layout(tree);
 const items=nodes.map(n=>n.key),push=(caption,key,extra={})=>add(items,caption,key?[items.indexOf(key)]:[],{nodes,edges,values,path,kind:'minimax',...extra});
 push('分数始终从 MAX 的视角看：MAX 想大，MIN 想小；双方都聪明。');
 const solve=(t,key='R',depth=0)=>{path.push(key);push(`进入 ${key}：${Array.isArray(t)?depth%2?'MIN 的回合':'MAX 的回合':'叶子结局'}。`,key);let value;
  if(!Array.isArray(t)){value=t;values[key]=value;push(`叶子给出分数 ${value}。`,key);}
  else {const children=t.map((c,i)=>solve(c,key+i,depth+1));value=(depth%2?Math.min:Math.max)(...children);values[key]=value;push(`${depth%2?'MIN 选最小':'MAX 选最大'}：${children.join('、')} → ${value}，把它返回给父节点。`,key);}
  path.pop();return value;};const result=solve(tree);push(`回传完成：双方最优时，MAX 能保证的分数是 ${result}。`,'R',{result,done:true});return frames;
}
const codes={
 insertion:`def insertion(a):
    for i in range(1, len(a)):
        key, j = a[i], i - 1
        while j >= 0 and a[j] > key:
            a[j + 1] = a[j]
            j -= 1
        a[j + 1] = key
    return a`,
 merge:`def merge_sort(a):
    if len(a) <= 1:
        return a[:]
    mid = len(a) // 2
    left = merge_sort(a[:mid])
    right = merge_sort(a[mid:])
    out, i, j = [], 0, 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            out.append(left[i]); i += 1
        else:
            out.append(right[j]); j += 1
    return out + left[i:] + right[j:]`,
 quick:`def quick_sort(a):
    def sort(lo, hi):
        if lo >= hi:
            return
        pivot, i = a[hi], lo
        for j in range(lo, hi):
            if a[j] < pivot:
                a[i], a[j] = a[j], a[i]
                i += 1
        a[i], a[hi] = a[hi], a[i]
        sort(lo, i - 1)
        sort(i + 1, hi)
    sort(0, len(a) - 1)
    return a`,
 heap:`def heap_sort(a):
    def sift(root, size):
        while root * 2 + 1 < size:
            child = root * 2 + 1
            if child + 1 < size and a[child + 1] > a[child]:
                child += 1
            if a[root] >= a[child]:
                break
            a[root], a[child] = a[child], a[root]
            root = child
    for root in range(len(a) // 2 - 1, -1, -1):
        sift(root, len(a))
    for end in range(len(a) - 1, 0, -1):
        a[0], a[end] = a[end], a[0]
        sift(0, end)
    return a`,
 recursion:`def factorial(n):
    # 前提：n 是非负整数。先检查基例！
    if n == 0:
        return 1
    child = factorial(n - 1)
    return n * child

print(factorial(4))  # 24`,
 stones:`def winning_moves(n, limit=3):
    win = [False] * (n + 1)
    for count in range(1, n + 1):
        win[count] = any(
            not win[count - take]
            for take in range(1, min(count, limit) + 1)
        )
    return [take for take in range(1, min(n, limit) + 1)
            if not win[n - take]]  # 空列表：没有必胜走法`,
 minimax:`# 叶子分数统一从 MAX 的角度看；内部节点是孩子列表。
def minimax(tree, maximizing=True):
    if isinstance(tree, int):
        return tree
    scores = [minimax(child, not maximizing) for child in tree]
    return max(scores) if maximizing else min(scores)

print(minimax([[3, 8], [4, 1]]))  # max(3, 1) = 3`
};
const entries=[
 ['insertion','插入排序','把新牌插进有序手牌',1,'左边已经有序。暂存下一张牌，把比它大的牌右移，再插进空位。','最好 O(n)，平均/最坏 O(n²)；额外空间 O(1)。相等时不右移，稳定。'],
 ['merge','归并排序','先分小队，再有序合并',2,'分到单个元素，再比较两支有序小队的队首，每次拿较小的一个。','时间 O(n log n)，辅助数组峰值 O(n)，递归栈 O(log n)。相等时先拿左边，稳定。'],
 ['quick','快速排序','围绕基准分左右',2,'本演示用末尾作基准。严格小于基准的送左边，基准就位后分别处理两侧。','平均 O(n log n)，最坏 O(n²)（如有序或全相等且总选末尾）。递归栈平均 O(log n)、最坏 O(n)，不稳定。'],
 ['heap','堆排序','大顶堆反复送出最大值',3,'数组也能表示二叉堆：编号 i 的孩子是 2i+1、2i+2。先建大顶堆，再取最大值、缩堆、向下修复。','建堆 O(n)，总时间 O(n log n)，额外空间 O(1)；不稳定。堆只保证父大于等于孩子，不是完全有序。'],
 ['recursion','递归与返回','先到底，再带答案回来',2,'factorial(n) 等待 factorial(n-1) 的答案。n == 0 是刹车；返回时逐层相乘。0! = 1。','非负整数 n：时间 O(n)，调用栈 O(n)。没有基例或问题不变小会无限递归；大 n 可能超过 Python 递归深度。'],
 ['preorder','二叉树 · 前序','根 → 左 → 右',2,'前序先访问根，再完整走左子树，最后走右子树。箭头左、右不能互换。','每个节点访问一次，时间 O(n)，递归栈 O(h)，h 为树高；不要求是二叉搜索树。'],
 ['inorder','二叉树 · 中序','左 → 根 → 右',2,'中序先完整走左子树，再访问根，最后走右子树。只有二叉搜索树的中序才保证有序。','时间 O(n)，递归栈 O(h)，h 为树高；这里是普通二叉树，不按字母大小决定方向。'],
 ['postorder','二叉树 · 后序','左 → 右 → 根',2,'左右子树都完成后，才访问根。像先收好两个小房间，最后收大厅。','时间 O(n)，递归栈 O(h)，h 为树高。适合先处理孩子、再汇总父节点的任务。'],
 ['stones','取石子博弈','把必败态留给对手',2,'两人轮流取石子，每次取 1 到上限颗，拿到最后一颗的人赢。必胜态有至少一条路通向必败态；必败态所有路都通向必胜态。','动态规划时间 O(n × k)，空间 O(n)，k 为每次可取上限。胜负判断假设双方都最优；必败不等于随便玩也一定输。'],
 ['minimax','极小极大博弈树','你取大，对手取小',3,'叶子都是 MAX 的分数。MIN 不会帮 MAX 选高分：从叶子往上交替取最小、最大，直到根。','完整搜索时间 O(b^d)，递归栈 O(d)，b 为分支数，d 为深度；本演示保存整棵树用于回放，没有 α-β 剪枝。']
];
export const advancedTopics=entries.map(([id,title,subtitle,stars,idea,cost])=>({id,title,subtitle,stars,idea,cost,python:codes[id]??`# 节点用字典表示：value、left、right；空孩子用 None。
def traverse(node):
    output = []
    def walk(current):
        if current is None:
            return
${id==='preorder'?'        output.append(current["value"])\n':''}        walk(current.get("left"))
${id==='inorder'?'        output.append(current["value"])\n':''}        walk(current.get("right"))
${id==='postorder'?'        output.append(current["value"])\n':''}    walk(node)
    return output`}));
export function makeAdvancedLesson(id,seed){
 const topic=advancedTopics.find(t=>t.id===id);if(!topic)return null;
 let state=seed>>>0;const rand=n=>{state=(Math.imul(state,1664525)+1013904223)>>>0;return (state>>>8)%n;};
 const option=v=>({label:String(v),value:v}),numeric=(answer,others)=>[...new Set([answer,...others])].slice(0,4).sort((a,b)=>a-b).map(option);
 let data,frames,exercise;
 if(['insertion','merge','quick','heap'].includes(id)){
  data=Array.from({length:6},()=>rand(40)+5);frames=sortTrace(id,data);
  if(id==='insertion'){
   const answer=JSON.stringify([...data.slice(0,2)].sort((a,b)=>a-b).concat(data.slice(2)));
   const variants=[answer,JSON.stringify([...data].sort((a,b)=>a-b)),JSON.stringify([...data].reverse()),JSON.stringify(data.slice(1).concat(data[0])),JSON.stringify(data.map(x=>x+1))];
   exercise={answer,meta:{input:data},prompt:`插入排序从 ${data.join('、')} 开始，只插好第 2 个元素（编号 1），数组变成什么？`,options:[...new Set(variants)].slice(0,4).map(v=>({label:JSON.parse(v).join('、'),value:v})),hint:'只把第二张牌插进左边已有的第一张牌；后面的牌还没动。',explanation:'前两张排好序，编号 2 以后的数保持原位。'};
  }else if(id==='merge'){
   const left=data.slice(0,3).sort((a,b)=>a-b),right=data.slice(3).sort((a,b)=>a-b),answer=JSON.stringify([...data].sort((a,b)=>a-b));
   exercise={answer,meta:{left,right},prompt:`合并有序小队 [${left}] 和 [${right}]，完整输出是哪一排？`,options:[...new Set([answer,JSON.stringify([...left,...right]),JSON.stringify([...data].sort((a,b)=>b-a)),JSON.stringify([...right,...left]),JSON.stringify(data.map(x=>x+1))])].slice(0,4).map(v=>({label:JSON.parse(v).join('、'),value:v})),hint:'每次只比较两队的队首，较小的先出来；一队空了，再接上另一队。',explanation:'合并的结果整体有序，数量和所有数值都不改变。'};
  }else if(id==='quick'){
   const pivot=data.at(-1),answer=data.filter(x=>x<pivot).length;
   exercise={answer,meta:{input:data,pivot},prompt:`${data.join('、')}，末尾 ${pivot} 是基准。按“小于基准放左边”的规则，第一轮分区后基准的编号是多少？`,options:Array.from({length:data.length},(_,i)=>option(i)),hint:'先数出严格小于基准的数；等于基准的数不放进左区。',explanation:`有 ${answer} 个数严格小于 ${pivot}，它们占前 ${answer} 格，所以基准编号为 ${answer}。`};
  }else{
   const answer=Math.max(...data);exercise={answer,meta:{input:data},prompt:`${data.join('、')} 建成大顶堆，第一次送到数组最右边的数是多少？`,options:[...new Set([answer,...data,answer+1,answer+2])].slice(0,4).map(option),hint:'大顶堆的根比每个孩子都不小，堆顶就是整堆最大值。',explanation:`第一次送出最大值 ${answer}，之后缩小堆并修复。`};
  }
 }else if(id==='recursion'){
  const n=2+rand(5);data=[n];frames=recursionTrace(n);let answer=1;for(let i=2;i<=n;i++)answer*=i;
  exercise={answer,meta:{n},prompt:`factorial(0) 返回 1；factorial(n) 返回 n × factorial(n-1)。factorial(${n}) 最终返回什么？`,options:numeric(answer,[n,answer+1,answer+n,0]),hint:'先写到 factorial(0) = 1，再沿调用栈往回乘，不是把各层相加。',explanation:`从基例 1 逐层乘回 ${n}，得到 ${answer}。`};
 }else if(['preorder','inorder','postorder'].includes(id)){
  const letters=['A','B','C','D','E','F'];for(let i=letters.length-1;i>0;i--){const j=rand(i+1);[letters[i],letters[j]]=[letters[j],letters[i]];}
  const [a,b,c,d,e,f]=letters,tree={value:a,left:{value:b,left:{value:d},right:{value:e}},right:{value:c,right:{value:f}}};data=letters;frames=treeTrace(tree,id);
  const answer=frames.at(-1).visited.join(' → '),other=['preorder','inorder','postorder'].filter(x=>x!==id).map(x=>treeTrace(tree,x).at(-1).visited.join(' → '));
  exercise={answer,meta:{tree},prompt:`按图中左右关系，从根 ${a} 开始做${topic.title.split(' · ')[1]}遍历，完整访问顺序是什么？（节点名字不决定方向）`,options:[answer,...other,[...frames.at(-1).visited].reverse().join(' → ')].map(option),hint:`每个子树都重复“${topic.subtitle}”；进入节点不一定立即输出。`,explanation:`遵守 ${topic.subtitle}，结果为 ${answer}。`};
 }else if(id==='stones'){
  const n=5+rand(8),limit=2+rand(2);data=Array.from({length:n},(_,i)=>i+1);frames=stoneTrace(n,limit);const answer=frames.at(-1).moves[0]??0;
  exercise={answer,meta:{n,limit},prompt:`共有 ${n} 颗石子，每次取 1～${limit} 颗，拿到最后一颗获胜。双方最优，你应先取几颗？若不止一种，选最小的必胜取法。`,options:[{label:'没有必胜走法',value:0},...Array.from({length:limit},(_,i)=>({label:`取 ${i+1} 颗`,value:i+1}))],hint:'0 颗是必败态。想办法把必败态留给对手；如果所有走法都送出必胜态，就没有必胜走法。',explanation:answer?`取 ${answer} 颗，把 ${n-answer} 颗的必败态留给对手。`:'所有合法走法都让对手进入必胜态；双方最优时先手必败。'};
 }else{
  const leaves=Array.from({length:2},()=>Array.from({length:2},()=>rand(19)-5));data=leaves.flat();frames=minimaxTrace(leaves);const answer=frames.at(-1).result;
  exercise={answer,meta:{leaves},prompt:`根是 MAX，下一层两个 MIN 的叶子分别是 [${leaves[0]}] 和 [${leaves[1]}]。双方最优时根回传几分？`,options:numeric(answer,[...data].sort((a,b)=>b-a).concat([answer+1,answer-1,answer+2])),hint:'先分别算两组的最小值（MIN 不会帮你拿高分），根再取这两个值的最大值。',explanation:`max(min(${leaves[0]}), min(${leaves[1]})) = ${answer}。`};
 }
 // Shuffle options deterministically: the correct choice must not always occupy slot 0.
 for(let i=exercise.options.length-1;i>0;i--){const j=rand(i+1);[exercise.options[i],exercise.options[j]]=[exercise.options[j],exercise.options[i]];}
 return {...topic,data,frames,exercise};
}
