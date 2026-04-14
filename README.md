# ai_study AI工程化学习

个人 **AI 应用 / Agent / Python 后端工程化** 学习笔记与 Demo 仓库。内容按模块分目录存放，与根目录的进度文档配合使用。

在线仓库：<https://github.com/chl-5g/ai_study>

## 目录结构

| 目录 | 内容 |
|------|------|
| [A-Python基础](A-Python基础/) | **A1** Pythonic 与标准库；**A2** Python 网络与 HTTP 基础（`A2-Python网络与HTTP基础/`）；**A3** FastAPI 深度（`A3-FastAPI深度/`）；**A4** 并发与异步（`A4-并发与异步/`）；**A5** 测试与 CI（`A5-测试与CI/`，`demos/` 内建议建 `.venv` 再 `pytest`）。各章均为 `理论讲解.md` + `demos/`（A2 体例与 A1 对齐：分节小结与对照实验） |
| [B-后端工程化](B-后端工程化/) | **B1** 数据库深度；**B5–B9** Docker 与部署、消息队列与任务队列、SSE 与 WebSocket、微服务与系统设计、设计模式（原 B2–B4 已并入 **A-Python基础** 的 A3–A5）。各章 `理论讲解.md` + 可运行 `demos/`（以各章 `demos/README.md` 为准）；**B9** 含 **GoF 23 整合速览（§2）** |
| [C-AI-Agent全栈](C-AI-Agent全栈/) | **索引**见 [C-AI-Agent全栈/README.md](C-AI-Agent全栈/README.md)。C1–C8 均有 `理论讲解.md` 与可运行 `demos/`（C4 见该章 `demos/requirements.txt`） |
| [D-求职面试](D-求职面试/) | [Python + AI Agent 应用/架构 — 面试题与参考答案](D-求职面试/Python与AI-Agent应用开发-面试题.md)（无 demo）；索引见 [D-求职面试/README.md](D-求职面试/README.md) |
| [Resume](Resume/) | 简历 LaTeX 工具链说明与构建脚本（见该目录 `README.md`） |

根目录其他文件：

- [学习流程-5步循环.md](学习流程-5步循环.md)：每章节的 **理论 → Demo → 实操 → 更新进度** 固定节奏
- [学习进度.md](学习进度.md)：章节状态与周复盘记录
- `学习计划（补充完整版）.docx`：补充版学习计划（若已纳入版本库则与上述文档一致迭代）

## 章节内约定

- 理论稿：各章目录下的 `理论讲解.md`（若已生成）
- 示例代码：各章下的 `demos/`，命名如 `01_xxx.py`、`02_xxx.py`
- 模块 **C**（AI Agent 全栈）：各章理论文末有 **与 `demos/` 脚本对照** 表，与该章 `demos/README.md` 所列文件一致；索引与依赖说明见 [C-AI-Agent全栈/README.md](C-AI-Agent全栈/README.md)
- 空目录在 Git 中默认不可见，尚未填充的 `demos/` 等目录用 **`.gitkeep`** 占位；放入真实文件后可自行删掉对应 `.gitkeep`
- 运行 Demo 需本机安装对应版本的 **Python 3**；部分章节会依赖额外包或本地服务，以各章 `理论讲解.md`、`demos/README.md` 或脚本头部注释为准

## 隐私与 `.gitignore`

以下不入库，仅保留在本地（见 [.gitignore](.gitignore)）：

- `Resume/` 下的 `.jpg`、`.pdf`、`.docx`、`.tex`（避免简历成品与源稿进入远程）
- `**/.ipynb_checkpoints/`
- `.DS_Store`

如需在公开仓库中完全去掉某类文件的历史记录，需单独做历史清理（例如 `git filter-repo`），本 README 不展开。

## 贡献与许可

私人学习用途；内容不构成课程或商业承诺。若你 fork 自用，请自行注意敏感信息勿提交。
