# 🎮 TypeSafe Tetris: Official Guideline + Native TypeSafe AI Live Dashboard

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python" alt="Python 3.10+" />
  <img src="https://img.shields.io/badge/FastAPI-0.95%2B-009688?style=for-the-badge&logo=fastapi" alt="FastAPI" />
  <img src="https://img.shields.io/badge/TypeSafe-SDK_0.6.0-6C5CE7?style=for-the-badge" alt="TypeSafe SDK" />
  <img src="https://img.shields.io/badge/Render-Retina_2x_0%25_Blur-00D2D3?style=for-the-badge" alt="Retina 2x" />
  <img src="https://img.shields.io/badge/Tests-14_Passed-2ecc71?style=for-the-badge" alt="Tests Passed" />
  <img src="https://img.shields.io/badge/License-MIT-F39C12?style=for-the-badge" alt="MIT License" />
</p>

<p align="center">
  <b>俄罗斯方块官方 Tetris Guideline 规范 + 原生 TypeSafe AI 全链路透明决策现代 Web 实时驾驶舱</b><br>
  <i>100% 纯净解耦 Headless 核心引擎 · 60FPS 双向全量状态广播 · 视网膜 Retina 2x 矢量点对点绘制 · 绝对 0% 模糊</i>
</p>

---

## 🌟 核心亮点 (Key Highlights)

- 🧩 **100% 官方 Tetris Guideline 规范**：
  - 严谨实现 **SRS (Super Rotation System)** 顺/逆时针四态踢墙旋转系统；
  - 官方 **7-Bag 随机发生器**（绝对杜绝方块干旱或长条缺位）；
  - 标准 **Lock Delay (0.5s / 15次重置保护)** 与 T-Spin / Back-to-Back / 连续消行 (Combo) 计分机制。
- 🧠 **原生 TypeSafe AI 决策透明化 (三原语深度融合)**：
  - **Choice (排他选择)**：候选物理落点竞争矩阵 $P(c_0 \sim c_4)$，实时高亮胜出方案，并在棋盘投影 AI Target Ghost；
  - **Choice (战术模式)**：四种通关意图（防守避险 / 填平地表 / 蓄积四消 / 贪心进攻）概率竞争；
  - **Noul (条件门控真值)**：双阈值危机门控（濒危概率、暂存换块概率），直观展示 AI 的风险敏感度；
  - **Score (健康度评分)**：棋盘 5 级离散健康直方柱状图与加权综合星级。
- 🖥️ **现代深色玻璃拟态 Web 驾驶舱**：
  - 基于 **FastAPI + WebSocket** 实现 60FPS 双向高频全量状态流；
  - **Retina 2x Canvas 点对点矢量绘制**：告别传统桌面渲染在 4K/5K 及高分屏下的模糊、抗锯齿发虚问题，达到 100% 视网膜超清锐利；
  - **Assembled State Inspector (输入端透明)**：实时格式化展开给 AI 模型的原始输入字典，模型看什么、怎么想一览无余！
- ⚡ **0-Config 极速体验，无 Key 也可秒跑**：
  - 内置高质量本地物理启发式对齐引擎，即使未配置任何 API Key，也能完整体验 AI 自动驾驶与三原语全概率推导；
  - 若配置了 `TYPESAFE_API_KEY`，则无缝连接云端 LLM 进行自然语言与语义推理。

---

## 📸 四栏式全景视窗 (Dashboard Architecture)

```
┌─────────────────┬─────────────────┬─────────────────────────┬─────────────────────────┐
│  栏 1: 战况与背包 │  栏 2: 核心对战  │ 栏 3: TypeSafe 输入端视窗 │ 栏 4: TypeSafe 输出端大屏│
├─────────────────┼─────────────────┼─────────────────────────┼─────────────────────────┤
│ • 暂存区 (HOLD) │ • 10x20 规范棋盘 │ • 用户自然语言意图       │ • 候选落点胜选概率条形图│
│ • 预览队列(NEXT)│ • 2x 视网膜矢量  │   (User Question)       │ • 4 种宏观战术概率分布   │
│ • 得分/等级/行数 │ • 活动块/下落幽灵│ • Assembled State 字典  │ • Noul 危机/换块门控标尺│
│ • 操作快捷键指南 │ • AI 落点虚框投影│ • 原生 Prompt 指令清单   │ • Score 5级健康度直方图 │
└─────────────────┴─────────────────┴─────────────────────────┴─────────────────────────┘
```

---

## 🚀 30 秒极速上手 (Quick Start)

### 选项 A：使用 `uv` 运行 (推荐 · 极速包管理器)

```bash
# 1. 克隆本仓库
git clone https://github.com/your-username/typesafe-tetris.git
cd typesafe-tetris

# 2. 安装依赖并启动 (会自动为您在默认浏览器中打开驾驶舱)
uv run python main.py
```

### 选项 B：使用传统 `pip` 运行

```bash
# 1. 创建并激活虚拟环境 (可选但推荐)
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动驾驶舱
python main.py
```

