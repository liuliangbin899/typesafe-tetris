"""
7-Bag Randomizer according to the Tetris Guideline.
Ensures every set of 7 pieces contains all 7 tetromino types without drought.
"""

from collections import deque
import random
from typing import Deque, List, Optional

try:
    from .models import TetrominoType
except ImportError:
    from models import TetrominoType  # type: ignore



ALL_PIECES: List[TetrominoType] = ['I', 'J', 'L', 'O', 'S', 'T', 'Z']


class SevenBagRandomizer:
    """
    7-Bag 随机发生器
    遵循官方规范：每次把 7 种不同方块打乱生成一个 bag 并加入队列，
    使方块出现频率极度均衡，绝不会出现长期没有 I 块（长条）或特定方块的情况。
    """

    def __init__(self, seed: Optional[int] = None, preview_count: int = 5) -> None:
        self._rng = random.Random(seed)
        self._preview_count = preview_count
        self._queue: Deque[TetrominoType] = deque()
        self._refill()
        self._refill()  # 预先补充两个 bag 保证预览充分

    def _refill(self) -> None:
        """生成一组新的 7 块并随机洗牌加入队列"""
        bag = list(ALL_PIECES)
        self._rng.shuffle(bag)
        self._queue.extend(bag)

    def next_piece(self) -> TetrominoType:
        """取出下一个方块，并保证队列充足"""
        if len(self._queue) <= self._preview_count + 1:
            self._refill()
        return self._queue.popleft()

    def get_preview(self, count: Optional[int] = None) -> List[TetrominoType]:
        """获取接下来 count 个预览方块（不消耗队列）"""
        n = count if count is not None else self._preview_count
        while len(self._queue) < n:
            self._refill()
        return list(list(self._queue)[:n])

    def reset(self, seed: Optional[int] = None) -> None:
        """重置发牌器"""
        if seed is not None:
            self._rng.seed(seed)
        self._queue.clear()
        self._refill()
        self._refill()
