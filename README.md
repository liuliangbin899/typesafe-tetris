# 🎮 TypeSafe Tetris: 原生 TypeSafe AI 决策范式与实时推演架构

<p align="center">
  <img src="https://img.shields.io/badge/Architecture-TypeSafe_System_One-6C5CE7?style=for-the-badge&logo=ai" alt="TypeSafe Architecture" />
  <img src="https://img.shields.io/badge/SDK-typesafe--sdk_0.6.0-0984e3?style=for-the-badge" alt="TypeSafe SDK" />
  <img src="https://img.shields.io/badge/Latency-12ms_Realtime-00D2D3?style=for-the-badge" alt="Latency" />
  <img src="https://img.shields.io/badge/Protocol-Tetris_Guideline_SRS-2ecc71?style=for-the-badge" alt="Guideline" />
  <img src="https://img.shields.io/badge/Tests-14_Passed-brightgreen?style=for-the-badge" alt="Tests" />
  <img src="https://img.shields.io/badge/License-MIT-F39C12?style=for-the-badge" alt="MIT License" />
</p>

<p align="center">
  <b>面向高频实时环境的 TypeSafe 原生三原语 (Noul / Choice / Score) 智能决策系统与全链路透明化 Web 驾驶舱</b><br>
  <i>摆脱传统 LLM 慢速自回归 Token 生成与幻觉崩溃 · 毫秒级输出确定性全量概率分布 · 官方 SRS 踢墙与 7-Bag 物理仿真</i>
</p>

---

## 1. 为什么传统 LLM 无法胜任实时游戏决策？

在面对俄罗斯方块、竞技游戏等高吞吐、高实时性（60 FPS）的动态决策场景时，直接调用通用大语言模型（如 GPT-4、Claude 等自由文本生成模型）存在致命的技术瓶颈：

| 维度 | 传统 LLM (Token-by-Token) | TypeSafe AI (System One 原语) |
| :--- | :--- | :--- |
| **推理延迟 (Latency)** | 500ms ~ 3000ms（逐词自回归生成），严重脱节于物理时序 | **8ms ~ 20ms**（System One 直接输出概率张量），实时跟手 |
| **输出格式契约** | 自由文本或 JSON 字符串，极易发生语法残缺或 Parse Error | **100% 强类型数学契约**，由语言模型直接驱动的类型判定 |
| **概率可观测性** | 黑盒输出单个答案，无法获得全量候选落点的 Softmax 概率分布 | **原生暴露全量竞争矩阵与置信度**，具备数学确定性与可信度量化 |
| **决策可解释性** | 生成冗长的事后“幻觉辩护词”，难以与物理指标建立精确映射 | **三原语解耦**：门控真值、战术分类与多候选打分层层透明对应 |

**TypeSafe 的核心思想**：大模型不应该仅仅被当作聊天机器人，而应该被抽象为**“可编程的类型安全常识判断原语”（Programmable Common-Sense Primitives）**。

---

## 2. TypeSafe 三大核心原语在俄罗斯方块中的技术建模

本项目依托官方 `typesafe-sdk`，将复杂的俄罗斯方块落子决策严格形式化为 **三大原语的组合推理系统**：

```
                              ┌───────────────────────────────────┐
                              │  GameState (10x20 棋盘与方块背包)   │
                              └─────────────────┬─────────────────┘
                                                │
                                                ▼
                                    ┌───────────────────────┐
                                    │ 几何特征提取与拓扑展开  │
                                    │ (Holes/Height/Bump)   │
                                    └───────────┬───────────┘
                                                │
                 ┌──────────────────────────────┼──────────────────────────────┐
                 │                              │                              │
                 ▼                              ▼                              ▼
     ┌──────────────────────┐       ┌──────────────────────┐       ┌──────────────────────┐
     │ 1. Noul (条件门控)   │       │ 2. Choice (排他竞争)  │       │ 3. Score (健康评级)  │
     ├──────────────────────┤       ├──────────────────────┤       ├──────────────────────┤
     │ • 危机避险门控       │       │ • 宏观战术模式选择   │       │ • 5 级离散分布评级   │
     │   P(is_crisis_danger)│       │   P(tactic_mode)     │       │   P(health_grade)    │
     │ • 换块暂存门控       │       │ • 候选落点竞争矩阵   │       │ • 局面可持续发展打分 │
     │   P(should_hold)     │       │   P(cand_0 ~ cand_k) │       │   (1.0 ~ 5.0 级)     │
     └───────────┬──────────┘       └───────────┬──────────┘       └───────────┬──────────┘
                 │                              │                              │
                 └──────────────────────────────┼──────────────────────────────┘
                                                │
                                                ▼
                               ┌─────────────────────────────────┐
                               │     综合判决 (ActionPlanner)     │
                               │  反解按键序列: [旋, 移, 软降, 锁定] │
                               └────────────────┬────────────────┘
                                                │ 60 FPS WebSocket
                                                ▼
                               ┌─────────────────────────────────┐
                               │    全景 Web 矢量点对点视网膜驾驶舱  │
                               └─────────────────────────────────┘
```

