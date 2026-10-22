# Lucas Lab · 动手，想明白

独立中文学习站：**https://shawnq-msft.github.io/lucas-lab/**

- `practice/`：已有星矿探险 Python 游戏模拟，六关、首次/复测两套题组、分级提示、行动回放、本机保存、JSON 导出。自制模拟，非官方赛事平台。
- `algorithms/`：数组、栈、队列、二分查找、冒泡排序、广度优先搜索。单步/自动演示、预测练习、正误反馈、提示、学习记录与导出。
- `tokamak/`：沿用已有中文交互剖面，六步导览、磁场切换、零件解释。教学示意，不是工程设计或真实运行模型。

建议电脑 Edge/Chrome。首次打开 Python 页面须下载本站约 14 MB 的 Pyodide 0.27.7 运行资源，不依赖第三方 CDN；不是离线应用。学生代码在浏览器 Worker 执行，无服务器提交。没有账号和云同步；localStorage 按浏览器、来源隔离。旧 Beijing Vibe Trip 记录不会自动迁移；请在旧页导出备份。

公开链接和公开源码，`noindex` 不提供访问控制。不要填入姓名、学校、账号或密码。首次摸底应关闭 AI/补全；提示后通过不等于独立掌握。

## 构建与验证

```sh
python3 build.py
python3 -m unittest discover -s tests -p test_build.py -v
python3 -m unittest discover -s sources/practice -p test_engine.py -v
node --test tests/model.test.mjs
# 另一个终端：python3 -m http.server 8786 --bind 127.0.0.1
# Python 环境需安装 playwright，且 playwright install chromium
python3 tests/browser.py
python3 tests/practice_browser.py
# 线上回归
LAB_URL=https://shawnq-msft.github.io/lucas-lab/ python3 tests/browser.py
LAB_URL=https://shawnq-msft.github.io/lucas-lab/ python3 tests/practice_browser.py
```

截图、浏览器报告、模拟测试导出的记录均写入忽略的 `verification/`，不发布成儿童的真实学习记录。`sources/practice/test_engine.py` 含家长参考解答，学生页面不展示。浏览器自动化使用独立 Chromium 测试上下文，不读取私人登录/学习记录。

`main` 推送后 GitHub Actions 构建、执行单元测试，仅将三模块及公共资源作为 Pages artifact 上传；测试、源快照不在站点目录内。`build.py` 完全使用仓库内快照，原有两个站点不被修改。

## 来源与第三方

- Python 练习快照来自 `projects/maodou-python-quest`；Tokamak 来自 `voice-anatomy/figures/tokamak/tokamak-light.html`，原演示的 ITER 等科学来源保留在页面底部。
- 新增算法工作台为 Lucas Lab 自编。
- `practice/runtime/` 为 [Pyodide 0.27.7](https://github.com/pyodide/pyodide/releases/tag/0.27.7) 官方发布资源镜像（CDN: https://cdn.jsdelivr.net/pyodide/v0.27.7/full/）。许可证见 `THIRD_PARTY.md` 与同目录 LICENSE。
