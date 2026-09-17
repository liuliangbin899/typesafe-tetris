"""
Headless Tetris Core Engine Implementation.
100% decoupled from rendering libraries. Implements SRS, 7-Bag, Lock Delay, T-Spin, and Combo scoring.
"""

from collections import defaultdict
import copy
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

try:
    from .constants import (
        BACK_TO_BACK_MULTIPLIER,
        BOARD_HEIGHT,
        BOARD_WIDTH,
        BUFFER_ROWS,
        COLORS,
        COMBO_MULTIPLIER,
        ID_TO_PIECE,
        LOCK_DELAY_MS,
        MAX_LOCK_RESETS,
        PIECE_IDS,
        SCORE_TABLE,
        SHAPES,
        SPAWN_POSITIONS,
        TOTAL_ROWS,
        WALL_KICK_I,
        WALL_KICK_JLSTZ,
        get_fall_interval_ms,
    )
    from .models import (
        ActivePiece,
        GameOverEvent,
        GameState,
        GameStatus,
        HardDropResult,
        ITetrisEngine,
        LevelUpEvent,
        LineClearEvent,
        PieceEvent,
        RotationIndex,
        TetrisEvents,
        TetrominoType,
    )
    from .randomizer import SevenBagRandomizer
except ImportError:
    from constants import (  # type: ignore
        BACK_TO_BACK_MULTIPLIER,
        BOARD_HEIGHT,
        BOARD_WIDTH,
        BUFFER_ROWS,
        COLORS,
        COMBO_MULTIPLIER,
        ID_TO_PIECE,
        LOCK_DELAY_MS,
        MAX_LOCK_RESETS,
        PIECE_IDS,
        SCORE_TABLE,
        SHAPES,
        SPAWN_POSITIONS,
        TOTAL_ROWS,
        WALL_KICK_I,
        WALL_KICK_JLSTZ,
        get_fall_interval_ms,
    )
    from models import (  # type: ignore
        ActivePiece,
        GameOverEvent,
        GameState,
        GameStatus,
        HardDropResult,
        ITetrisEngine,
        LevelUpEvent,
        LineClearEvent,
        PieceEvent,
        RotationIndex,
        TetrisEvents,
        TetrominoType,
    )
    from randomizer import SevenBagRandomizer  # type: ignore



