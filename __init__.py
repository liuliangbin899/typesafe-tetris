"""
Tetris Standard Package - Headless Engine and Ultra-Crisp Web Cockpit
Follows the official Tetris Guideline standards.
"""

try:
    from .models import (
        ActivePiece,
        AIDecisionSnapshot,
        GameState,
        GameStatus,
        HardDropResult,
        ITetrisEngine,
        LineClearEvent,
        RotationIndex,
        TetrisEvents,
        TetrominoType,
    )
    from .engine import TetrisEngine
except ImportError:
    from models import (  # type: ignore
        ActivePiece,
        AIDecisionSnapshot,
        GameState,
        GameStatus,
        HardDropResult,
        ITetrisEngine,
        LineClearEvent,
        RotationIndex,
        TetrisEvents,
        TetrominoType,
    )
    from engine import TetrisEngine  # type: ignore

__all__ = [
    "TetrominoType",
    "RotationIndex",
    "GameStatus",
    "ActivePiece",
    "GameState",
    "HardDropResult",
    "LineClearEvent",
    "TetrisEvents",
    "ITetrisEngine",
    "TetrisEngine",
]
