"""
Tetris Guideline Constants, SRS Tables, Matrices, and Scoring Rules.
"""

from typing import Dict, List, Tuple

try:
    from .models import RotationIndex, TetrominoType
except ImportError:
    from models import RotationIndex, TetrominoType  # type: ignore



# === 1. 棋盘规格 (Board Dimensions) ===
BOARD_WIDTH = 10         # 标准列数
BOARD_HEIGHT = 20        # 可见行数
BUFFER_ROWS = 4          # 顶部隐藏缓冲行 (方块入场与高位旋转)
TOTAL_ROWS = BOARD_HEIGHT + BUFFER_ROWS  # 24 行

# 方块出场起始位置 (Spawn Position: x, y)
# 默认在第 4 列附近居中，位于缓冲行 (例如 y = 2)
SPAWN_POSITIONS: Dict[TetrominoType, Tuple[int, int]] = {
    'I': (3, 2),
    'J': (3, 2),
    'L': (3, 2),
    'O': (4, 2),
    'S': (3, 2),
    'T': (3, 2),
    'Z': (3, 2),
}

# === 2. 七种方块初始形状矩阵 (Tetromino Initial Matrices at 0°) ===
# 1 代表实体填充，0 代表空白
SHAPES: Dict[TetrominoType, List[List[int]]] = {
    'I': [
        [0, 0, 0, 0],
        [1, 1, 1, 1],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ],
    'J': [
        [1, 0, 0],
        [1, 1, 1],
        [0, 0, 0],
    ],
    'L': [
        [0, 0, 1],
        [1, 1, 1],
        [0, 0, 0],
    ],
    'O': [
        [1, 1],
        [1, 1],
    ],
    'S': [
        [0, 1, 1],
        [1, 1, 0],
        [0, 0, 0],
    ],
    'T': [
        [0, 1, 0],
        [1, 1, 1],
        [0, 0, 0],
    ],
    'Z': [
        [1, 1, 0],
        [0, 1, 1],
        [0, 0, 0],
    ],
}

# 方块的整型标识 (存入棋盘便于区分颜色)
PIECE_IDS: Dict[TetrominoType, int] = {
    'I': 1,
    'J': 2,
    'L': 3,
    'O': 4,
    'S': 5,
    'T': 6,
    'Z': 7,
}

ID_TO_PIECE: Dict[int, TetrominoType] = {v: k for k, v in PIECE_IDS.items()}

# 方块官方标准配色 (RGB)
COLORS: Dict[TetrominoType, Tuple[int, int, int]] = {
    'I': (0, 220, 235),      # 青色 (Cyan)
    'J': (33, 115, 243),     # 蓝色 (Blue)
    'L': (255, 140, 0),      # 橙色 (Orange)
    'O': (255, 215, 0),      # 黄色 (Yellow)
    'S': (46, 204, 113),     # 绿色 (Green)
    'T': (155, 89, 182),     # 紫色 (Purple)
    'Z': (231, 76, 60),      # 红色 (Red)
}

# === 3. SRS 超级旋转系统 (Super Rotation System) 踢墙表 ===
# 踢墙坐标系规范：(dx, dy)，其中 dx 向右为正，dy 向下为正 (适合二维网格数组运算)
# 标准转换对: (from_rot, to_rot) -> List[Tuple[dx, dy]] (共 5 组测试偏移)

# JLSTZ 踢墙表
WALL_KICK_JLSTZ: Dict[Tuple[int, int], List[Tuple[int, int]]] = {
    (0, 1): [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)],
    (1, 0): [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)],
    (1, 2): [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)],
    (2, 1): [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)],
    (2, 3): [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)],
    (3, 2): [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)],
    (3, 0): [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)],
    (0, 3): [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)],
}

# I 专属踢墙表
WALL_KICK_I: Dict[Tuple[int, int], List[Tuple[int, int]]] = {
    (0, 1): [(0, 0), (-2, 0), (1, 0), (-2, 1), (1, -2)],
    (1, 0): [(0, 0), (2, 0), (-1, 0), (2, -1), (-1, 2)],
    (1, 2): [(0, 0), (-1, 0), (2, 0), (-1, -2), (2, 1)],
    (2, 1): [(0, 0), (1, 0), (-2, 0), (1, 2), (-2, -1)],
    (2, 3): [(0, 0), (2, 0), (-1, 0), (2, -1), (-1, 2)],
    (3, 2): [(0, 0), (-2, 0), (1, 0), (-2, 1), (1, -2)],
    (3, 0): [(0, 0), (1, 0), (-2, 0), (1, 2), (-2, -1)],
    (0, 3): [(0, 0), (-1, 0), (2, 0), (-1, -2), (2, 1)],
}

# === 4. 游戏操作与手感常量 (Handling & Timers) ===
LOCK_DELAY_MS: float = 500.0     # 触底锁定延迟 (毫秒)
MAX_LOCK_RESETS: int = 15        # 每次落块触底后最多重置锁定的移动/旋转次数

# DAS & ARR (手感关键)
DEFAULT_DAS_MS: float = 130.0    # Delayed Auto Shift: 长按初次平移前延迟 (毫秒)
DEFAULT_ARR_MS: float = 25.0     # Auto Repeat Rate: 触发后每次快速平移间隔 (毫秒)
SOFT_DROP_INTERVAL_MS: float = 35.0  # 软降间隔 (毫秒)

# === 5. 速度等级与自然重力下落间隔 (Fall Interval per Level) ===
# 遵循 Tetris Guideline 标准公式：(0.8 - ((Level - 1) * 0.007)) ^ (Level - 1) 秒
def get_fall_interval_ms(level: int) -> float:
    """根据等级返回自然下落的时间间隔 (毫秒)"""
    level = max(1, min(level, 20))
    # 指数曲线逼近，每级提速，高级别极速挑战
    seconds = (0.8 - ((level - 1) * 0.007)) ** (level - 1)
    return max(16.0, seconds * 1000.0)

# === 6. 标准计分表 (Tetris Guideline Scoring) ===
SCORE_TABLE: Dict[str, int] = {
    'SINGLE': 100,
    'DOUBLE': 300,
    'TRIPLE': 500,
    'TETRIS': 800,
    'TSPIN_MINI_NO_LINE': 100,
    'TSPIN_NO_LINE': 400,
    'TSPIN_MINI_SINGLE': 200,
    'TSPIN_SINGLE': 800,
    'TSPIN_DOUBLE': 1200,
    'TSPIN_TRIPLE': 1600,
    'PERFECT_CLEAR_SINGLE': 800,
    'PERFECT_CLEAR_DOUBLE': 1200,
    'PERFECT_CLEAR_TRIPLE': 1800,
    'PERFECT_CLEAR_TETRIS': 2000,
    'SOFT_DROP_PER_CELL': 1,
    'HARD_DROP_PER_CELL': 2,
}

# Back-to-Back 奖励倍率
BACK_TO_BACK_MULTIPLIER = 1.5
# 每连击额外奖励 = 50 * combo * level
COMBO_MULTIPLIER = 50
