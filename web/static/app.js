/**
 * TypeSafe AI Tetris - Ultra-Crisp Modern Web Dashboard Client
 * Handles Retina 2x Canvas rendering, WebSocket real-time frame syncing,
 * and interactive strategy controls.
 */

// 方块调色盘
const PIECE_COLORS = {
  I: { fill: "#00dceb", light: "#5ff2fc", dark: "#009ea8" },
  J: { fill: "#2173f3", light: "#629cf5", dark: "#124fb3" },
  L: { fill: "#ff8c00", light: "#ffa938", dark: "#b86500" },
  O: { fill: "#ffd700", light: "#ffe552", dark: "#b89a00" },
  S: { fill: "#2ecc71", light: "#60df95", dark: "#1e8a4b" },
  T: { fill: "#9b59b6", light: "#b779ce", dark: "#6f3e84" },
  Z: { fill: "#e74c3c", light: "#f07769", dark: "#ab2e20" },
};

const ID_TO_TYPE = {
  1: "I", 2: "J", 3: "L", 4: "O", 5: "S", 6: "T", 7: "Z"
};

const TACTIC_NAMES = {
  FLATTEN: "填平底盘",
  BUILD_TETRIS: "积攒4消",
  SCORE_ATTACK: "贪心进攻",
  SURVIVAL: "紧急避险",
};

class TetrisWebDashboard {
  constructor() {
    this.ws = null;
    this.currentState = null;
    
    // 初始化 Canvas
    this.boardCanvas = document.getElementById("tetrisCanvas");
    this.boardCtx = this.setupRetinaCanvas(this.boardCanvas, 300, 600);
    
    this.holdCanvas = document.getElementById("holdCanvas");
    this.holdCtx = this.setupRetinaCanvas(this.holdCanvas, 100, 70);

    this.nextCanvases = [
      this.setupRetinaCanvas(document.getElementById("nextCanvas0"), 80, 50),
      this.setupRetinaCanvas(document.getElementById("nextCanvas1"), 80, 50),
      this.setupRetinaCanvas(document.getElementById("nextCanvas2"), 80, 50),
    ];

    this.bindEvents();
    this.connectWebSocket();
  }

  setupRetinaCanvas(canvas, cssWidth, cssHeight) {
    const dpr = window.devicePixelRatio || 2;
    canvas.width = cssWidth * dpr;
    canvas.height = cssHeight * dpr;
    canvas.style.width = `${cssWidth}px`;
    canvas.style.height = `${cssHeight}px`;
    const ctx = canvas.getContext("2d");
    ctx.scale(dpr, dpr);
    return ctx;
  }

  connectWebSocket() {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    
    const wsStatus = document.getElementById("wsStatus");
    const statusText = wsStatus.querySelector(".status-text");

    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      wsStatus.classList.add("connected");
      statusText.innerText = "实时已连接 (60 FPS)";
    };

    this.ws.onmessage = (event) => {
      try {
        const state = JSON.parse(event.data);
        this.currentState = state;
        this.renderAll(state);
      } catch (err) {
        console.error("Frame parse error:", err);
      }
    };

    this.ws.onclose = () => {
      wsStatus.classList.remove("connected");
      statusText.innerText = "连接中断，重连中...";
      setTimeout(() => this.connectWebSocket(), 1000);
    };