class TetrisEngine(ITetrisEngine):
    """
    俄罗斯方块核心引擎 (Headless Engine)
    纯数学网格状态机，提供完备的 API 与事件总线。
    """

    def __init__(self, random_seed: Optional[int] = None) -> None:
        self._randomizer = SevenBagRandomizer(seed=random_seed)
        self._status: GameStatus = GameStatus.IDLE

        # 棋盘网格：TOTAL_ROWS (24) 行 × BOARD_WIDTH (10) 列，0 表示空，1~7 表示方块 ID
        self._board: List[List[int]] = [[0] * BOARD_WIDTH for _ in range(TOTAL_ROWS)]

        self._current_piece: Optional[ActivePiece] = None
        self._hold_piece: Optional[TetrominoType] = None
        self._can_hold: bool = True

        self._score: int = 0
        self._lines: int = 0
        self._level: int = 1
        self._combo: int = -1
        self._back_to_back: bool = False

        # 计时器与锁定延迟状态
        self._fall_timer_ms: float = 0.0
        self._lock_timer_ms: float = 0.0
        self._is_touching_ground: bool = False
        self._lock_reset_count: int = 0

        # T-Spin 检测辅助标记
        self._last_action_rotate: bool = False
        self._last_rotate_kick_index: int = 0

        # 方块唯一自增序号计数器
        self._spawn_counter: int = 0

        # 事件总线订阅字典: event_name -> list of handlers
        self._event_handlers: Dict[str, List[Callable[[Any], None]]] = defaultdict(list)

    # ==========================================
    # === 1. 游戏生命周期控制 ===
    # ==========================================

    def start(self) -> None:
        """开始游戏"""
        self.restart()

    def pause(self) -> None:
        """暂停游戏"""
        if self._status == GameStatus.PLAYING:
            self._status = GameStatus.PAUSED

    def resume(self) -> None:
        """继续游戏"""
        if self._status == GameStatus.PAUSED:
            self._status = GameStatus.PLAYING

    def restart(self) -> None:
        """重新开始一局游戏"""
        self._board = [[0] * BOARD_WIDTH for _ in range(TOTAL_ROWS)]
        self._randomizer.reset()
        self._hold_piece = None
        self._can_hold = True
        self._score = 0
        self._lines = 0
        self._level = 1
        self._combo = -1
        self._back_to_back = False
        self._fall_timer_ms = 0.0
        self._lock_timer_ms = 0.0
        self._is_touching_ground = False
        self._lock_reset_count = 0
        self._last_action_rotate = False
        self._status = GameStatus.PLAYING

        self._spawn_next_piece()

    def tick(self, delta_time_ms: float) -> None:
        """驱动游戏时钟，处理自然下落与触底锁定延迟"""
        if self._status != GameStatus.PLAYING or self._current_piece is None:
            return

        fall_interval = get_fall_interval_ms(self._level)

        # 1. 检测当前是否处于触底悬空边缘
        is_grounded = self._check_collision(self._current_piece, offset_x=0, offset_y=1)
        self._is_touching_ground = is_grounded

        # 2. 如果已触底，累加锁定延迟计时器
        if is_grounded:
            self._lock_timer_ms += delta_time_ms
            if self._lock_timer_ms >= LOCK_DELAY_MS:
                # 锁定延迟时间到，将当前方块固化并消行
                self._lock_current_piece()
                return
        else:
            # 悬空状态，清空锁定计时器
            self._lock_timer_ms = 0.0

        # 3. 处理自然重力下落
        self._fall_timer_ms += delta_time_ms
        if self._fall_timer_ms >= fall_interval:
            self._fall_timer_ms -= fall_interval
            if not is_grounded:
                self._current_piece.y += 1
                self._last_action_rotate = False
                self._emit(TetrisEvents.PIECE_MOVE, PieceEvent(piece=self._current_piece))

    # ==========================================
    # === 2. 玩家操作指令 (Actions) ===
    # ==========================================

    def move_left(self) -> bool:
        """向左平移"""
        if not self._can_act():
            return False
        assert self._current_piece is not None
        if not self._check_collision(self._current_piece, offset_x=-1, offset_y=0):
            self._current_piece.x -= 1
            self._on_piece_manipulated()
            self._last_action_rotate = False
            self._emit(TetrisEvents.PIECE_MOVE, PieceEvent(piece=self._current_piece))
            return True
        return False

    def move_right(self) -> bool:
        """向右平移"""
        if not self._can_act():
            return False
        assert self._current_piece is not None
        if not self._check_collision(self._current_piece, offset_x=1, offset_y=0):
            self._current_piece.x += 1
            self._on_piece_manipulated()
            self._last_action_rotate = False
            self._emit(TetrisEvents.PIECE_MOVE, PieceEvent(piece=self._current_piece))
            return True
        return False

    def soft_drop(self) -> bool:
        """软降（下落一格并累加软降分数）"""
        if not self._can_act():
            return False
        assert self._current_piece is not None
        if not self._check_collision(self._current_piece, offset_x=0, offset_y=1):
            self._current_piece.y += 1
            self._score += SCORE_TABLE['SOFT_DROP_PER_CELL']
            self._fall_timer_ms = 0.0  # 重置自然下落计时器
            self._last_action_rotate = False
            self._emit(TetrisEvents.PIECE_MOVE, PieceEvent(piece=self._current_piece))
            return True
        else:
            # 已经触底，触底状态软降可加速锁定
            self._lock_timer_ms += 100.0
            return False

    def hard_drop(self) -> HardDropResult:
        """硬降：瞬间触底并立即锁定"""
        if not self._can_act():
            return HardDropResult(cells_dropped=0, lines_cleared=0, score_gained=0)
        assert self._current_piece is not None

        ghost_x, ghost_y = self.get_ghost_position()
        cells_dropped = ghost_y - self._current_piece.y

        self._current_piece.y = ghost_y
        drop_score = cells_dropped * SCORE_TABLE['HARD_DROP_PER_CELL']
        self._score += drop_score

        # 立即锁定
        lines_cleared, clear_score = self._lock_current_piece()
        return HardDropResult(
            cells_dropped=cells_dropped,
            lines_cleared=lines_cleared,
            score_gained=drop_score + clear_score,
        )

    def rotate_cw(self) -> bool:
        """顺时针旋转 (0 -> 1 -> 2 -> 3 -> 0)，带 SRS 踢墙测试"""
        return self._rotate(clockwise=True)

    def rotate_ccw(self) -> bool:
        """逆时针旋转 (0 -> 3 -> 2 -> 1 -> 0)，带 SRS 踢墙测试"""
        return self._rotate(clockwise=False)

    def hold(self) -> bool:
        """暂存当前方块"""
        if not self._can_act() or not self._can_hold:
            return False
        assert self._current_piece is not None

        current_type = self._current_piece.type

        if self._hold_piece is None:
            # 首次暂存：将当前放入 hold，生成下一个新块
            self._hold_piece = current_type
            self._spawn_next_piece()
        else:
            # 交换暂存：调出暂存块
            prev_hold = self._hold_piece
            self._hold_piece = current_type
            self._spawn_piece(prev_hold)

        self._can_hold = False
        return True

    # ==========================================
    # === 3. 查询接口 (Queries) ===
    # ==========================================

    def get_state(self) -> GameState:
        """获取当前全局状态快照"""
        ghost_y = self.get_ghost_position()[1] if self._current_piece else 0
        current_clone = self._current_piece.clone() if self._current_piece else None
        board_copy = [row[:] for row in self._board]

        return GameState(
            status=self._status,
            board=board_copy,
            current_piece=current_clone,
            ghost_y=ghost_y,
            next_queue=self._randomizer.get_preview(5),
            hold_piece=self._hold_piece,
            can_hold=self._can_hold,
            score=self._score,
            lines=self._lines,
            level=self._level,
            combo=self._combo,
            back_to_back=self._back_to_back,
        )

    def get_ghost_position(self) -> Tuple[int, int]:
        """计算幽灵块坐标 (x, y)"""
        if self._current_piece is None:
            return (0, 0)

        ghost_y = self._current_piece.y
        while not self._check_collision(self._current_piece, offset_x=0, offset_y=(ghost_y - self._current_piece.y + 1)):
            ghost_y += 1

        return (self._current_piece.x, ghost_y)

    # ==========================================
    # === 4. 事件总线接口 (Event Bus) ===
    # ==========================================

    def on(self, event_name: str, handler: Callable[[Any], None]) -> None:
        """注册事件监听器"""
        if handler not in self._event_handlers[event_name]:
            self._event_handlers[event_name].append(handler)

    def off(self, event_name: str, handler: Callable[[Any], None]) -> None:
        """注销事件监听器"""
        if handler in self._event_handlers[event_name]:
            self._event_handlers[event_name].remove(handler)

    def _emit(self, event_name: str, data: Any) -> None:
        """派发事件"""
        for handler in list(self._event_handlers[event_name]):
            handler(data)

    # ==========================================
    # === 5. 核心底层逻辑与算法实现 ===
    # ==========================================

    def _can_act(self) -> bool:
        return self._status == GameStatus.PLAYING and self._current_piece is not None

    def _on_piece_manipulated(self) -> None:
        """当玩家在触底期间成功进行了平移或旋转操作时，重置锁定计时"""
        if self._is_touching_ground:
            if self._lock_reset_count < MAX_LOCK_RESETS:
                self._lock_timer_ms = 0.0
                self._lock_reset_count += 1

    def _rotate_matrix(self, matrix: List[List[int]], clockwise: bool) -> List[List[int]]:
        """旋转方块矩阵"""
        if clockwise:
            # 顺时针旋转 90 度
            return [list(row) for row in zip(*matrix[::-1])]
        else:
            # 逆时针旋转 90 度
            return [list(row) for row in zip(*matrix)][::-1]

    def _rotate(self, clockwise: bool) -> bool:
        """执行带 SRS (Super Rotation System) 踢墙测试的旋转算法"""
        if not self._can_act():
            return False
        assert self._current_piece is not None

        piece = self._current_piece
        # 'O' 块各朝向完全对称，不需要真正旋转和踢墙
        if piece.type == 'O':
            return True

        from_rot = piece.rotation_index
        to_rot: RotationIndex = (from_rot + 1) % 4 if clockwise else (from_rot - 1) % 4  # type: ignore

        rotated_matrix = self._rotate_matrix(piece.matrix, clockwise=clockwise)

        # 获取踢墙偏移候选表
        kick_table = WALL_KICK_I if piece.type == 'I' else WALL_KICK_JLSTZ
        test_offsets = kick_table.get((from_rot, to_rot), [(0, 0)])

        # 依次测试 5 组踢墙偏移向量
        for kick_idx, (dx, dy) in enumerate(test_offsets):
            trial_piece = ActivePiece(
                type=piece.type,
                matrix=rotated_matrix,
                x=piece.x + dx,
                y=piece.y + dy,
                rotation_index=to_rot,
            )
            if not self._check_collision(trial_piece, offset_x=0, offset_y=0):
                # 成功找到有效落点，应用旋转与偏移
                piece.matrix = rotated_matrix
                piece.x += dx
                piece.y += dy
                piece.rotation_index = to_rot

                self._on_piece_manipulated()
                self._last_action_rotate = True
                self._last_rotate_kick_index = kick_idx

                self._emit(TetrisEvents.PIECE_MOVE, PieceEvent(piece=piece))
                return True

        # 全部 5 次测试均被阻挡，旋转失败
        return False

    def _check_collision(self, piece: ActivePiece, offset_x: int = 0, offset_y: int = 0) -> bool:
        """
        核心碰撞检测
        判断方块在加上偏移量后，是否与边界越界或与已固化方块重叠
        """
        for r_idx, row in enumerate(piece.matrix):
            for c_idx, val in enumerate(row):
                if val == 0:
                    continue
                board_x = piece.x + c_idx + offset_x
                board_y = piece.y + r_idx + offset_y

                # 横向越界检查 (0 <= x < BOARD_WIDTH)
                if board_x < 0 or board_x >= BOARD_WIDTH:
                    return True
                # 纵向越界检查 (y >= TOTAL_ROWS 触底)
                if board_y >= TOTAL_ROWS:
                    return True
                # 上方允许超出 (缓冲行上面)，但不允许 y < 0 且被其他阻挡
                if board_y < 0:
                    continue

                # 检查棋盘已有固化方块重叠
                if self._board[board_y][board_x] != 0:
                    return True

        return False

    def _spawn_next_piece(self) -> None:
        """从 7-Bag 发牌器取出下一个方块入场"""
        next_type = self._randomizer.next_piece()
        self._spawn_piece(next_type)

    def _spawn_piece(self, p_type: TetrominoType) -> None:
        """初始化生成指定类型的方块并检测是否发生 Block Out"""
        matrix = [row[:] for row in SHAPES[p_type]]
        spawn_x, spawn_y = SPAWN_POSITIONS[p_type]

        self._spawn_counter += 1
        piece = ActivePiece(
            type=p_type,
            matrix=matrix,
            x=spawn_x,
            y=spawn_y,
            rotation_index=0,
            spawn_id=self._spawn_counter,
        )

        # 重置单个方块周期状态
        self._current_piece = piece
        self._is_touching_ground = False
        self._lock_timer_ms = 0.0
        self._fall_timer_ms = 0.0
        self._lock_reset_count = 0
        self._last_action_rotate = False
        self._can_hold = True

        # 检测方块刚出生是否就发生重叠 (Block Out 游戏结束)
        if self._check_collision(piece, offset_x=0, offset_y=0):
            self._game_over()
            return

        self._emit(
            TetrisEvents.PIECE_SPAWN,
            PieceEvent(piece=piece, next_queue=self._randomizer.get_preview(5)),
        )

    def _detect_t_spin(self) -> Tuple[bool, bool]:
        """
        官方 3-Corner 规则检测 T-Spin 与 T-Spin Mini
        返回: (is_tspin, is_tspin_mini)
        """
        if self._current_piece is None or self._current_piece.type != 'T' or not self._last_action_rotate:
            return False, False

        px = self._current_piece.x
        py = self._current_piece.y

        # T 块中心点坐标为 (px + 1, py + 1)
        # 4 个对角点坐标：
        corners = [
            (px, py),         # 左上 (Top-Left)
            (px + 2, py),     # 右上 (Top-Right)
            (px, py + 2),     # 左下 (Bottom-Left)
            (px + 2, py + 2), # 右下 (Bottom-Right)
        ]

        occupied_count = 0
        for cx, cy in corners:
            # 边界外或者已有方块均计为 occupied
            if cx < 0 or cx >= BOARD_WIDTH or cy >= TOTAL_ROWS or (cy >= 0 and self._board[cy][cx] != 0):
                occupied_count += 1

        # 3-Corner 规则：至少 3 个对角被占据
        if occupied_count < 3:
            return False, False

        # 判断是否为 T-Spin Mini: 如果使用的是常规旋转且正面两个角中只有一个被占据，则为 Mini
        # 简化标准：若使用了第 5 踢墙（1 或 2 号大位移），视为 Regular T-Spin
        is_mini = (self._last_rotate_kick_index < 4) and (occupied_count == 3)
        return True, is_mini

    def _lock_current_piece(self) -> Tuple[int, int]:
        """
        将活动方块固化写入棋盘，执行消行检测、计分计算并生成下一个方块
        返回: (lines_cleared_count, score_gained)
        """
        if self._current_piece is None:
            return 0, 0

        piece = self._current_piece
        piece_id = PIECE_IDS[piece.type]

        # 1. 检查 Lock Out：如果整块方块全在可见棋盘上方 (y < BUFFER_ROWS)，即为 Lock Out Game Over
        locked_above_buffer = True
        for r_idx, row in enumerate(piece.matrix):
            for c_idx, val in enumerate(row):
                if val != 0:
                    board_y = piece.y + r_idx
                    if board_y >= BUFFER_ROWS:
                        locked_above_buffer = False

        if locked_above_buffer:
            self._game_over()
            return 0, 0

        # 2. 检测 T-Spin
        is_tspin, is_tspin_mini = self._detect_t_spin()

        # 3. 固化写入棋盘
        for r_idx, row in enumerate(piece.matrix):
            for c_idx, val in enumerate(row):
                if val != 0:
                    board_x = piece.x + c_idx
                    board_y = piece.y + r_idx
                    if 0 <= board_x < BOARD_WIDTH and 0 <= board_y < TOTAL_ROWS:
                        self._board[board_y][board_x] = piece_id

        self._emit(TetrisEvents.PIECE_LOCK, PieceEvent(piece=piece))

        # 4. 检测消行
        cleared_lines_indices: List[int] = []
        for r in range(TOTAL_ROWS):
            if all(self._board[r][c] != 0 for c in range(BOARD_WIDTH)):
                cleared_lines_indices.append(r)

        line_count = len(cleared_lines_indices)

        # 5. 执行消行并下落上方行
        if line_count > 0:
            new_board: List[List[int]] = [[0] * BOARD_WIDTH for _ in range(line_count)]
            for r in range(TOTAL_ROWS):
                if r not in cleared_lines_indices:
                    new_board.append(self._board[r])
            self._board = new_board

        # 6. 检测 Perfect Clear (全清全空)
        is_perfect_clear = all(
            self._board[r][c] == 0 for r in range(TOTAL_ROWS) for c in range(BOARD_WIDTH)
        )

        # 7. 计分结算与 Back-to-Back、Combo 状态流转
        score_gained = 0
        action_type = ""

        if is_tspin:
            if line_count == 0:
                action_type = 'TSPIN_MINI_NO_LINE' if is_tspin_mini else 'TSPIN_NO_LINE'
            elif line_count == 1:
                action_type = 'TSPIN_MINI_SINGLE' if is_tspin_mini else 'TSPIN_SINGLE'
            elif line_count == 2:
                action_type = 'TSPIN_DOUBLE'
            elif line_count == 3:
                action_type = 'TSPIN_TRIPLE'
        else:
            if line_count == 1:
                action_type = 'SINGLE'
            elif line_count == 2:
                action_type = 'DOUBLE'
            elif line_count == 3:
                action_type = 'TRIPLE'
            elif line_count == 4:
                action_type = 'TETRIS'

        if action_type in SCORE_TABLE:
            base_score = SCORE_TABLE[action_type] * self._level

            # 判定 Back-to-Back (四消 Tetris 或 T-Spin 清行)
            is_difficult_action = (line_count == 4) or (is_tspin and line_count > 0)
            if is_difficult_action:
                if self._back_to_back:
                    base_score = int(base_score * BACK_TO_BACK_MULTIPLIER)
                self._back_to_back = True
            elif line_count > 0:
                # 产生普通消行，打断 B2B
                self._back_to_back = False

            score_gained += base_score

        # 连击 Combo 奖励
        if line_count > 0:
            self._combo += 1
            if self._combo > 0:
                combo_bonus = COMBO_MULTIPLIER * self._combo * self._level
                score_gained += combo_bonus
        else:
            self._combo = -1

        # 全清 Perfect Clear 额外奖励
        if is_perfect_clear and line_count > 0:
            pc_key = f'PERFECT_CLEAR_{["SINGLE", "DOUBLE", "TRIPLE", "TETRIS"][min(line_count, 4) - 1]}'
            score_gained += SCORE_TABLE.get(pc_key, 1000) * self._level

        self._score += score_gained

        # 8. 累计总消行数与等级提升 (每消除 10 行升 1 级)
        prev_level = self._level
        self._lines += line_count
        self._level = max(1, (self._lines // 10) + 1)

        # 触发消行事件
        if line_count > 0:
            self._emit(
                TetrisEvents.LINE_CLEAR,
                LineClearEvent(
                    cleared_lines=cleared_lines_indices,
                    line_count=line_count,
                    score_gained=score_gained,
                    is_tspin=is_tspin,
                    is_tspin_mini=is_tspin_mini,
                    is_back_to_back=self._back_to_back,
                    combo=max(0, self._combo),
                    is_perfect_clear=is_perfect_clear,
                ),
            )

        # 触发升级事件
        if self._level > prev_level:
            self._emit(
                TetrisEvents.LEVEL_UP,
                LevelUpEvent(new_level=self._level, fall_interval_ms=get_fall_interval_ms(self._level)),
            )

        # 9. 生成下一个活动方块
        self._spawn_next_piece()
        return line_count, score_gained

    def _game_over(self) -> None:
        """处理游戏结束"""
        self._status = GameStatus.GAME_OVER
        self._current_piece = None
        self._emit(
            TetrisEvents.GAME_OVER,
            GameOverEvent(final_score=self._score, total_lines=self._lines),
        )
