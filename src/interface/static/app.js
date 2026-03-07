/**
 * Manas Brain Dashboard — WebSocket client + live UI updater
 * Phase 3: Power & Scale
 */

// ── Config ────────────────────────────────────────────────────
const WS_URL = `ws://${location.host}/ws`;
const API_URL = `${location.origin}`;
const RECONNECT_DELAY = 3000;

// Emotion → CSS colour (matches style.css custom properties)
const EMOTION_COLORS = {
    happiness: '#FFD700',
    curiosity: '#7C3AED',
    fear: '#EF4444',
    anxiety: '#F97316',
    confidence: '#10B981',
    caution: '#FBBF24',
};

const CHEM_COLORS = {
    dopamine: '#FFD700',
    serotonin: '#34D399',
    norepinephrine: '#F87171',
    cortisol: '#FB923C',
    oxytocin: '#A78BFA',
    endorphins: '#38BDF8',
    acetylcholine: '#4ADE80',
    gaba: '#94A3B8',
};

const NEURAL_SHORT = {
    sensory_cortex: 'Sensory',
    prefrontal: 'PFC',
    amygdala: 'Amygdala',
    hippocampus: 'Hippo',
    thalamus: 'Thalamus',
    basal_ganglia: 'Basal G.',
    cerebellum: 'Cerebellum',
    insula: 'Insula',
    acc: 'ACC',
    wernickes: 'Wernicke',
    brocas: 'Broca',
    default_mode: 'DMN',
    consciousness: 'Global W.',
};

// ── State ──────────────────────────────────────────────────────
let ws = null;
let sending = false;
let goalData = [];

// ── Elements ───────────────────────────────────────────────────
const chatArea = document.getElementById('chat-area');
const chatInput = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-btn');
const connBadge = document.getElementById('connection-badge');
const emotionBars = document.getElementById('emotion-bars');
const chemBars = document.getElementById('chem-bars');
const neuralGrid = document.getElementById('neural-grid');
const monologue = document.getElementById('monologue-panel');
const autonomousPanel = document.getElementById('autonomous-panel');
const goalsPanel = document.getElementById('goals-panel');
const memPanel = document.getElementById('memory-panel');
const hCycle = document.getElementById('h-cycle');
const hDebt = document.getElementById('h-debt');
const hEmotion = document.getElementById('h-emotion');
const hConscious = document.getElementById('h-conscious');
const consOrb = document.getElementById('consciousness-orb');
const consLabel = document.getElementById('consciousness-label');
const consLevel = document.getElementById('consciousness-level');

// ── Init ───────────────────────────────────────────────────────
window.addEventListener('DOMContentLoaded', () => {
    buildEmotionBars();
    buildChemBars();
    buildNeuralGrid();
    loadGoals();
    connect();

    sendBtn.addEventListener('click', sendMessage);
    chatInput.addEventListener('keydown', e => {
        if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
    });
});

// ── WebSocket ──────────────────────────────────────────────────
function connect() {
    ws = new WebSocket(WS_URL);

    ws.onopen = () => {
        connBadge.textContent = '● Connected';
        connBadge.classList.remove('disconnected');
        addSystemMsg('Connected to Manas brain ✓');
    };

    ws.onclose = () => {
        connBadge.textContent = '● Disconnected';
        connBadge.classList.add('disconnected');
        addSystemMsg('Connection lost — reconnecting…');
        setTimeout(connect, RECONNECT_DELAY);
    };

    ws.onerror = () => {
        connBadge.textContent = '● Error';
        connBadge.classList.add('disconnected');
    };

    ws.onmessage = (evt) => {
        try {
            const data = JSON.parse(evt.data);
            handleUpdate(data);
        } catch (e) { /* ignore parse errors */ }
    };
}