    this.ws.onerror = () => {
      this.ws.close();
    };
  }

  sendCommand(cmd, payload = null) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ cmd, payload }));
    }
  }

  bindEvents() {
    // 1. 模式分段选择器 (支持鼠标直接点击切换)
    const segBtnManual = document.getElementById("segBtnManual");
    const segBtnAi = document.getElementById("segBtnAi");
    if (segBtnManual && segBtnAi) {
      segBtnManual.addEventListener("click", () => {
        if (this.currentState && this.currentState.auto_pilot) {
          this.sendCommand("TOGGLE_AUTOPILOT");
        }
      });
      segBtnAi.addEventListener("click", () => {
        if (this.currentState && !this.currentState.auto_pilot) {
          this.sendCommand("TOGGLE_AUTOPILOT");
        }
      });
    }

    // 2. 顶栏策略下拉菜单
    const strategyDropdown = document.getElementById("strategyDropdown");
    const btnStrategyTrigger = document.getElementById("btnStrategyDropdown");
    if (btnStrategyTrigger && strategyDropdown) {
      btnStrategyTrigger.addEventListener("click", (e) => {
        e.stopPropagation();
        strategyDropdown.classList.toggle("open");
      });

      // 点击外部区域关闭下拉菜单
      document.addEventListener("click", (e) => {
        if (!strategyDropdown.contains(e.target)) {
          strategyDropdown.classList.remove("open");
        }
      });
    }

    // 顶栏策略菜单项点击
    const menuItems = document.querySelectorAll(".strategy-menu .menu-item");
    menuItems.forEach((item) => {
      item.addEventListener("click", () => {
        const val = item.getAttribute("data-value");
        if (val) {
          this.sendCommand("SET_QUESTION", val);
          if (strategyDropdown) strategyDropdown.classList.remove("open");
        }
      });
    });

    // 3. 第 3 栏策略下拉选择组件 (鼠标选择 / change 事件)
    const strategySelect = document.getElementById("strategySelect");
    if (strategySelect) {
      strategySelect.addEventListener("change", (e) => {
        const val = e.target.value;
        if (val) {
          this.sendCommand("SET_QUESTION", val);
        }
      });
    }

    // 4. AI 运行速度分段调节器点击
    const speedBtns = document.querySelectorAll(".speed-btn");
    speedBtns.forEach((btn) => {
      btn.addEventListener("click", () => {
        const speed = parseFloat(btn.getAttribute("data-speed"));
        if (!isNaN(speed)) {
          this.sendCommand("SET_AI_SPEED", speed);
        }
      });
    });

    // 5. 屏幕手动操控手柄 (Virtual Gamepad) 按钮点击
    const padBtns = document.querySelectorAll(".pad-btn");
    padBtns.forEach((btn) => {
      const action = btn.getAttribute("data-action");
      if (action) {
        btn.addEventListener("click", (e) => {
          e.preventDefault();
          this.sendCommand("ACTION", action);
        });
      }
    });

    // 暂停
    document.getElementById("btnPause").addEventListener("click", () => {
      this.sendCommand("PAUSE_TOGGLE");
    });

    // 重开
    document.getElementById("btnRestart").addEventListener("click", () => {
      this.sendCommand("RESTART");
    });

    // 弹窗按键
    document.getElementById("overlayBtn").addEventListener("click", () => {
      if (this.currentState && this.currentState.status === "GAME_OVER") {
        this.sendCommand("RESTART");
      } else {
        this.sendCommand("PAUSE_TOGGLE");
      }
    });

    // 全局键盘监听
    window.addEventListener("keydown", (e) => {
      if (e.target.tagName === "INPUT" || e.target.tagName === "SELECT") return;

      const keyMap = {
        "KeyA": () => this.sendCommand("TOGGLE_AUTOPILOT"),
        "KeyM": () => this.sendCommand("TOGGLE_AUTOPILOT"),
        "KeyQ": () => this.sendCommand("CYCLE_QUESTION"),
        "KeyP": () => this.sendCommand("PAUSE_TOGGLE"),
        "KeyR": () => this.sendCommand("RESTART"),
        "Space": () => this.sendCommand("ACTION", "HARD_DROP"),
        "ArrowLeft": () => this.sendCommand("ACTION", "MOVE_LEFT"),
        "ArrowRight": () => this.sendCommand("ACTION", "MOVE_RIGHT"),
        "ArrowDown": () => this.sendCommand("ACTION", "SOFT_DROP"),
        "ArrowUp": () => this.sendCommand("ACTION", "ROTATE_CW"),
        "KeyX": () => this.sendCommand("ACTION", "ROTATE_CW"),
        "KeyZ": () => this.sendCommand("ACTION", "ROTATE_CCW"),
        "KeyC": () => this.sendCommand("ACTION", "HOLD"),
      };

      if (keyMap[e.code]) {
        e.preventDefault();
        keyMap[e.code]();
      }
    });
  }

  // =========================================================================
  // 主渲染流程
  // =========================================================================

  renderAll(state) {
    this.renderTopControls(state);
    this.renderBoard(state);
    this.renderPreviews(state);
    this.renderStats(state);
    this.renderInputStatePanel(state);
    this.renderDecisionDashboard(state);
    this.renderOverlay(state);
  }

  renderTopControls(state) {
    // 1. 实时推理延迟更新 (Inference Latency)
    const latency = state.decision_latency_ms !== undefined ? state.decision_latency_ms : (state.ai_decision?.decision_latency_ms || 12.5);
    const navLatencyVal = document.getElementById("navLatencyVal");
    if (navLatencyVal) {
      navLatencyVal.innerText = `${latency} ms`;
    }
    const agentLatencyVal = document.getElementById("agentLatencyVal");
    if (agentLatencyVal) {
      agentLatencyVal.innerText = `${latency} ms`;
    }

    // 2. 模式分段选择器高亮
    const segBtnManual = document.getElementById("segBtnManual");
    const segBtnAi = document.getElementById("segBtnAi");
    if (segBtnManual && segBtnAi) {
      if (state.auto_pilot) {
        segBtnAi.classList.add("active");
        segBtnManual.classList.remove("active");
      } else {
        segBtnManual.classList.add("active");
        segBtnAi.classList.remove("active");
      }
    }

    // 3. AI 执行速度按钮高亮同步
    const currentInterval = state.ai_step_interval_ms !== undefined ? state.ai_step_interval_ms : 40;
    const speedBtns = document.querySelectorAll(".speed-btn");
    speedBtns.forEach((btn) => {
      const s = parseFloat(btn.getAttribute("data-speed"));
      if (Math.abs(s - currentInterval) < 5) {
        btn.classList.add("active");
      } else {
        btn.classList.remove("active");
      }
    });

    // 4. 顶栏当前策略显示与下拉勾选同步
    const topStrategyName = document.getElementById("topStrategyName");
    if (topStrategyName) {
      topStrategyName.innerText = state.current_question || "稳扎稳打平稳通关";
    }

    const menuItems = document.querySelectorAll(".strategy-menu .menu-item");
    menuItems.forEach((item) => {
      if (item.getAttribute("data-value") === state.current_question) {
        item.classList.add("active");
      } else {
        item.classList.remove("active");
      }
    });

    const badgePill = document.getElementById("agentBadgePill");
    if (badgePill) {
      badgePill.innerText = state.auto_pilot ? "🟢 自动驾驶托管中" : "⚪ 人类操控 · AI 辅助中";
    }

    const boardBadge = document.getElementById("badgeText");
    if (boardBadge) {
      boardBadge.innerText = state.auto_pilot ? "● 🤖 TypeSafe AI 托管中" : "○ 👤 人类操控中 (按 M 键切 AI)";
    }
  }


  renderBoard(state) {
    const ctx = this.boardCtx;
    const width = 300;
    const height = 600;
    const cellSize = 30;

    // 清空背景
    ctx.fillStyle = "#07090f";
    ctx.fillRect(0, 0, width, height);

    // 绘制高精网格细线
    ctx.strokeStyle = "rgba(25, 34, 52, 0.45)";
    ctx.lineWidth = 1;
    for (let c = 1; c < 10; c++) {
      ctx.beginPath();
      ctx.moveTo(c * cellSize, 0);
      ctx.lineTo(c * cellSize, height);
      ctx.stroke();
    }
    for (let r = 1; r < 20; r++) {
      ctx.beginPath();
      ctx.moveTo(0, r * cellSize);
      ctx.lineTo(width, r * cellSize);
      ctx.stroke();
    }

    // 1. 固化方块 (略过顶部 4 行缓冲)
    const board = state.board;
    for (let r = 4; r < 24; r++) {
      const vr = r - 4;
      for (let c = 0; c < 10; c++) {
        const id = board[r][c];
        if (id !== 0) {
          const type = ID_TO_TYPE[id] || "T";
          this.drawBlock(ctx, c * cellSize, vr * cellSize, cellSize, PIECE_COLORS[type]);
        }
      }
    }

    // 2. TypeSafe AI 目标落点虚线透视框 (AI Target Ghost)
    if (state.ai_decision && state.ai_decision.target_placement_coords && state.current_piece) {
      const [tx, ty, rot] = state.ai_decision.target_placement_coords;
      const matrix = state.current_piece.matrix;
      // 旋转矩阵
      const rotMatrix = this.rotateMatrix(matrix, rot);
      for (let r = 0; r < rotMatrix.length; r++) {
        for (let c = 0; c < rotMatrix[r].length; c++) {
          if (rotMatrix[r][c] !== 0) {
            const by = ty + r;
            const bx = tx + c;
            if (by >= 4) {
              this.drawTargetGhost(ctx, bx * cellSize, (by - 4) * cellSize, cellSize);
            }
          }
        }
      }
    }

    // 3. 物理自然幽灵块 (Natural Ghost)
    if (state.current_piece && state.ghost_pos) {
      const p = state.current_piece;
      const gy = state.ghost_pos.y;
      const color = PIECE_COLORS[p.type] || PIECE_COLORS.T;
      for (let r = 0; r < p.matrix.length; r++) {
        for (let c = 0; c < p.matrix[r].length; c++) {
          if (p.matrix[r][c] !== 0) {
            const by = gy + r;
            const bx = p.x + c;
            if (by >= 4) {
              this.drawGhostBlock(ctx, bx * cellSize, (by - 4) * cellSize, cellSize, color.fill);
            }
          }
        }
      }
    }

    // 4. 当前活动方块
    if (state.current_piece) {
      const p = state.current_piece;
      const color = PIECE_COLORS[p.type] || PIECE_COLORS.T;
      for (let r = 0; r < p.matrix.length; r++) {
        for (let c = 0; c < p.matrix[r].length; c++) {
          if (p.matrix[r][c] !== 0) {
            const by = p.y + r;
            const bx = p.x + c;
            if (by >= 4) {
              this.drawBlock(ctx, bx * cellSize, (by - 4) * cellSize, cellSize, color);
            }
          }
        }
      }
    }
  }

  drawBlock(ctx, x, y, size, color) {
    const pad = 1;
    const r = 4;
    const w = size - pad * 2;
    const h = size - pad * 2;

    ctx.fillStyle = color.fill;
    this.roundRect(ctx, x + pad, y + pad, w, h, r);
    ctx.fill();

    // 顶部与左侧立体微光
    ctx.strokeStyle = color.light;
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(x + pad + 2, y + pad + h - 3);
    ctx.lineTo(x + pad + 2, y + pad + 2);
    ctx.lineTo(x + pad + w - 3, y + pad + 2);
    ctx.stroke();

    // 底部与右侧阴影
    ctx.strokeStyle = color.dark;
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(x + pad + w - 2, y + pad + 3);
    ctx.lineTo(x + pad + w - 2, y + pad + h - 2);
    ctx.lineTo(x + pad + 3, y + pad + h - 2);
    ctx.stroke();
  }

  drawGhostBlock(ctx, x, y, size, colorHex) {
    ctx.strokeStyle = colorHex;
    ctx.lineWidth = 1.5;
    ctx.fillStyle = "rgba(0, 0, 0, 0.2)";
    this.roundRect(ctx, x + 2, y + 2, size - 4, size - 4, 3);
    ctx.stroke();
  }

  drawTargetGhost(ctx, x, y, size) {
    ctx.save();
    ctx.strokeStyle = "#00dceb";
    ctx.lineWidth = 2;
    ctx.setLineDash([4, 3]);
    ctx.fillStyle = "rgba(0, 220, 235, 0.12)";
    this.roundRect(ctx, x + 2, y + 2, size - 4, size - 4, 3);
    ctx.fill();
    ctx.stroke();
    ctx.restore();
  }

  roundRect(ctx, x, y, width, height, radius) {
    ctx.beginPath();
    ctx.moveTo(x + radius, y);
    ctx.lineTo(x + width - radius, y);
    ctx.quadraticCurveTo(x + width, y, x + width, y + radius);
    ctx.lineTo(x + width, y + height - radius);
    ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
    ctx.lineTo(x + radius, y + height);
    ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
    ctx.lineTo(x, y + radius);
    ctx.quadraticCurveTo(x, y, x + radius, y);
    ctx.closePath();
  }

  rotateMatrix(matrix, rotCount) {
    let curr = matrix.map(row => [...row]);
    const times = (rotCount % 4 + 4) % 4;
    for (let t = 0; t < times; t++) {
      const rows = curr.length;
      const cols = curr[0].length;
      const res = [];
      for (let c = 0; c < cols; c++) {
        res[c] = [];
        for (let r = 0; r < rows; r++) {
          res[c][r] = curr[rows - 1 - r][c];
        }
      }
      curr = res;
    }
    return curr;
  }

  renderPreviews(state) {
    // 渲染 HOLD
    this.renderSinglePreview(this.holdCtx, state.hold_piece, 100, 70, 16);

    // 渲染 NEXT 3
    if (state.next_queue) {
      for (let i = 0; i < 3; i++) {
        this.renderSinglePreview(this.nextCanvases[i], state.next_queue[i], 80, 50, 14);
      }
    }
  }

  renderSinglePreview(ctx, pieceType, width, height, cellSize) {
    ctx.clearRect(0, 0, width, height);
    if (!pieceType) return;

    const shapes = {
      I: [[1, 1, 1, 1]],
      O: [[1, 1], [1, 1]],
      T: [[0, 1, 0], [1, 1, 1]],
      L: [[0, 0, 1], [1, 1, 1]],
      J: [[1, 0, 0], [1, 1, 1]],
      S: [[0, 1, 1], [1, 1, 0]],
      Z: [[1, 1, 0], [0, 1, 1]],
    };

    const m = shapes[pieceType] || [[1]];
    const color = PIECE_COLORS[pieceType] || PIECE_COLORS.T;
    const pW = m[0].length * cellSize;
    const pH = m.length * cellSize;
    const startX = Math.round((width - pW) / 2);
    const startY = Math.round((height - pH) / 2);

    for (let r = 0; r < m.length; r++) {
      for (let c = 0; c < m[r].length; c++) {
        if (m[r][c] !== 0) {
          this.drawBlock(ctx, startX + c * cellSize, startY + r * cellSize, cellSize, color);
        }
      }
    }
  }

  renderStats(state) {
    document.getElementById("valScore").innerText = Number(state.score).toLocaleString();
    document.getElementById("valLines").innerText = `${state.lines} 行`;
    document.getElementById("valLevel").innerText = `${state.level} 级`;
    document.getElementById("valCombo").innerText = `${Math.max(0, state.combo)} Combo`;
  }

  // =========================================================================
  // TypeSafe 输入端 & 输出端渲染
  // =========================================================================

  renderInputStatePanel(state) {
    // 渲染激活的自然语言 Question & 同步策略下拉菜单
    const qText = state.current_question || "稳扎稳打平稳通关";
    const activeTextEl = document.getElementById("activeQuestionText");
    if (activeTextEl) {
      activeTextEl.innerText = `"${qText}"`;
    }

    const strategySelect = document.getElementById("strategySelect");
    if (strategySelect && strategySelect.value !== qText) {
      strategySelect.value = qText;
    }

    // 渲染高亮 State JSON 树
    if (state.ai_decision && state.ai_decision.raw_state) {
      const raw = state.ai_decision.raw_state;
      const formatted = JSON.stringify(raw, null, 2);
      const jsonEl = document.getElementById("jsonStateContent");
      if (jsonEl) {
        jsonEl.innerHTML = this.syntaxHighlight(formatted);
      }
    }
  }


  syntaxHighlight(json) {
    json = json.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    return json.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g, (match) => {
      let cls = "color: #d8e5f8;";
      if (/^"/.test(match)) {
        if (/:$/.test(match)) {
          cls = "color: #00dceb; font-weight: 600;"; // Key
        } else {
          cls = "color: #ffa938;"; // String
        }
      } else if (/true|false/.test(match)) {
        cls = "color: #2ecc71; font-weight: 700;"; // Boolean
      } else if (/null/.test(match)) {
        cls = "color: #e74c3c;";
      } else {
        cls = "color: #ffcc00;"; // Number
      }
      return `<span style="${cls}">${match}</span>`;
    });
  }

  renderDecisionDashboard(state) {
    const ai = state.ai_decision;
    if (!ai) return;

    // 1. [Choice] 候选落点竞争矩阵
    const candsList = document.getElementById("candsList");
    if (candsList && ai.candidates_detail) {
      candsList.innerHTML = ai.candidates_detail.map(c => {
        const isSelected = c.id === ai.selected_candidate_id;
        const pct = Math.round((ai.candidate_probabilities[c.id] || 0) * 100);
        const clearText = c.lines_cleared > 0 ? `消${c.lines_cleared}行` : "无消行";
        const heightText = c.height_diff !== undefined ? `高+${c.height_diff}` : "";
        return `
          <div class="cand-item ${isSelected ? "selected" : ""}">
            <span class="cand-name">${c.id}: 旋${c.rotation_index * 90}°</span>
            <span class="cand-summary">列${c.target_x} | ${clearText}, 洞+${c.resulting_holes || 0} ${heightText}</span>
            <div class="cand-bar-wrap">
              <div class="cand-bar" style="width: ${pct}%;"></div>
            </div>
            <span class="cand-prob">${pct}%</span>
          </div>
        `;
      }).join("");
    }

    const confEl = document.getElementById("placementConfidence");
    if (confEl && ai.placement_confidence) {
      confEl.innerText = `选定置信度: ${Math.round(ai.placement_confidence * 100)}%`;
    }

    // 2. [Choice] 宏观战术模式分布
    const tacticsGrid = document.getElementById("tacticsGrid");
    if (tacticsGrid && ai.tactic_probabilities) {
      tacticsGrid.innerHTML = Object.entries(ai.tactic_probabilities).map(([tKey, prob]) => {
        const isSelected = tKey === ai.tactic_mode;
        const pct = Math.round(prob * 100);
        const name = TACTIC_NAMES[tKey] || tKey;
        return `
          <div class="tactic-box ${isSelected ? "selected" : ""}">
            <div class="tactic-top">
              <span>${isSelected ? "☑ " : ""}${name}</span>
              <span>${pct}%</span>
            </div>
            <div class="tactic-meter">
              <div class="tactic-fill" style="width: ${pct}%;"></div>
            </div>
          </div>
        `;
      }).join("");
    }

    // 3. [Noul] 临界条件门控
    const crisisVal = Math.round(ai.crisis_prob * 100);
    document.getElementById("noulCrisisVal").innerText = `${crisisVal}%`;
    document.getElementById("meterCrisisBar").style.width = `${crisisVal}%`;
    const crisisTag = document.getElementById("noulCrisisTag");
    if (ai.is_crisis_danger) {
      crisisTag.className = "noul-tag danger";
      crisisTag.innerText = "【濒危避险】";
    } else {
      crisisTag.className = "noul-tag safe";
      crisisTag.innerText = "【安全稳定】";
    }

    const holdVal = Math.round(ai.hold_prob * 100);
    document.getElementById("noulHoldVal").innerText = `${holdVal}%`;
    document.getElementById("meterHoldBar").style.width = `${holdVal}%`;
    const holdTag = document.getElementById("noulHoldTag");
    if (ai.should_hold) {
      holdTag.className = "noul-tag danger";
      holdTag.innerText = "【暂存换块】";
    } else {
      holdTag.className = "noul-tag neutral";
      holdTag.innerText = "【维持当前块】";
    }

    // 4. [Score] 局面健康态势 5 级直方图
    const scoreStars = document.getElementById("scoreStars");
    if (scoreStars) {
      const h = Number(ai.board_health).toFixed(1);
      scoreStars.innerText = `★★★★★ ${h} / 5.0 级`;
    }

    const histContainer = document.getElementById("scoreHistogram");
    if (histContainer && ai.score_probabilities) {
      const levels = [
        { lvl: 1, name: "1级·濒危" },
        { lvl: 2, name: "2级·不良" },
        { lvl: 3, name: "3级·正常" },
        { lvl: 4, name: "4级·良好" },
        { lvl: 5, name: "5级·黄金" },
      ];
      // 找出最大概率级别
      let maxProb = 0;
      let peakLvl = 5;
      levels.forEach(item => {
        const p = ai.score_probabilities[item.lvl] || 0;
        if (p > maxProb) { maxProb = p; peakLvl = item.lvl; }
      });

      histContainer.innerHTML = levels.map(item => {
        const p = ai.score_probabilities[item.lvl] || 0;
        const pct = Math.round(p * 100);
        const isPeak = item.lvl === peakLvl;
        return `
          <div class="hist-col ${isPeak ? "peak" : ""}">
            <span class="hist-pct">${pct}%</span>
            <div class="hist-bar-container">
              <div class="hist-bar-fill" style="height: ${Math.max(4, pct)}%;"></div>
            </div>
            <span class="hist-label">${item.name}</span>
          </div>
        `;
      }).join("");
    }

    // 总结栏
    const summaryText = document.getElementById("summaryText");
    if (summaryText && ai.summary_text) {
      summaryText.innerText = ai.summary_text;
    }
  }

  renderOverlay(state) {
    const overlay = document.getElementById("boardOverlay");
    const title = document.getElementById("overlayTitle");
    const msg = document.getElementById("overlayMsg");
    const btn = document.getElementById("overlayBtn");

    if (state.status === "PAUSED") {
      overlay.classList.remove("hidden");
      title.innerText = "游戏已暂停";
      msg.innerText = "按 [ P ] 键或点击下方按钮继续游戏";
      btn.innerText = "继续游戏";
    } else if (state.status === "GAME_OVER") {
      overlay.classList.remove("hidden");
      title.innerText = "游戏结束 (GAME OVER)";
      msg.innerHTML = `最终得分: <strong style="color: #ffcc00;">${state.score}</strong><br>总消行数: <strong>${state.lines}</strong>`;
      btn.innerText = "重新开始新一局 [ R ]";
    } else {
      overlay.classList.add("hidden");
    }
  }
}

// 页面加载后启动
window.addEventListener("DOMContentLoaded", () => {
  window.dashboard = new TetrisWebDashboard();
});
