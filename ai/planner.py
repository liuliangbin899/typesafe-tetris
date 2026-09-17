"""
Action Planner for Tetris.
Translates selected CandidatePlacement into discrete executable engine actions.
"""

from typing import List

try:
    from ..models import ActivePiece, ITetrisEngine
    from .evaluator import CandidatePlacement
except (ImportError, ValueError):
    from models import ActivePiece, ITetrisEngine  # type: ignore
    from ai.evaluator import CandidatePlacement  # type: ignore




class ActionPlanner:
    """动作规划器：将目标落点解析为按键动作指令列表"""

    @staticmethod
    def plan_actions(current_piece: ActivePiece, candidate: CandidatePlacement) -> List[str]:
        """
        生成从当前活动方块状态到达目标落点的动作序列
        指令枚举: 'ROTATE_CW', 'ROTATE_CCW', 'MOVE_LEFT', 'MOVE_RIGHT', 'HARD_DROP'
        """
        actions: List[str] = []

        # 1. 计算旋转差异 (0, 1, 2, 3)
        curr_rot = current_piece.rotation_index
        target_rot = candidate.rotation_index

        rot_diff = (target_rot - curr_rot) % 4
        if rot_diff == 1:
            actions.append('ROTATE_CW')
        elif rot_diff == 2:
            actions.append('ROTATE_CW')
            actions.append('ROTATE_CW')
        elif rot_diff == 3:
            actions.append('ROTATE_CCW')

        # 2. 计算横向平移距离
        # 注意：旋转后方块在 x 轴的锚点可能一致，我们直接计算目标差
        curr_x = current_piece.x
        target_x = candidate.target_x
        x_diff = target_x - curr_x

        if x_diff > 0:
            actions.extend(['MOVE_RIGHT'] * x_diff)
        elif x_diff < 0:
            actions.extend(['MOVE_LEFT'] * abs(x_diff))

        # 3. 终结动作：硬降锁定
        actions.append('HARD_DROP')
        return actions

    @staticmethod
    def execute_action(engine: ITetrisEngine, action: str) -> None:
        """在引擎上执行单步动作"""
        if action == 'ROTATE_CW':
            engine.rotate_cw()
        elif action == 'ROTATE_CCW':
            engine.rotate_ccw()
        elif action == 'MOVE_LEFT':
            engine.move_left()
        elif action == 'MOVE_RIGHT':
            engine.move_right()
        elif action == 'HARD_DROP':
            engine.hard_drop()
        elif action == 'HOLD':
            engine.hold()
