"""
Board Evaluator & Candidate Generator for Tetris.
Extracts high-level geometric facts and simulates all legal placements.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

try:
    from ..constants import (
        BOARD_HEIGHT,
        BOARD_WIDTH,
        BUFFER_ROWS,
        SHAPES,
        TOTAL_ROWS,
    )
    from ..models import ActivePiece, RotationIndex, TetrominoType
except (ImportError, ValueError):
    from constants import (  # type: ignore
        BOARD_HEIGHT,
        BOARD_WIDTH,
        BUFFER_ROWS,
        SHAPES,
        TOTAL_ROWS,
    )
    from models import ActivePiece, RotationIndex, TetrominoType  # type: ignore



@dataclass
class BoardMetrics:
    """棋盘客观几何指标"""
    column_heights: List[int]
    max_height: int
    aggregate_height: int
    holes_count: int
    bumpiness: int
    right_well_depth: int  # 最右侧列与次右侧列的落差 (保留打 Tetris 的井深)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_height": self.max_height,
            "aggregate_height": self.aggregate_height,
            "holes_count": self.holes_count,
            "bumpiness": self.bumpiness,
            "right_well_depth": self.right_well_depth,
        }


@dataclass
class CandidatePlacement:
    """单个合法落点候选方案"""
    id: str
    piece_type: TetrominoType
    rotation_index: RotationIndex
    target_x: int
    target_y: int
    matrix: List[List[int]]
    lines_cleared: int
    resulting_holes: int
    resulting_bumpiness: int
    resulting_max_height: int
    is_tspin: bool = False
    heuristic_score: float = 0.0

    def to_summary(self) -> str:
        """格式化为自然语言描述，供 TypeSafe 智能原语理解与点选"""
        clear_str = f"clears {self.lines_cleared} line(s)" if self.lines_cleared > 0 else "no lines cleared"
        tspin_str = " (T-SPIN!)" if self.is_tspin else ""
        return (
            f"Rot {self.rotation_index * 90}° at col {self.target_x}: "
            f"{clear_str}{tspin_str}, leaves {self.resulting_holes} holes, "
            f"max height {self.resulting_max_height}, bumpiness {self.resulting_bumpiness}"
        )


class BoardEvaluator:
    """棋盘几何特征提取与候选落点生成器"""

    @staticmethod
    def calculate_metrics(board: List[List[int]]) -> BoardMetrics:
        """提取当前棋盘的统计指标"""
        col_heights = [0] * BOARD_WIDTH
        holes = 0

        # 计算每列高度 (自下而上)
        for c in range(BOARD_WIDTH):
            for r in range(BUFFER_ROWS, TOTAL_ROWS):
                if board[r][c] != 0:
                    col_heights[c] = TOTAL_ROWS - r
                    break

        # 计算空洞数 (在某列最高填充块之下的空格子)
        for c in range(BOARD_WIDTH):
            found_top = False
            for r in range(TOTAL_ROWS - col_heights[c], TOTAL_ROWS):
                if board[r][c] != 0:
                    found_top = True
                elif found_top:
                    holes += 1

        # 计算相邻列落差凹凸度 (Bumpiness)
        bumpiness = sum(abs(col_heights[c] - col_heights[c + 1]) for c in range(BOARD_WIDTH - 1))

        max_height = max(col_heights)
        agg_height = sum(col_heights)
        # 右侧井深：第 8 列高度减去第 9 列高度
        right_well_depth = max(0, col_heights[8] - col_heights[9]) if BOARD_WIDTH >= 10 else 0

        return BoardMetrics(
            column_heights=col_heights,
            max_height=max_height,
            aggregate_height=agg_height,
            holes_count=holes,
            bumpiness=bumpiness,
            right_well_depth=right_well_depth,
        )

    @classmethod
    def rotate_matrix(cls, matrix: List[List[int]], rot_count: int) -> List[List[int]]:
        """顺时针旋转矩阵 rot_count 次"""
        curr = [row[:] for row in matrix]
        for _ in range(rot_count % 4):
            curr = [list(row) for row in zip(*curr[::-1])]
        return curr

    @classmethod
    def simulate_drop(
        cls,
        board: List[List[int]],
        piece_matrix: List[List[int]],
        start_x: int,
    ) -> Optional[int]:
        """模拟将方块在指定 x 坐标处硬降，返回落点 target_y，若无法放置返回 None"""
        # 边界与初始越界检测
        p_h = len(piece_matrix)
        p_w = len(piece_matrix[0])

        # 检查是否横向越界
        for r_idx, row in enumerate(piece_matrix):
            for c_idx, val in enumerate(row):
                if val != 0:
                    bx = start_x + c_idx
                    if bx < 0 or bx >= BOARD_WIDTH:
                        return None

        # 从顶部往下试探
        curr_y = 0
        def collides(y_pos: int) -> bool:
            for r_idx, row in enumerate(piece_matrix):
                for c_idx, val in enumerate(row):
                    if val != 0:
                        bx = start_x + c_idx
                        by = y_pos + r_idx
                        if by >= TOTAL_ROWS:
                            return True
                        if by >= 0 and board[by][bx] != 0:
                            return True
            return False

        if collides(curr_y):
            return None

        while not collides(curr_y + 1):
            curr_y += 1

        # 检查是否整块都死在可见行上方
        visible_blocks = 0
        for r_idx, row in enumerate(piece_matrix):
            for c_idx, val in enumerate(row):
                if val != 0 and (curr_y + r_idx) >= BUFFER_ROWS:
                    visible_blocks += 1

        if visible_blocks == 0:
            return None

        return curr_y

    @classmethod
    def generate_candidates(
        cls,
        board: List[List[int]],
        piece_type: TetrominoType,
        max_candidates: int = 8,
    ) -> List[CandidatePlacement]:
        """
        穷举生成当前方块的所有合法放置候选，并根据启发式进行多样化筛选
        返回最多 max_candidates 个高质量落点方案
        """
        raw_shape = SHAPES[piece_type]
        candidates: List[CandidatePlacement] = []
        cand_idx = 0

        # O 块只有 1 个独立朝向，I/S/Z 只有 2 个独立朝向，J/L/T 有 4 个
        rot_angles = [0] if piece_type == 'O' else ([0, 1] if piece_type in ('I', 'S', 'Z') else [0, 1, 2, 3])

        for rot in rot_angles:
            rot_matrix = cls.rotate_matrix(raw_shape, rot)
            p_w = len(rot_matrix[0])

            # 遍历可能的横向位置 (从 -2 到 BOARD_WIDTH)
            for test_x in range(-2, BOARD_WIDTH):
                drop_y = cls.simulate_drop(board, rot_matrix, test_x)
                if drop_y is None:
                    continue

                # 模拟将方块放入棋盘并计算消行
                sim_board = [row[:] for row in board]
                for r_idx, row in enumerate(rot_matrix):
                    for c_idx, val in enumerate(row):
                        if val != 0:
                            bx = test_x + c_idx
                            by = drop_y + r_idx
                            if 0 <= bx < BOARD_WIDTH and 0 <= by < TOTAL_ROWS:
                                sim_board[by][bx] = 1

                # 统计消行
                lines_cleared = sum(1 for r in range(TOTAL_ROWS) if all(sim_board[r][c] != 0 for c in range(BOARD_WIDTH)))
                # 清除满行
                if lines_cleared > 0:
                    new_b = [[0] * BOARD_WIDTH for _ in range(lines_cleared)]
                    for r in range(TOTAL_ROWS):
                        if not all(sim_board[r][c] != 0 for c in range(BOARD_WIDTH)):
                            new_b.append(sim_board[r])
                    sim_board = new_b

                metrics = cls.calculate_metrics(sim_board)

                # 启发式综合分：鼓励消行、严厉惩罚空洞和过大凹凸、鼓励保留右侧单井打 Tetris
                # score = lines * 40 - holes * 35 - bumpiness * 5 - max_height * 4
                h_score = (
                    (lines_cleared ** 2) * 50.0
                    - metrics.holes_count * 45.0
                    - metrics.bumpiness * 6.0
                    - metrics.max_height * 5.0
                    + min(metrics.right_well_depth, 4) * 8.0
                )

                candidates.append(
                    CandidatePlacement(
                        id=f"cand_{cand_idx}",
                        piece_type=piece_type,
                        rotation_index=rot,  # type: ignore
                        target_x=test_x,
                        target_y=drop_y,
                        matrix=rot_matrix,
                        lines_cleared=lines_cleared,
                        resulting_holes=metrics.holes_count,
                        resulting_bumpiness=metrics.bumpiness,
                        resulting_max_height=metrics.max_height,
                        is_tspin=(piece_type == 'T' and lines_cleared > 0),
                        heuristic_score=h_score,
                    )
                )
                cand_idx += 1

        if not candidates:
            return []

        # 按启发分从高到低排序，选取多样化的高质量候选
        candidates.sort(key=lambda c: c.heuristic_score, reverse=True)

        # 保证最多返回 max_candidates 个，但必须包含：
        # 1. 消除行数最多的方案 (消行优先)
        # 2. 空洞最少的方案 (平整安全优先)
        # 3. 启发式综合得分最高的方案
        selected: List[CandidatePlacement] = []
        # 最优综合
        selected.append(candidates[0])

        # 消行最多的方案 (若不同)
        max_clear_cand = max(candidates, key=lambda c: c.lines_cleared)
        if max_clear_cand.id not in [s.id for s in selected]:
            selected.append(max_clear_cand)

        # 空洞最少的方案 (若不同)
        min_hole_cand = min(candidates, key=lambda c: c.resulting_holes)
        if min_hole_cand.id not in [s.id for s in selected]:
            selected.append(min_hole_cand)

        # 其余按排序填充
        for c in candidates:
            if len(selected) >= max_candidates:
                break
            if c.id not in [s.id for s in selected]:
                selected.append(c)

        # 重新为选中的候选命名规范 ID: c0, c1, ...
        for idx, item in enumerate(selected):
            item.id = f"c{idx}"

        return selected