### 原语 1: `Noul` (条件门控与概率真值)
`Noul` 是二元布尔门控原语，输出真值概率 $P \in [0.0, 1.0]$，用于快速判定是否触发硬性边界条件：
- **`is_crisis_danger` (危机避险门控)**：
  - **触发逻辑**：分析棋盘最大高度（如 $> 12$ 行）与当前空洞数，计算 $P(\text{Crisis})$。
  - **决策作用**：当 $P(\text{Crisis}) \ge 0.50$ 时，强制打断激进进攻策略，进入最高优先级的防守求生模式。
- **`should_hold` (暂存置换门控)**：
  - **触发逻辑**：对比当前块与背包暂存块（Hold Piece）在当前地表形态下的拟合度。
  - **决策作用**：若当前方块极难安全落脚且暂存块能显著化解险情，直接输出置换指令。

```python
# ai/typesafe_agent.py 中真实的 Noul 原语定义
"is_crisis_danger": Noul(
    instructions="分析 `board_metrics`，判断最大高度是否超过12行或存在多个空洞，局面是否已处于危险边缘必须放弃大招全力防守？"
),
"should_hold": Noul(
    instructions="对比 `inventory.current_piece` 与 `inventory.hold_piece`，当前方块在当前地形下是否难以落脚且暂存块明显更有利？"
)
```

### 原语 2: `Choice` (排他性多类别与候选竞争)
`Choice` 原语为有限互斥集合分配归一化的概率分布 $\sum P(x) = 1.0$，并输出选定项及整体置信度：
- **宏观战术分类 (`tactic_mode`)**：
  - `SURVIVAL`：极限削减堆叠高度，紧急避险；
  - `FLATTEN`：填平地表凹凸差，构造厚实平坦底盘；
  - `BUILD_TETRIS`：右侧预留第 10 列深井，积蓄 4 消大招爆发；
  - `SCORE_ATTACK`：积极追求消除行数与 Combo 连击。
- **候选落点竞争矩阵 (`selected_candidate_id`)**：
  - 物理引擎对当前方块的 4 种旋转姿态和 10 列平移进行碰撞扫描，预先过滤出 5~6 个代表性极佳的落点集合 $C = \{c_0, c_1, \dots, c_k\}$；
  - 将每个候选方案执行后的几何特征（`lines_cleared`, `resulting_holes`, `height_diff`, `bumpiness`）作为 criteria 载入；
  - `Choice` 给出竞争概率分布 $P(c_i)$，得分最高者胜出并实时在 Web 棋盘上投射**青色虚线目标幽灵框**。

```python
# ai/typesafe_agent.py 中微观候选落点竞争
"selected_candidate_id": Choice(
    instructions="根据确定的战术模式和 `user_question`，从 `candidates` 备选落点中挑选综合收益最高、最稳妥的最佳落点方案",
    criteria={cand.id: cand.to_summary() for cand in candidates}
)
```

### 原语 3: `Score` (离散态势评级直方图)
`Score` 原语用于对连续态势进行严谨的 1~5 级离散化健康度评估：
- 输出每个星级的置信概率 $P(\text{Grade}_k)$ 以及数学期望得分 $\mathbb{E}[\text{Health}] \in [1.0, 5.0]$；
- 赋予 AI 长程质量规划视角：即使当前某落点消除了 1 行，但如果导致未来健康度直方图断崖式下跌至 1 级，AI 也能通过加权感知进行规避。

```python
# ai/typesafe_agent.py 中健康态势 Score 原语
"board_health": Score(
    instructions="评估当前棋盘的整体健康度与可持续发展态势",
    criteria=[
        "1: 濒危崩盘，高度触顶，空洞严重阻塞通道",
        "2: 态势不良，凹凸差距大，需要多次复杂清坑",
        "3: 正常态势，高度适中，具备基本的消行空间",
        "4: 良好态势，表面平整无隐患，易于连续消行",
        "5: 黄金态势，底盘平实扎实，深井整齐，攻守兼备",
    ]
)
```

---

## 3. 全链路数据流与动作执行管线 (Data Pipeline)

从方块生成到最终落盘，整个生命周期由以下模块严格流水线化解耦驱动：

1. **`TetrisEngine` (Headless 核心物理引擎)**：
   - 100% 严谨遵循官方 **Tetris Guideline**；
   - 完整实现 **SRS (Super Rotation System)** 顺/逆时针四态踢墙算法与 5 点偏移表；
   - **7-Bag 发生器**保证方块分布公平性；支持 0.5s / 15 次重置的 **Lock Delay**。
