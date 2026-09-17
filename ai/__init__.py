"""
Tetris AI Package powered by TypeSafe System One Native Primitives.
"""

try:
    from .evaluator import BoardEvaluator, CandidatePlacement
    from .planner import ActionPlanner
    from .typesafe_agent import TypeSafeTetrisAgent
except ImportError:
    from ai.evaluator import BoardEvaluator, CandidatePlacement  # type: ignore
    from ai.planner import ActionPlanner  # type: ignore
    from ai.typesafe_agent import TypeSafeTetrisAgent  # type: ignore

__all__ = [
    "BoardEvaluator",
    "CandidatePlacement",
    "ActionPlanner",
    "TypeSafeTetrisAgent",
]
