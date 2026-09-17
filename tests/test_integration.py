"""
Integration Smoke Test for Tetris Web Backend & Headless Game Loop.
Verifies end-to-end headless engine, TypeSafe agent, and Web state serialization.
"""

import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from tetris.engine import TetrisEngine
    from tetris.models import GameStatus
    from tetris.ai.typesafe_agent import TypeSafeTetrisAgent
    from tetris.ai.planner import ActionPlanner
    from tetris.web.server import manager
except ImportError:
    from engine import TetrisEngine  # type: ignore
    from models import GameStatus  # type: ignore
    from ai.typesafe_agent import TypeSafeTetrisAgent  # type: ignore
    from ai.planner import ActionPlanner  # type: ignore
    from web.server import manager  # type: ignore



class TestTetrisWebIntegration(unittest.TestCase):
    def test_headless_engine_and_agent_loop(self) -> None:
        """运行 60 帧纯净 Headless 核心引擎与 TypeSafe 决策规划，验证无任何崩溃"""
        engine = TetrisEngine(random_seed=123)
        agent = TypeSafeTetrisAgent()
        engine.start()

        actions_queue = []
        for frame in range(60):
            dt_ms = 16.6  # 约 60FPS
            state = engine.get_state()
            if state.current_piece and not actions_queue:
                chosen, snap = agent.decide(state)
                if chosen:
                    actions_queue = ActionPlanner.plan_actions(state.current_piece, chosen)

            if actions_queue:
                act = actions_queue.pop(0)
                ActionPlanner.execute_action(engine, act)

            engine.tick(dt_ms)

        current_state = engine.get_state()
        self.assertEqual(current_state.status, GameStatus.PLAYING)
        self.assertGreaterEqual(current_state.score, 0)

    def test_web_state_serialization(self) -> None:
        """测试 Web 端所广播的数据序列化完整性，确保前端所有字段契约匹配"""
        state_dict = manager.serialize_state()

        # 检查核心游戏字段
        self.assertIn("score", state_dict)
        self.assertIn("lines", state_dict)
        self.assertIn("level", state_dict)
        self.assertIn("board", state_dict)
        self.assertIn("current_piece", state_dict)
        self.assertIn("ghost_pos", state_dict)
        self.assertIn("next_queue", state_dict)

        # 检查棋盘尺寸与结构 (24 行包含 4 行隐形缓冲)
        self.assertEqual(len(state_dict["board"]), 24)
        self.assertEqual(len(state_dict["board"][0]), 10)

        # 触发一次决策以填充 ai_decision
        state = manager.engine.get_state()
        chosen, snap = manager.agent.decide(state)
        manager.current_decision_snapshot = snap
        state_dict = manager.serialize_state()

        # 检查 AI 决策字典
        ai_dict = state_dict["ai_decision"]
        self.assertIsNotNone(ai_dict)
        self.assertIn("question", ai_dict)
        self.assertIn("raw_state", ai_dict)
        self.assertIn("candidate_probabilities", ai_dict)
        self.assertIn("candidates_detail", ai_dict)
        self.assertIn("tactic_probabilities", ai_dict)
        self.assertIn("crisis_prob", ai_dict)
        self.assertIn("board_health", ai_dict)
        self.assertIn("summary_text", ai_dict)
