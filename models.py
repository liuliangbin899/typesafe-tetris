"""
Core Data Models, Types, and Interfaces for Tetris Engine.
Strictly decoupled from rendering and following the Tetris Guideline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Literal, Optional, Protocol, Tuple, TypeVar, Union

# 1. 七种标准四连块类型 (Tetromino Type)
TetrominoType = Literal['I', 'J', 'L', 'O', 'S', 'T', 'Z']

# 2. 四种旋转朝向 (0: 0°, 1: 90° CW, 2: 180°, 3: 270° CCW)
RotationIndex = Literal[0, 1, 2, 3]


class GameStatus(str, Enum):
    """游戏状态枚举"""
    IDLE = 'IDLE'
    PLAYING = 'PLAYING'
    PAUSED = 'PAUSED'
    GAME_OVER = 'GAME_OVER'


@dataclass
class ActivePiece:
    """当前活动方块信息"""
    type: TetrominoType
    matrix: List[List[int]]          # 形状矩阵 (e.g. 3x3 或 4x4, 1 表示实体块, 0 表示空白)
    x: int = 0                       # 棋盘网格横坐标 (0-9)
    y: int = 0                       # 棋盘网格纵坐标 (含顶部隐藏缓冲行)
    rotation_index: RotationIndex = 0  # 旋转朝向 (0, 1, 2, 3)
    spawn_id: int = 0                # 唯一自增入场编号 (确保决策指纹绝对唯一，杜绝漏检)

    def clone(self) -> ActivePiece:
        """浅/深拷贝活动方块，便于试探性计算"""
        return ActivePiece(
            type=self.type,
            matrix=[row[:] for row in self.matrix],
            x=self.x,
            y=self.y,
            rotation_index=self.rotation_index,
            spawn_id=self.spawn_id,
        )


@dataclass
class HardDropResult:
    """硬降执行结果"""
    cells_dropped: int
    lines_cleared: int
    score_gained: int


@dataclass
class LineClearEvent:
    """消行事件负载数据"""
    cleared_lines: List[int]        # 被消除的行号（自上而下或自下而上）
    line_count: int                 # 消除行数 (1=Single, 2=Double, 3=Triple, 4=Tetris)
    score_gained: int               # 本次消除获得的分数
    is_tspin: bool = False          # 是否触发 T-Spin
    is_tspin_mini: bool = False     # 是否触发 T-Spin Mini
    is_back_to_back: bool = False   # 是否 B2B 连续大招加成
    combo: int = 0                  # 当前连击次数
    is_perfect_clear: bool = False  # 是否全清 (All Clear)


@dataclass
class PieceEvent:
    """方块相关事件负载数据"""
    piece: ActivePiece
    next_queue: Optional[List[TetrominoType]] = None


@dataclass
class LevelUpEvent:
    """升级事件负载数据"""
    new_level: int
    fall_interval_ms: float


@dataclass
class GameOverEvent:
    """游戏结束事件负载数据"""
    final_score: int
    total_lines: int


@dataclass
class CandidateDetail:
    """候选落点详细数据 (供渲染层绘制概率条与动作预期)"""
    id: str                                      # 方案标识 (如 c0, c1...)
    rotation_index: int                          # 旋转朝向 (0, 1, 2, 3)
    target_x: int                                # 目标落脚列 (0~9)
    target_y: int                                # 目标落脚行
    lines_cleared: int                           # 预期消除行数
    resulting_holes: int                         # 产生的空洞数
    height_diff: int                             # 高度变化
    probability: float                           # TypeSafe Choice 模型预测的胜选概率 (0.0~1.0)
    is_chosen: bool                              # 是否为模型最终胜选的方案
    summary: str                                 # 中文动作收益小结


@dataclass
class AIDecisionSnapshot:
    """TypeSafe AI 决策快照 (供渲染层实时呈现三原语判定结果与全量概率分布)"""
    question: str = ""                           # 用户当前设定的提问/目标
    # Noul 原语 (条件门控真值概率)
    is_crisis_danger: bool = False               # Noul: 濒危保命判定
    crisis_prob: float = 0.0                     # Noul: 濒危概率 (0.0~1.0)
    should_hold: bool = False                    # Noul: 换块暂存判定
    hold_prob: float = 0.0                       # Noul: 换块概率 (0.0~1.0)
    # Choice 原语 1 (战术模式)
    tactic_mode: str = "FLATTEN"                 # Choice: 战术分类 (SURVIVAL / FLATTEN / BUILD_TETRIS / SCORE_ATTACK)
    tactic_confidence: float = 0.0               # Choice: 战术置信度
    tactic_probabilities: Dict[str, float] = field(default_factory=dict) # 战术模式完整概率分布
    # Choice 原语 2 (候选落点方案排他决策与概率矩阵)
    selected_candidate_id: str = ""              # Choice: 选定的候选落点 ID
    placement_confidence: float = 0.0            # Choice: 落点置信度
    selected_candidate_summary: str = ""         # 选定落点的直观动作描述
    target_placement_coords: Optional[Tuple[int, int, int]] = None # (target_x, target_y, rotation_index) 用于棋盘透视
    candidate_probabilities: Dict[str, float] = field(default_factory=dict) # 所有候选落点的完整概率分布
    candidates_detail: List[CandidateDetail] = field(default_factory=list)  # Top 候选落点详情清单
    # Score 原语 (可持续健康度多级评分与离散概率直方图)
    board_health: float = 3.0                    # Score: 局面健康加权综合评分 (1.0 ~ 5.0)
    score_confidence: float = 0.0                # Score: 评分置信度
    score_probabilities: Dict[int, float] = field(default_factory=dict) # 1~5 各级别的离散概率分布
    score_legend: Dict[int, str] = field(default_factory=dict)         # 各级别描述
    # 输入端完整数据 (State 与 Questions)
    raw_state: Dict[str, Any] = field(default_factory=dict)            # 发送给 TypeSafe 的组装 State 完整结构化字典
    question_instructions: Dict[str, str] = field(default_factory=dict) # 各原语的具体提问指令 (Instructions)
    # 状态与解释
    board_metrics_snapshot: Dict[str, Any] = field(default_factory=dict) # 棋盘几何物理事实指标
    summary_text: str = ""                       # 决策理由简报


@dataclass
class GameState:
    """游戏全局快照状态 (用于外部状态查询与绘制渲染)"""
    status: GameStatus
    board: List[List[int]]                      # 标准棋盘：宽度 10，高度 20 + 4 缓冲行（总共 24 行）
    current_piece: Optional[ActivePiece] = None # 当前活动方块
    ghost_y: int = 0                            # 幽灵落点 Y 坐标
    next_queue: List[TetrominoType] = field(default_factory=list) # 下一个预览队列 (保留 5 个)
    hold_piece: Optional[TetrominoType] = None  # 暂存区方块
    can_hold: bool = True                       # 当前落块周期内是否允许再次 hold
    score: int = 0                              # 当前得分
    lines: int = 0                              # 已消除总行数
    level: int = 1                              # 速度等级
    combo: int = -1                             # 连续消行连击数 (-1 或 0 表示无连击)
    back_to_back: bool = False                  # 当前是否处于 Back-to-Back 链状态
    ai_decision: Optional[AIDecisionSnapshot] = None # TypeSafe AI 当前决策快照
    auto_pilot: bool = False                     # 是否开启 AI 自动驾驶托管


# 事件回调函数签名类型
T = TypeVar('T')
EventHandler = Callable[[Any], None]


class TetrisEvents:
    """事件名常数集合"""
    PIECE_MOVE = "piece_move"
    PIECE_SPAWN = "piece_spawn"
    PIECE_LOCK = "piece_lock"
    LINE_CLEAR = "line_clear"
    LEVEL_UP = "level_up"
    GAME_OVER = "game_over"


class ITetrisEngine(Protocol):
    """
    俄罗斯方块核心引擎接口规范 (Engine API Interface)
    纯 Headless 接口定义，完全独立于任何渲染引擎。
    """

    # === 1. 游戏生命周期控制 ===
    def start(self) -> None:
        """开始游戏"""
        ...

    def pause(self) -> None:
        """暂停游戏"""
        ...

    def resume(self) -> None:
        """继续游戏"""
        ...

    def restart(self) -> None:
        """重新开始游戏"""
        ...

    def tick(self, delta_time_ms: float) -> None:
        """
        外部时钟驱动或 requestAnimationFrame 轮询
        处理自然下落、触底锁定延迟 (Lock Delay) 等
        """
        ...

    # === 2. 玩家操作指令 (Actions) ===
    def move_left(self) -> bool:
        """左移一格，成功返回 True，阻挡返回 False"""
        ...

    def move_right(self) -> bool:
        """右移一格，成功返回 True，阻挡返回 False"""
        ...

    def soft_drop(self) -> bool:
        """软降（加速下落一格），成功返回 True，触底返回 False"""
        ...

    def hard_drop(self) -> HardDropResult:
        """硬降（瞬间触底并立即锁定）"""
        ...

    def rotate_cw(self) -> bool:
        """顺时针旋转 (结合 SRS 踢墙系统)，成功返回 True"""
        ...

    def rotate_ccw(self) -> bool:
        """逆时针旋转 (结合 SRS 踢墙系统)，成功返回 True"""
        ...

    def hold(self) -> bool:
        """暂存方块，成功返回 True，若本周期已暂存过则返回 False"""
        ...

    # === 3. 查询接口 (Queries) ===
    def get_state(self) -> GameState:
        """获取当前全局游戏状态快照"""
        ...

    def get_ghost_position(self) -> Tuple[int, int]:
        """计算幽灵投影块的 (x, y) 坐标"""
        ...

    # === 4. 事件监听体系 (Event Bus) ===
    def on(self, event_name: str, handler: EventHandler) -> None:
        """注册事件监听器"""
        ...

    def off(self, event_name: str, handler: EventHandler) -> None:
        """注销事件监听器"""
        ...
