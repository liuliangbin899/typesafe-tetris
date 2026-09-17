"""
Unit Tests for Native TypeSafe Tetris AI Agent and Primitives.
"""

import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from tetris.ai.evaluator import BoardEvaluator
    from tetris.ai.planner import ActionPlanner
    from tetris.ai.typesafe_agent import TypeSafeTetrisAgent
    from tetris.constants import TOTAL_ROWS, BOARD_WIDTH
    from tetris.engine import TetrisEngine
    from tetris.models import ActivePiece, GameStatus
except ImportError:
    from ai.evaluator import BoardEvaluator  # type: ignore
    from ai.planner import ActionPlanner  # type: ignore
    from ai.typesafe_agent import TypeSafeTetrisAgent  # type: ignore
    from constants import TOTAL_ROWS, BOARD_WIDTH  # type: ignore
    from engine import TetrisEngine  # type: ignore
    from models import ActivePiece, GameStatus  # type: ignore



class TestTypeSafeTetrisAgent(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = TetrisEngine(random_seed=42)
        self.engine.start()
        self.agent = TypeSafeTetrisAgent()

    def test_evaluator_candidates(self) -> None:
        """测试几何指标计算与落点候选生成"""
        board = self.engine.get_state().board
        candidates = BoardEvaluator.generate_candidates(board, 'T', max_candidates=6)
        self.assertGreater(len(candidates), 0)
        self.assertLessEqual(len(candidates), 6)

        first = candidates[0]
        self.assertIn(first.rotation_index, (0, 1, 2, 3))
        self.assertGreaterEqual(first.target_x, -2)
        self.assertLess(first.target_x, BOARD_WIDTH)
        self.assertGreater(len(first.to_summary()), 10)

    def test_action_planner(self) -> None:
        """测试动作路径规划反解"""
        piece = ActivePiece(type='T', matrix=[[0, 1, 0], [1, 1, 1], [0, 0, 0]], x=3, y=2, rotation_index=0)
        board = self.engine.get_state().board
        candidates = BoardEvaluator.generate_candidates(board, 'T', max_candidates=1)
        target = candidates[0]

        actions = ActionPlanner.plan_actions(piece, target)
        self.assertIn('HARD_DROP', actions)
        # 验证最后一个动作必然是 HARD_DROP
        self.assertEqual(actions[-1], 'HARD_DROP')

    def test_native_typesafe_primitives(self) -> None:
        """测试原生 TypeSafe SDK 三原语 (Noul, Choice, Score) 输出与快照生成"""
        state = self.engine.get_state()
        chosen_cand, snapshot = self.agent.decide(state, question="稳扎稳打平稳通关")

        self.assertIsNotNone(chosen_cand)
        self.assertEqual(snapshot.question, "稳扎稳打平稳通关")

        # 1. 验证 Noul 原语输出
        self.assertIsInstance(snapshot.is_crisis_danger, bool)
        self.assertGreaterEqual(snapshot.crisis_prob, 0.0)
        self.assertLessEqual(snapshot.crisis_prob, 1.0)
        self.assertIsInstance(snapshot.should_hold, bool)

        # 2. 验证 Choice 原语输出
        self.assertIn(snapshot.tactic_mode, ["SURVIVAL", "FLATTEN", "BUILD_TETRIS", "SCORE_ATTACK"])
        self.assertGreaterEqual(snapshot.tactic_confidence, 0.0)
        self.assertEqual(snapshot.selected_candidate_id, chosen_cand.id)

        # 3. 验证 Score 原语输出
        self.assertGreaterEqual(snapshot.board_health, 1.0)
        self.assertLessEqual(snapshot.board_health, 5.0)

    def test_question_influence_on_tactic(self) -> None:
        """测试不同 User Question 对战略 Choice 的影响"""
        state = self.engine.get_state()

        # 问题 1：要求防守通关
        _, snap1 = self.agent.decide(state, question="稳健通关不冒险")
        self.assertIn(snap1.tactic_mode, ["FLATTEN", "SURVIVAL"])

        # 问题 2：要求追求 Tetris 4 消
        _, snap2 = self.agent.decide(state, question="帮我准备打出Tetris大招")
        self.assertEqual(snap2.tactic_mode, "BUILD_TETRIS")


if __name__ == '__main__':
    unittest.main()