2. **`BoardEvaluator` (拓扑特征提取器)**：
   - 基于网格位运算反解表面轮廓，提取聚合高度、最大高度、空洞数、凹凸度（Bumpiness）与深井特征；
   - 展开所有无碰撞合法姿态，生成带拓扑评分的候选子集。
3. **`TypeSafeTetrisAgent` (Jev 原语推理)**：
   - 构建强类型 `state_dict`，装载用户自然语言策略意图（`user_question`）；
   - 执行 `SystemOne` 极速推理，提取 $P(\text{Candidate})$、$P(\text{Tactic})$、$P(\text{Danger})$、$P(\text{Hold})$ 与健康星级；
   - 耗时精确记录并广播至前端（~12ms）。
4. **`ActionPlanner` (动作路径反解器)**：
   - 采用逆向路径追踪算法，将胜出落点 $(rot\_index, target\_x, target\_y)$ 转换为确定性的微操键位指令队列：
     $$\text{Action Queue} = [ \text{ROTATE\_CW}, \dots, \text{MOVE\_RIGHT}, \dots, \text{HARD\_DROP} ]$$
5. **`FastAPI WebSocket Server` (双向流广播)**：
   - 60 FPS 高频无锁向前端推送全量 State 帧；
   - 接收人类按键或鼠标点击动作指令（触发时**平滑自动切断 AI 托管，实现 0 冲突的人机接管**）。

---

## 4. 全景 Web 实时驾驶舱架构

```text
┌─────────────────┬─────────────────┬─────────────────────────┬─────────────────────────┐
│  栏 1: 战况与背包 │  栏 2: 核心战场  │ 栏 3: TypeSafe 输入端视窗 │ 栏 4: TypeSafe 输出端大屏│
├─────────────────┼─────────────────┼─────────────────────────┼─────────────────────────┤
│ • 暂存区 (HOLD) │ • 10x20 核心棋盘 │ • 策略意图下拉组件 (Q)   │ • 候选落点胜选概率矩阵  │
│ • 预备队列(NEXT)│ • 2x 视网膜矢量  │   (极低纵向空间占用)    │ • 4 种宏观战术概率分布  │
│ • 得分/行数/等级 │ • AI 落点目标投影│ • 组装 Context State 树 │ • 危机与换块 Noul 标尺  │
│ • 连击数 (Combo)│ • 屏幕虚拟手柄  │ • 原生 Prompt 提问指令  │ • 5 级健康态势直方图    │
└─────────────────┴─────────────────┴─────────────────────────┴─────────────────────────┘
```

- **0% 模糊视网膜渲染 (Retina 2x)**：彻底剥离传统 Pygame 桌面窗口在高分屏下的模糊拉伸缺陷，采用 HTML5 Canvas 逻辑像素与物理像素 2x 矢量点对点绘制；
- **紧凑型策略意图下拉组件**：第 3 栏顶部提供现代深色玻璃拟态下拉选择器，仅占几十像素高度，释放充裕空间展示原始 Context JSON 与 Prompt Specs；
- **实时推理耗时与三档调速**：
  - 顶栏与看板高亮展示 TypeSafe 决策推理延迟（`12.5ms` 极速闪烁）；
  - 顶栏提供 `🐢 慢速 (120ms)`、`⚡ 标准 (40ms)`、`🚀 极速 (10ms)` 动作巡航步频切换。

---

## 5. 快速上手 (Quick Start)

项目已配置完备的工程化依赖，推荐使用 `uv` 极速运行：

```bash
# 1. 克隆代码
git clone https://github.com/liuliangbin899/typesafe-tetris.git
cd typesafe-tetris

# 2. 一键启动 (自动打开现代 Web 驾驶舱: http://127.0.0.1:8000)
uv run python main.py
```

*若使用传统 pip：`pip install -r requirements.txt && python main.py`*

### 双模交互控制指南

- **鼠标操控**：主棋盘下方内置 **【🎮 屏幕手动控制台】**，点击方向键/旋转/硬降/暂存即可直接操作；
- **键盘操控**：
  - `M` 或 `A`：随时在 **AI 自动驾驶** 与 **人类手动操控** 之间无缝切换；
  - `Q`：轮换当前策略意图（“稳扎稳打”、“组织大招”、“消行冲刺”、“绝境求生”）；
  - `←` / `→` / `↓`：左右平移与加速软降；
  - `↑` / `Z`：顺时针 / 逆时针 SRS 旋转；
  - `SPACE` (空格)：瞬间硬降触底锁定；
  - `C`：暂存方块 (Hold)；`P`：暂停 / 继续；`R`：重开游戏。

### 自动化测试验证

```bash
uv run pytest tests/
```
覆盖核心引擎物理、SRS 踢墙碰撞、TypeSafe 契约规范与 Web 状态广播的 **14 项测试全部通过**。

---

## 6. 开源许可证

本项目基于 [MIT License](LICENSE) 开源。