启动后将自动在系统默认浏览器中打开驾驶舱页面。若未自动打开，请直接访问：**`http://127.0.0.1:8000`**。


---

## ⌨️ 控制快捷键与双向交互 (Controls)

无论是在页面顶栏点击按钮，还是使用键盘按键，均支持毫秒级低延迟操控：

| 按键 | 功能 | 说明 |
| :---: | :--- | :--- |
| **`A`** | **切换 AI 自动驾驶托管** | **随时一键开启/接管 AI 自动通关**（手动操控时 AI 看板也会实时运算预测） |
| **`Q`** | **轮转切换策略问题 (Question)** | 实时切换通关策略意图（“稳扎稳打”、“全力大招”、“消行冲刺”、“绝境求生”） |
| **`SPACE` (空格)** | **瞬间硬降 (Hard Drop)** | 瞬间直落到底部并立即锁定 |
| `←` / `→` | 横向平移 | 手动左右移动方块 |
| `↓` | 软降 (Soft Drop) | 加速平滑下落并增加得分 |
| `↑` / `Z` | 顺时针 / 逆时针旋转 | 触发官方 SRS 踢墙系统 |
| `C` | 暂存 (Hold) | 暂存当前方块（每个落块周期限 1 次） |
| `P` / `ESC` | 暂停 / 继续 | 唤起/关闭磨砂玻璃暂停菜单 |
| `R` | 重新开始游戏 | 清空棋盘重新开局 |

---

## 📂 仓库目录规范 (Repository Structure)

```text
typesafe-tetris/
├── .env.example              # 环境变量配置模板 (TYPESAFE_API_KEY 等)
├── .gitignore                # 忽略环境配置与测试构建缓存
├── LICENSE                   # MIT 开源许可证
├── pyproject.toml            # 现代构建标准 (支持 pip/uv 安装)
├── requirements.txt          # 核心生产依赖 (fastapi, uvicorn, websockets, typesafe-sdk)
├── requirements-dev.txt      # 开发者测试依赖 (pytest, ruff)
├── README.md                 # 国际化开源详尽使用说明书
│
├── main.py                   # 根目录主入口: 支持 python main.py 一键启动
├── web_launcher.py           # Web 专用启动器 (端口配置与系统浏览器自动唤起)
├── constants.py              # 官方 Tetris Guideline 标准常量 (SRS 表、配色、矩阵)
├── models.py                 # 核心数据模型 (Pydantic / Dataclass 强类型契约)
├── engine.py                 # 纯净 Headless 核心引擎 (SRS 踢墙、Lock Delay、碰撞)
├── randomizer.py             # 官方 7-Bag 随机数发生器
│
├── ai/                       # TypeSafe 智能决策核心大脑
│   ├── __init__.py
│   ├── evaluator.py          # 几何指标计算 (空洞、高度、凹凸度) 与候选落点生成
│   ├── planner.py            # 动作路径反解器 (将落点转换为精准操作按键序列)
│   └── typesafe_agent.py     # 原生 TypeSafe 三原语 (Choice, Noul, Score) 智能代理
│
├── web/                      # 现代 Web 全高清视网膜驾驶舱
│   ├── __init__.py
│   ├── server.py             # FastAPI + WebSocket 60FPS 双向全量状态广播
│   └── static/               # 现代化深色拟态前端工程 (深空灰背景、青金微光)
│       ├── index.html        # 四栏式仪表盘骨架
│       ├── style.css         # Retina 2x 高清流体样式与动效
│       └── app.js            # Canvas 矢量绘制、状态绑定与按键监听
│
└── tests/                    # 自动化测试套件 (14 项全绿)
    ├── __init__.py
    ├── test_engine.py        # 引擎物理、消行、随机序列逻辑测试
    ├── test_typesafe_agent.py# 原生 TypeSafe 接口契约与三原语测试
    └── test_integration.py   # Web 端到端状态流集成测试
```

---

## 🧪 自动化测试验证 (Testing)

本项目拥有完备的自动化测试套件，涵盖物理碰撞、SRS 踢墙、TypeSafe 原语契约与 Web 端到端状态序列化：

```bash
# 运行全部 14 项自动化测试
PYTHONPATH=. uv run pytest tests/  # 或: pytest tests/
```

测试执行结果：
```text
============================= test session starts ==============================
collected 14 items

tetris/tests/test_engine.py ........                                     [ 57%]
tetris/tests/test_integration.py ..                                      [ 71%]
tetris/tests/test_typesafe_agent.py ....                                 [100%]

============================== 14 passed in 10s ================================
```

---

## 💡 进阶：配置云端 TypeSafe API Key

如果您拥有官方 TypeSafe API Key 并希望启用云端大模型推理：
1. 复制 `.env.example` 为 `.env`：
   ```bash
   cp .env.example .env
   ```
2. 在 `.env` 中填入您的 Key：
   ```ini
   TYPESAFE_API_KEY=your_actual_key_here
   ```
3. 重启程序即可！

---

## 📄 开源许可证 (License)

本项目遵循 [MIT License](LICENSE) 开源协议。欢迎学习交流、提交 PR 与 Star 支持！
