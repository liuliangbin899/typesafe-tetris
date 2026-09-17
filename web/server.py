"""
FastAPI & WebSocket Backend Server for TypeSafe Tetris Web Dashboard.
Manages headless engine loop, TypeSafe AI AutoPilot, and real-time state synchronization.
"""

import asyncio
import os
from typing import Any, Dict, List, Optional, Set
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from ..engine import TetrisEngine
    from ..ai.typesafe_agent import TypeSafeTetrisAgent
    from ..ai.planner import ActionPlanner
    from ..models import GameState, GameStatus
except (ImportError, ValueError):
    from engine import TetrisEngine
    from ai.typesafe_agent import TypeSafeTetrisAgent
    from ai.planner import ActionPlanner
    from models import GameState, GameStatus


PRESET_QUESTIONS: List[str] = [
    "稳扎稳打平稳通关",
    "全力组织Tetris大招",
    "极致消行冲刺高分",
    "绝境极限降高求生",
]


import time

class GameServerManager:
    """管理后台游戏引擎循环与 WebSocket 连接广播"""

    def __init__(self) -> None:
        self.engine = TetrisEngine()
        self.agent = TypeSafeTetrisAgent()
        self.q_index: int = 0
        self.agent.set_question(PRESET_QUESTIONS[self.q_index])

        self.auto_pilot: bool = True
        self.ai_actions_queue: List[str] = []
        self.ai_step_timer_ms: float = 0.0
        self.ai_step_interval_ms: float = 40.0  # Web 端动作执行间隔 (平滑流畅)
        self.last_evaluated_fingerprint: Optional[tuple] = None
        self.last_decision_latency_ms: float = 12.5  # 最近一次 TypeSafe 推理延迟

        self.active_connections: Set[WebSocket] = set()
        self.is_running: bool = False
        self.current_decision_snapshot: Optional[Any] = None


        # 启动引擎
        self.engine.start()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.add(websocket)
        # 立即推送首帧
        await self.send_state(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self.active_connections.discard(websocket)

    def handle_command(self, cmd: str, payload: Optional[Any] = None) -> None:
        """处理来自前端的控制指令"""
        state = self.engine.get_state()

        if cmd == "TOGGLE_AUTOPILOT":
            self.auto_pilot = not self.auto_pilot
            self.ai_actions_queue.clear()
            self.last_evaluated_fingerprint = None
        elif cmd == "CYCLE_QUESTION":
            self.q_index = (self.q_index + 1) % len(PRESET_QUESTIONS)
            self.agent.set_question(PRESET_QUESTIONS[self.q_index])
            self.ai_actions_queue.clear()
            self.last_evaluated_fingerprint = None
        elif cmd == "SET_QUESTION":
            if isinstance(payload, str) and payload.strip():
                self.agent.set_question(payload.strip())
                self.ai_actions_queue.clear()
                self.last_evaluated_fingerprint = None
        elif cmd == "RESTART":
            self.engine.restart()
            self.ai_actions_queue.clear()
            self.last_evaluated_fingerprint = None
        elif cmd == "PAUSE_TOGGLE":
            if state.status == GameStatus.PLAYING:
                self.engine.pause()
            elif state.status == GameStatus.PAUSED:
                self.engine.resume()
        elif cmd == "SET_AI_SPEED":
            if isinstance(payload, (int, float)) and payload >= 0:
                self.ai_step_interval_ms = float(payload)
        elif cmd == "ACTION" and isinstance(payload, str):
            # 手动动作指令：若处于自动驾驶状态，操作时自动平滑切至手动模式接管
            if self.auto_pilot:
                self.auto_pilot = False
                self.ai_actions_queue.clear()

            if payload == "MOVE_LEFT":
                self.engine.move_left()
            elif payload == "MOVE_RIGHT":
                self.engine.move_right()
            elif payload == "ROTATE_CW":
                self.engine.rotate_cw()
            elif payload == "ROTATE_CCW":
                self.engine.rotate_ccw()
            elif payload == "SOFT_DROP":
                self.engine.soft_drop()
            elif payload == "HARD_DROP":
                self.engine.hard_drop()
            elif payload == "HOLD":
                self.engine.hold()


    def serialize_state(self) -> Dict[str, Any]:
        """打包前端所需的全部棋盘、方块、AI 决策与全量概率数据"""
        state = self.engine.get_state()
        ghost_x, ghost_y = self.engine.get_ghost_position()

        # 棋盘网格提取 (24x10，包含顶部 4 行缓冲)
        board_data = state.board

        # 当前活动方块
        current_data = None
        if state.current_piece:
            p = state.current_piece
            current_data = {
                "type": p.type,
                "x": p.x,
                "y": p.y,
                "rotation_index": p.rotation_index,
                "matrix": p.matrix,
                "spawn_id": p.spawn_id,
            }

        # AI 决策快照序列化
        ai_data = None
        if self.current_decision_snapshot:
            snap = self.current_decision_snapshot
            ai_data = {
                "question": snap.question,
                "is_crisis_danger": snap.is_crisis_danger,
                "crisis_prob": snap.crisis_prob,
                "should_hold": snap.should_hold,
                "hold_prob": snap.hold_prob,
                "tactic_mode": snap.tactic_mode,
                "tactic_confidence": snap.tactic_confidence,
                "tactic_probabilities": snap.tactic_probabilities,
                "selected_candidate_id": snap.selected_candidate_id,
                "placement_confidence": snap.placement_confidence,
                "selected_candidate_summary": snap.selected_candidate_summary,
                "target_placement_coords": snap.target_placement_coords,
                "candidate_probabilities": snap.candidate_probabilities,
                "candidates_detail": [
                    {
                        "id": c.id,
                        "rotation_index": c.rotation_index,
                        "target_x": c.target_x,
                        "target_y": c.target_y,
                        "lines_cleared": c.lines_cleared,
                        "resulting_holes": c.resulting_holes,
                        "height_diff": c.height_diff,
                        "probability": c.probability,
                        "is_chosen": c.is_chosen,
                        "summary": c.summary,
                    }
                    for c in snap.candidates_detail
                ],
                "board_health": snap.board_health,
                "score_confidence": snap.score_confidence,
                "score_probabilities": snap.score_probabilities,
                "score_legend": snap.score_legend,
                "raw_state": snap.raw_state,
                "question_instructions": snap.question_instructions,
                "summary_text": snap.summary_text,
                "decision_latency_ms": self.last_decision_latency_ms,
            }

        return {
            "status": state.status.name,
            "score": state.score,
            "lines": state.lines,
            "level": state.level,
            "combo": state.combo,
            "back_to_back": state.back_to_back,
            "can_hold": state.can_hold,
            "hold_piece": state.hold_piece,
            "next_queue": state.next_queue[:3],
            "board": board_data,
            "current_piece": current_data,
            "ghost_pos": {"x": ghost_x, "y": ghost_y},
            "auto_pilot": self.auto_pilot,
            "decision_latency_ms": self.last_decision_latency_ms,
            "ai_step_interval_ms": self.ai_step_interval_ms,
            "preset_questions": PRESET_QUESTIONS,
            "current_q_index": self.q_index,
            "current_question": self.agent.current_question,
            "ai_decision": ai_data,
        }

    async def send_state(self, websocket: WebSocket) -> None:
        try:
            await websocket.send_json(self.serialize_state())
        except Exception:
            pass

    async def broadcast(self) -> None:
        if not self.active_connections:
            return
        data = self.serialize_state()
        dead = []
        for ws in self.active_connections:
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

    def tick(self, dt_ms: float) -> None:
        """核心物理与 AI 决策驱动"""
        self.engine.tick(dt_ms)
        state = self.engine.get_state()

        if state.status == GameStatus.PLAYING and state.current_piece is not None:
            piece_fingerprint = (state.current_piece.spawn_id, self.q_index)
            if piece_fingerprint != self.last_evaluated_fingerprint:
                self.last_evaluated_fingerprint = piece_fingerprint
                t0 = time.perf_counter()
                chosen, snap = self.agent.decide(state)
                self.last_decision_latency_ms = round((time.perf_counter() - t0) * 1000.0, 1)
                self.current_decision_snapshot = snap

                if self.auto_pilot and chosen is not None:
                    if snap.should_hold and state.can_hold:
                        self.ai_actions_queue = ['HOLD']
                    else:
                        self.ai_actions_queue = ActionPlanner.plan_actions(state.current_piece, chosen)
                    self.ai_step_timer_ms = 0.0

            # 消费自动驾驶队列
            if self.auto_pilot and self.ai_actions_queue:
                self.ai_step_timer_ms += dt_ms
                if self.ai_step_timer_ms >= self.ai_step_interval_ms:
                    self.ai_step_timer_ms = 0.0
                    action = self.ai_actions_queue.pop(0)
                    ActionPlanner.execute_action(self.engine, action)


from contextlib import asynccontextmanager


async def game_loop():
    """60FPS 后台游戏主循环"""
    dt_sec = 1.0 / 60.0
    dt_ms = dt_sec * 1000.0
    while True:
        manager.tick(dt_ms)
        await manager.broadcast()
        await asyncio.sleep(dt_sec)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(game_loop())
    yield
    task.cancel()


# 创建 FastAPI 实例
manager = GameServerManager()
app = FastAPI(title="TypeSafe Tetris Live Dashboard", lifespan=lifespan)

static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.api_route("/", methods=["GET", "HEAD"])
async def get_index():
    return FileResponse(os.path.join(static_dir, "index.html"))


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            cmd = data.get("cmd")
            payload = data.get("payload")
            if cmd:
                manager.handle_command(cmd, payload)
                await manager.broadcast()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)

