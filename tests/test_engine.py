"""
Unit Tests for Headless Tetris Engine.
Runs purely in memory without GUI or display dependencies.
"""

import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from tetris.constants import BOARD_WIDTH, TOTAL_ROWS, SHAPES, LOCK_DELAY_MS
    from tetris.engine import TetrisEngine
    from tetris.models import GameStatus, TetrisEvents, LineClearEvent, ActivePiece
    from tetris.randomizer import SevenBagRandomizer, ALL_PIECES
except ImportError:
    from constants import BOARD_WIDTH, TOTAL_ROWS, SHAPES, LOCK_DELAY_MS  # type: ignore
    from engine import TetrisEngine  # type: ignore
    from models import GameStatus, TetrisEvents, LineClearEvent, ActivePiece  # type: ignore
    from randomizer import SevenBagRandomizer, ALL_PIECES  # type: ignore



class TestTetrisEngine(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = TetrisEngine(random_seed=42)
        self.engine.start()

    def test_7_bag_randomizer(self) -> None:
        """验证 7-Bag 算法：抽 14 个块，每个块必定出现恰好 2 次"""
        randomizer = SevenBagRandomizer(seed=123)
        pieces = [randomizer.next_piece() for _ in range(14)]
        for p in ALL_PIECES:
            self.assertEqual(pieces.count(p), 2, f"Piece {p} did not appear exactly 2 times in 14 draws.")

    def test_start_and_spawn(self) -> None:
        """验证游戏启动与首个方块生成"""
        state = self.engine.get_state()
        self.assertEqual(state.status, GameStatus.PLAYING)
        self.assertIsNotNone(state.current_piece)
        self.assertEqual(len(state.next_queue), 5)
        self.assertIsNone(state.hold_piece)
        self.assertTrue(state.can_hold)

    def test_move_left_right_bounds(self) -> None:
        """验证向左移动到达左边界无法继续越界"""
        piece = self.engine.get_state().current_piece
        self.assertIsNotNone(piece)

        # 连续向左移动 10 次
        for _ in range(10):
            self.engine.move_left()

        cur_x = self.engine.get_state().current_piece.x
        # 尝试再向左移动一次应该返回 False
        res = self.engine.move_left()
        self.assertFalse(res)
        self.assertEqual(self.engine.get_state().current_piece.x, cur_x)

    def test_hard_drop(self) -> None:
        """验证硬降：瞬降触底、固化并生成下一个方块"""
        old_piece_type = self.engine.get_state().current_piece.type
        result = self.engine.hard_drop()

        self.assertGreater(result.cells_dropped, 0)
        state = self.engine.get_state()
        self.assertIsNotNone(state.current_piece)
        # 棋盘上应该已有固化方块
        has_blocks = any(any(val != 0 for val in row) for row in state.board)
        self.assertTrue(has_blocks)

    def test_hold_mechanism(self) -> None:
        """验证 Hold 暂存机制与同一落块周期只能暂存一次"""
        first_piece_type = self.engine.get_state().current_piece.type
        # 第一次 hold 成功
        success = self.engine.hold()
        self.assertTrue(success)
        state = self.engine.get_state()
        self.assertEqual(state.hold_piece, first_piece_type)
        self.assertFalse(state.can_hold)

        # 同一周期第二次 hold 应该被拒绝
        second_hold = self.engine.hold()
        self.assertFalse(second_hold)

    def test_line_clear_and_scoring(self) -> None:
        """验证填满一行后的消除与得分事件"""
        # 手动构造棋盘：最底部第 23 行填满 9 格，留一格
        bottom_row = TOTAL_ROWS - 1
        for col in range(1, BOARD_WIDTH):
            self.engine._board[bottom_row][col] = 1

        # 强制设置当前活动方块为放置在 col 0 的单块
        self.engine._current_piece = ActivePiece(
            type='I',
            matrix=[[1]],
            x=0,
            y=bottom_row - 1,
            rotation_index=0,
        )

        cleared_events = []
        self.engine.on(TetrisEvents.LINE_CLEAR, lambda data: cleared_events.append(data))

        # 软降一格落入底部并锁定
        self.engine.soft_drop()
        self.engine._lock_current_piece()

        # 验证消行事件被触发
        self.assertEqual(len(cleared_events), 1)
        event: LineClearEvent = cleared_events[0]
        self.assertEqual(event.line_count, 1)
        self.assertGreater(event.score_gained, 0)
        self.assertEqual(self.engine.get_state().lines, 1)

    def test_srs_wall_kick(self) -> None:
        """验证 SRS 贴墙踢墙测试 (Wall Kick)"""
        # 将 I 块竖直放置 (rotation 1)，并贴在最左侧 x = -1 (使得实体块在 x = 0)
        self.engine._current_piece = ActivePiece(
            type='I',
            matrix=[
                [0, 0, 1, 0],
                [0, 0, 1, 0],
                [0, 0, 1, 0],
                [0, 0, 1, 0],
            ],
            x=-2,  # 此时第 2 列恰在 x=0
            y=10,
            rotation_index=1,
        )
        # 顺时针旋转回横向 (1 -> 2)，横向需要占用 4 列，必然需要踢墙偏移右移
        rotated = self.engine.rotate_cw()
        self.assertTrue(rotated)
        self.assertGreaterEqual(self.engine.get_state().current_piece.x, -1)

    def test_lock_delay_and_tick(self) -> None:
        """验证 500ms 锁定延迟与 tick 自然触发固化"""
        # 将方块放在最底部 (y = TOTAL_ROWS - 2)
        bottom_y = TOTAL_ROWS - 2
        self.engine._current_piece = ActivePiece(
            type='O',
            matrix=[[1, 1], [1, 1]],
            x=4,
            y=bottom_y,
            rotation_index=0,
        )
        # 此时下一格就是底部越界，进入触底状态
        self.engine.tick(100.0)
        self.assertTrue(self.engine._is_touching_ground)
        self.assertEqual(self.engine._status, GameStatus.PLAYING)

        # 累加超过 500ms 锁定时间
        self.engine.tick(450.0)
        # 应该触发固化并生成新块
        state = self.engine.get_state()
        self.assertTrue(self.engine._board[bottom_y][4] != 0)


if __name__ == '__main__':
    unittest.main()
