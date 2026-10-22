export const topics=[
 {id:'array',title:'数组',subtitle:'按门牌找矿石',idea:'数组像一排带门牌的储物格。Python 列表的第一个位置编号是 0。',python:'stones = [12, 25, 38]\nprint(stones[1])  # 第二格：25',cost:'知道位置，就直接找到那一格；不必从头检查。'},
 {id:'stack',title:'栈',subtitle:'最后放，最先拿',idea:'像一叠盘子，只能从顶端放入或取走。最后放进去的，最先出来。',python:'bag = []\nbag.append("铜矿")\nbag.append("银矿")\nprint(bag.pop())  # 银矿',cost:'入栈、出栈只操作顶端，不用移动其他盘子。'},
 {id:'queue',title:'队列',subtitle:'先到先出发',idea:'像排队坐缆车：从队尾加入，从队首离开，不插队。',python:'from collections import deque\nline = deque(["小鹿", "小熊"])\nline.append("小兔")\nprint(line.popleft())  # 小鹿',cost:'双端队列 deque 可以高效地从队首取出；列表 pop(0) 需要移动后面的元素。'},
 {id:'binary',title:'二分查找',subtitle:'每次排除一半',idea:'先排好序，再比较中间的一格。目标更大就去右半边，更小就去左半边。',python:'lo, hi = 0, len(stones) - 1\nmid = (lo + hi) // 2\n# 比较 stones[mid] 和目标\n# 更小：lo = mid + 1；更大：hi = mid - 1',cost:'前提：已经有序。每次大约剩一半；无序数据不能照搬。'},
 {id:'bubble',title:'冒泡排序',subtitle:'相邻比较，把大数送右边',idea:'从左往右比较相邻两个数。左边大就交换；一轮后，最大的数到最右边。',python:'for end in range(len(stones)-1, 0, -1):\n    for i in range(end):\n        if stones[i] > stones[i+1]:\n            stones[i], stones[i+1] = stones[i+1], stones[i]',cost:'简单但比较次数多。这里用来理解排序，不是大数据最快的方法。'},
 {id:'bfs',title:'广度优先搜索',subtitle:'一圈一圈探索',idea:'用队列存待探索的地点。先看近邻，再看更远一层；入队就标记，避免重复。',python:'queue = deque(["A"])\nseen = {"A"}\nwhile queue:\n    place = queue.popleft()\n    for neighbor in graph[place]:\n        if neighbor not in seen:\n            seen.add(neighbor)\n            queue.append(neighbor)',cost:'在每条边长度相同的图里，可以找最少步数路线；不是任意带权图的最短路算法。'}
];
const graph={A:['B','C'],B:['A','D','E'],C:['A','F'],D:['B'],E:['B'],F:['C']};
export function judge(exercise,value){return exercise.answer===value;}
export function makeLesson(id,seed=1){
 const topic=topics.find(t=>t.id===id);if(!topic)throw Error('Unknown topic');
 let s=seed>>>0;const rand=n=>{s=(Math.imul(s,1664525)+1013904223)>>>0;return s%n;};
 let data=Array.from({length:5},(_,i)=>10+i*10+rand(8)),frames=[],exercise,target,order=[];
 const frame=(items,caption,active=[],extra={})=>frames.push({items:[...items],caption,active:[...active],...extra});
 const option=v=>({label:String(v),value:v});
 if(id==='array'){
  const index=1+rand(3);frame(data,'一排矿石格，下面的编号从 0 开始。');frame(data,`想取编号 ${index} 的矿石，不是第 ${index} 格。`,[index]);frame(data,`直接读 data[${index}]，得到 ${data[index]}。`,[index]);
  exercise={index,answer:data[index],prompt:`仓库里依次是 ${data.join('、')}。data[${index}] 的值是多少？`,options:data.map(option),hint:'把第一个编号写成 0，再往右数。',explanation:`编号 ${index} 是第 ${index+1} 格，值是 ${data[index]}。`};
 }else if(id==='stack'||id==='queue'){
  data=['铜矿','银矿','水晶','月岩'].slice(0,3+rand(2));let items=[];
  frame(items,id==='stack'?'右端是栈顶，从这里放入和取出。':'左端是队首，右端是队尾。');
  for(const item of data){items.push(item);frame(items,`${item}${id==='stack'?'入栈，成为新栈顶':'从队尾加入'}。`,[items.length-1]);}
  const removed=id==='stack'?items.pop():items.shift();frame(items,`${removed}${id==='stack'?'出栈：最后来的先离开':'离队：最早来的先出发'}。`);
  exercise={answer:id==='stack'?data.at(-1):data[0],prompt:`依次放入：${data.join(' → ')}。现在${id==='stack'?'出栈 pop()':'从队首取出 popleft()'}，先拿到谁？`,options:data.map(option),hint:id==='stack'?'想象一叠盘子：最上面是哪一个？':'想象排队：谁最先到达？',explanation:`${id==='stack'?'栈后进先出':'队列先进先出'}，所以拿到 ${id==='stack'?data.at(-1):data[0]}。`};
 }else if(id==='binary'){
  data=Array.from({length:9},(_,i)=>i*10+rand(5));target=data[rand(data.length)];let lo=0,hi=data.length-1;
  frame(data,`已经从小到大排列。目标：${target}。`,[],{lo,hi});
  while(lo<=hi){const mid=Math.floor((lo+hi)/2);frame(data,`范围 [${lo}, ${hi}]，中间编号 ${mid}，值 ${data[mid]}。`,[mid],{lo,hi});if(data[mid]===target){frame(data,`找到了！编号 ${mid} 的值就是 ${target}。`,[mid],{lo,hi});break;}if(data[mid]<target){lo=mid+1;frame(data,'中间值比目标小，排除它和左边。',[],{lo,hi});}else{hi=mid-1;frame(data,'中间值比目标大，排除它和右边。',[],{lo,hi});}}
  const qlo=rand(3),qhi=6+rand(3);exercise={lo:qlo,hi:qhi,answer:Math.floor((qlo+qhi)/2),prompt:`有序数组的剩余范围是编号 [${qlo}, ${qhi}]。用 (lo + hi) // 2，下一步应该检查哪个编号？`,options:Array.from({length:qhi-qlo+1},(_,i)=>({label:`编号 ${qlo+i}`,value:qlo+i})),hint:'先把两个端点编号相加，再除以 2，只取整数部分。',explanation:`(${qlo} + ${qhi}) // 2 = ${Math.floor((qlo+qhi)/2)}。注意问的是编号，不是格子里的值。`};
 }else if(id==='bubble'){
  data=[30+rand(9),10+rand(9),50+rand(9),20+rand(9),40+rand(9)];let items=[...data];frame(items,'目标：从小到大排列。每次只比较相邻两格。');
  for(let end=items.length-1;end>0;end--){for(let i=0;i<end;i++){frame(items,`比较编号 ${i} 和 ${i+1}：${items[i]} 与 ${items[i+1]}。`,[i,i+1]);if(items[i]>items[i+1]){[items[i],items[i+1]]=[items[i+1],items[i]];frame(items,'左边更大，交换这两格。',[i,i+1]);}else frame(items,'顺序正确，不交换。',[i,i+1]);}frame(items,`这一轮完成，编号 ${end} 已就位。`,[end]);}frame(items,'排序完成！越往右，数越大。');
  exercise={answer:0,prompt:`起始数据 ${data.join('、')}。第一轮从左开始，第一对必须交换的是哪一对？`,options:data.slice(0,-1).map((v,i)=>({label:`${v} ↔ ${data[i+1]}（编号 ${i}, ${i+1}）`,value:i})),hint:'只检查相邻两格；从最左边开始，左边大于右边才交换。',explanation:`第一对 ${data[0]} > ${data[1]}，所以先交换编号 0 和 1。`};
 }else{
  data=['A','B','C','D','E','F'];let q=['A'],seen=new Set(['A']);frame(data,'从 A 出发，A 入队。队列：[A]。',[],{queue:[...q],visited:[],graph});
  while(q.length){const v=q.shift();order.push(v);for(const n of graph[v])if(!seen.has(n)){seen.add(n);q.push(n);}frame(data,`探索 ${v}，把还没发现的邻居入队。队列：[${q.join(', ')}]。`,[data.indexOf(v)],{queue:[...q],visited:[...order],graph});}
  exercise={answer:'C',prompt:'从 A 出发，按 B、C 的顺序入队。取出 B 后，把 D、E 加到队尾。现在队列是 [C, D, E]，下一站该探索谁？',options:['B','C','D','E'].map(option),hint:'不要被新发现的地点带跑：从队首取出，而不是队尾。',explanation:'C 已经在队首等着。D、E 是后加入的，不能插队。'};
 }
 return {...topic,data,frames,exercise,target,order};
}