// ── Update handler ─────────────────────────────────────────────
function handleUpdate(data) {
    if (data.emotions) updateEmotionBars(data.emotions);
    if (data.inner_monologue) updateMonologue(data.inner_monologue);
    if (data.thoughts) updateAutonomousActivity(data.thoughts);
    if (data.brain_activity) updateNeuralGrid(data.brain_activity);
    if (data.cycle !== undefined) hCycle.textContent = data.cycle;
    if (data.sleep_debt !== undefined) hDebt.textContent = data.sleep_debt.toFixed(2);
    if (data.dominant_emotion) {
        hEmotion.textContent = data.dominant_emotion;
        updateConsciousness(data.dominant_emotion, data.emotion_intensity || 0.5);
    }

    // Chat response from POST /chat
    if (data.type === 'chat_response' && data.chat?.response) {
        addManasMsg(data.chat.response, data.dominant_emotion, data.chat.tool);
        setSending(false);
    }
}

// ── Send message ───────────────────────────────────────────────
async function sendMessage() {
    const text = chatInput.value.trim();
    if (!text || sending) return;

    setSending(true);
    addUserMsg(text);
    chatInput.value = '';

    try {
        const resp = await fetch(`${API_URL}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text }),
        });
        const data = await resp.json();

        addManasMsg(
            data.response || data.error || '…',
            data.emotion,
            data.tool_result,
            data.inner_thought,
            data.memories_recalled,
            data.source,
        );
        // Also load updated goals/memory
        loadGoals();
        loadMemoryStats();
    } catch (e) {
        addManasMsg('⚠️ Could not reach Manas brain.', 'caution');
    } finally {
        setSending(false);
    }
}

// ── Chat messages ──────────────────────────────────────────────
function addUserMsg(text) {
    const div = document.createElement('div');
    div.className = 'msg user';
    div.innerHTML = `<div>${escHtml(text)}</div>
    <div class="msg-meta">${now()}</div>`;
    chatArea.appendChild(div);
    scrollChat();
}

function addManasMsg(text, emotion, toolResult, innerThought, memCount, source) {
    const div = document.createElement('div');
    div.className = 'msg manas';

    let meta = `${now()}`;
    if (emotion) meta += ` · 🎭 ${emotion}`;
    if (memCount) meta += ` · 🗄️ ${memCount} memories`;
    if (source) meta += ` · (${source})`;

    let extra = '';
    if (toolResult && toolResult.success) {
        extra += `<div class="msg-tool">🔧 ${toolResult.tool_name}: ${escHtml(toolResult.output.slice(0, 200))}</div>`;
    }
    if (innerThought) {
        extra += `<div style="margin-top:6px;font-size:11px;color:var(--text-dim);font-style:italic;">💭 ${escHtml(innerThought.slice(0, 120))}</div>`;
    }

    div.innerHTML = `<div>${escHtml(text)}</div>${extra}<div class="msg-meta">${meta}</div>`;
    chatArea.appendChild(div);
    scrollChat();
}

function addSystemMsg(text) {
    const div = document.createElement('div');
    div.className = 'msg system';
    div.textContent = text;
    chatArea.appendChild(div);
    scrollChat();
}

// ── Emotion bars ───────────────────────────────────────────────
function buildEmotionBars() {
    emotionBars.innerHTML = Object.keys(EMOTION_COLORS).map(em => `
    <div class="emotion-row">
      <span class="emotion-label">${em}</span>
      <div class="emotion-bar-track">
        <div class="emotion-bar-fill" id="em-${em}" style="width:0%;background:${EMOTION_COLORS[em]};"></div>
      </div>
      <span class="emotion-val" id="emv-${em}">0.00</span>
    </div>
  `).join('');
}

function updateEmotionBars(emotions) {
    for (const [em, val] of Object.entries(emotions)) {
        const bar = document.getElementById(`em-${em}`);
        const txt = document.getElementById(`emv-${em}`);
        if (bar) bar.style.width = `${Math.round((val || 0) * 100)}%`;
        if (txt) txt.textContent = (val || 0).toFixed(2);
    }
}

// ── Neurochem bars ─────────────────────────────────────────────
function buildChemBars() {
    chemBars.innerHTML = Object.keys(CHEM_COLORS).map(ch => `
    <div class="chem-row">
      <span class="chem-label">${ch}</span>
      <div class="chem-bar-track">
        <div class="chem-bar-fill" id="ch-${ch}" style="width:0%;background:${CHEM_COLORS[ch]};"></div>
      </div>
      <span class="chem-val" id="chv-${ch}">0.00</span>
    </div>
  `).join('');
}

function updateChemBars(chem) {
    for (const [ch, val] of Object.entries(chem)) {
        const bar = document.getElementById(`ch-${ch}`);
        const txt = document.getElementById(`chv-${ch}`);
        if (bar) bar.style.width = `${Math.round((val || 0) * 100)}%`;
        if (txt) txt.textContent = (val || 0).toFixed(2);
    }
}

// ── Neural grid ────────────────────────────────────────────────
function buildNeuralGrid() {
    neuralGrid.innerHTML = Object.keys(NEURAL_SHORT).map(region => `
    <div class="neural-cell" id="nc-${region}">
      <div class="neural-cell-bg" id="ncbg-${region}"></div>
      <div class="neural-cell-name">${NEURAL_SHORT[region]}</div>
      <div class="neural-cell-val" id="ncv-${region}">—</div>
    </div>
  `).join('');
}

function updateNeuralGrid(activity) {
    for (const [region, val] of Object.entries(activity)) {
        const cell = document.getElementById(`nc-${region}`);
        const bg = document.getElementById(`ncbg-${region}`);
        const vtxt = document.getElementById(`ncv-${region}`);
        if (!cell) continue;
        const v = Math.min(1, Math.max(0, val || 0));
        const opacity = 0.08 + v * 0.55;
        const hue = 200 + v * 60; // blue → purple with activity
        if (bg) bg.style.background = `hsla(${hue},80%,60%,${opacity})`;
        if (vtxt) vtxt.textContent = v.toFixed(2);
        cell.style.borderColor = v > 0.5 ? `hsla(${hue},80%,60%,0.5)` : 'var(--border)';
    }
}

// ── Inner monologue ────────────────────────────────────────────
const MONOLOGUE_MAX = 6;
let monologueItems = [];

function updateMonologue(lines) {
    // Only combine the actual monologue lines
    const all = [];
    for (const ln of (lines || [])) {
        all.push({ type: 'thought', content: ln });
    }
    if (!all.length) return;

    monologueItems = [...monologueItems, ...all].slice(-MONOLOGUE_MAX);
    monologue.innerHTML = monologueItems.reverse().map(t => `
    <div class="thought-item">
      <div class="thought-type">${t.type}</div>
      ${escHtml(t.content.slice(0, 120))}
    </div>
  `).join('');
    monologueItems.reverse(); // put back in order
}

// ── Autonomous Activity ────────────────────────────────────────
function updateAutonomousActivity(thoughts) {
    if (!thoughts || !thoughts.length) return;

    autonomousPanel.innerHTML = thoughts.slice().reverse().map(t => `
    <div class="auto-item" style="margin-bottom: 6px; border-bottom: 1px solid var(--border); padding-bottom: 4px;">
      <div class="auto-type" style="font-size: 10px; color: var(--accent); text-transform: uppercase;">${escHtml(t.type || 'auto')}</div>
      <div style="font-size: 11.5px; line-height: 1.3;">${escHtml(t.content)}</div>
    </div>
  `).join('');
}

// ── Consciousness ──────────────────────────────────────────────
function updateConsciousness(emotion, intensity) {
    hConscious.textContent = emotion || 'awake';
    const hue = {
        happiness: 50, curiosity: 270, fear: 0, anxiety: 25,
        confidence: 160, caution: 45,
    }[emotion] || 210;
    const alpha = 0.3 + intensity * 0.5;
    consOrb.style.background = `radial-gradient(circle at 35% 35%, hsla(${hue},90%,65%,0.9), hsla(${hue + 50},80%,50%,0.4))`;
    consOrb.style.boxShadow = `0 0 20px hsla(${hue},80%,60%,${alpha}), 0 0 60px hsla(${hue},80%,60%,${alpha * 0.4})`;
    consLabel.textContent = emotion ? `feeling ${emotion}` : 'neutral';
    consLevel.textContent = `${Math.round(intensity * 100)}%`;
}

// ── Goals ──────────────────────────────────────────────────────
async function loadGoals() {
    try {
        const r = await fetch(`${API_URL}/goals`);
        const d = await r.json();
        goalData = d.goals || [];
        renderGoals();
    } catch (_) { }
}

function renderGoals() {
    if (!goalData.length) {
        goalsPanel.innerHTML = '<div style="color:var(--text-dim);font-size:11px;">No active goals.</div>';
        return;
    }
    goalsPanel.innerHTML = goalData.slice(0, 5).map(g => {
        const catColor = { survival: '#f87171', growth: '#34d399', social: '#63b3ed', curiosity: '#a78bfa' }[g.category] || '#94a3b8';
        return `
      <div class="goal-item">
        <div class="goal-name">${escHtml(g.name)}</div>
        <div class="goal-meta" style="color:${catColor};">${g.category} · priority ${g.priority.toFixed(2)}</div>
        <div class="goal-progress-track">
          <div class="goal-progress-fill" style="width:${Math.round(g.progress * 100)}%;"></div>
        </div>
      </div>`;
    }).join('');
}

// ── Memory stats ───────────────────────────────────────────────
async function loadMemoryStats() {
    try {
        const r = await fetch(`${API_URL}/state`);
        const d = await r.json();
        if (d.memory) renderMemory(d.memory);
        if (d.neurochemistry) updateChemBars(d.neurochemistry);
    } catch (_) { }
}

function renderMemory(mem) {
    const tiers = mem.by_tier || {};
    const types = mem.by_type || {};
    const total = Object.values(types).reduce((a, b) => a + b, 0);
    memPanel.innerHTML = `
    <div style="margin-bottom:8px;">
      <div style="font-size:11px;color:var(--text-dim);margin-bottom:4px;">Tiers</div>
      ${Object.entries(tiers).map(([k, v]) => `
        <div style="display:flex;justify-content:space-between;font-size:11px;margin-bottom:3px;">
          <span style="color:var(--text-dim);">${k.replace('_', ' ')}</span>
          <span style="color:var(--accent);font-family:'JetBrains Mono',monospace;">${v}</span>
        </div>`).join('')}
    </div>
    <div>
      <div style="font-size:11px;color:var(--text-dim);margin-bottom:4px;">Types</div>
      ${Object.entries(types).map(([k, v]) => `
        <div style="display:flex;justify-content:space-between;font-size:11px;margin-bottom:3px;">
          <span style="color:var(--text-dim);">${k}</span>
          <span style="color:var(--accent3);font-family:'JetBrains Mono',monospace;">${v}</span>
        </div>`).join('')}
      <div style="margin-top:6px;font-size:10px;color:var(--text-dim);">Total: ${total}</div>
    </div>`;
}

// ── Poll for state every 5s (fallback for non-WS data) ─────────
setInterval(() => {
    loadMemoryStats();
    loadGoals();
}, 5000);

// On load, grab initial state
setTimeout(() => {
    loadGoals();
    loadMemoryStats();
}, 500);

// ── Helpers ────────────────────────────────────────────────────
function scrollChat() {
    requestAnimationFrame(() => { chatArea.scrollTop = chatArea.scrollHeight; });
}

function setSending(v) {
    sending = v;
    sendBtn.disabled = v;
    sendBtn.textContent = v ? '…' : 'Send';
}

function escHtml(str) {
    return (str || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function now() {
    return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}
