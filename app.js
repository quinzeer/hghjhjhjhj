(() => {
    'use strict';

    const BUTTON_NAMES = [
        'X', 'O', '□', '△',
        'L1', 'R1', 'L2', 'R2',
        'Share', 'Options', 'L3', 'R3',
        '↑', '↓', '←', '→',
        'PS', 'Touch'
    ];

    const state = {
        gamepadIndex: null,
        connected: false,
        buttonsTested: new Set(),
        stickLHistory: [],
        stickRHistory: [],
        stickLSectors: new Set(),
        stickRSectors: new Set(),
        triggerL2History: [],
        triggerR2History: [],
        triggerL2Min: 1,
        triggerL2Max: 0,
        triggerR2Min: 1,
        triggerR2Max: 0,
        deadzoneHistory: [],
        latency: { running: false, state: 'idle', times: [], greenAt: 0, timeout: null },
        stress: { running: false, timer: 30, total: 0, perSecond: [], lastButtons: [], interval: null, startTime: 0, heatmap: {} }
    };

    // DOM
    const $ = (sel) => document.querySelector(sel);
    const $$ = (sel) => document.querySelectorAll(sel);

    // Tabs
    $$('.tab').forEach(tab => {
        tab.addEventListener('click', () => {
            $$('.tab').forEach(t => t.classList.remove('active'));
            $$('.panel').forEach(p => p.classList.remove('active'));
            tab.classList.add('active');
            $(`#tab-${tab.dataset.tab}`).classList.add('active');
        });
    });

    // Gamepad connection
    window.addEventListener('gamepadconnected', (e) => {
        state.gamepadIndex = e.gamepad.index;
        state.connected = true;
        $('#connection-status').className = 'status connected';
        $('.status-text').textContent = e.gamepad.id.substring(0, 40);
        $('#connect-screen').classList.add('hidden');
        $('#test-area').classList.remove('hidden');
        $('#controller-info').textContent = e.gamepad.id;
        initOverviewButtons();
        initStressHeatmap();
        loop();
    });

    window.addEventListener('gamepaddisconnected', () => {
        state.connected = false;
        state.gamepadIndex = null;
        $('#connection-status').className = 'status disconnected';
        $('.status-text').textContent = 'Aucune manette';
        $('#connect-screen').classList.remove('hidden');
        $('#test-area').classList.add('hidden');
    });

    function getGamepad() {
        const gamepads = navigator.getGamepads();
        return state.gamepadIndex !== null ? gamepads[state.gamepadIndex] : null;
    }

    // Main loop
    function loop() {
        if (!state.connected) return;
        const gp = getGamepad();
        if (!gp) { requestAnimationFrame(loop); return; }

        updateOverview(gp);
        updateButtons(gp);
        updateSticks(gp);
        updateTriggers(gp);
        updateDeadzone(gp);
        updateLatency(gp);
        updateStress(gp);

        requestAnimationFrame(loop);
    }

    // === OVERVIEW ===
    function initOverviewButtons() {
        const container = $('#overview-buttons');
        container.innerHTML = '';
        BUTTON_NAMES.forEach((name, i) => {
            const el = document.createElement('div');
            el.className = 'overview-btn';
            el.id = `ov-btn-${i}`;
            el.textContent = name;
            container.appendChild(el);
        });
    }

    function updateOverview(gp) {
        gp.buttons.forEach((btn, i) => {
            const el = $(`#ov-btn-${i}`);
            if (el) el.classList.toggle('pressed', btn.pressed);
        });

        drawMiniStick('overview-stick-l', gp.axes[0], gp.axes[1]);
        drawMiniStick('overview-stick-r', gp.axes[2], gp.axes[3]);
        $('#overview-stick-l-values').textContent = `X: ${gp.axes[0].toFixed(2)}  Y: ${gp.axes[1].toFixed(2)}`;
        $('#overview-stick-r-values').textContent = `X: ${gp.axes[2].toFixed(2)}  Y: ${gp.axes[3].toFixed(2)}`;

        const l2 = gp.buttons[6]?.value || 0;
        const r2 = gp.buttons[7]?.value || 0;
        $('#overview-l2').style.width = `${l2 * 100}%`;
        $('#overview-r2').style.width = `${r2 * 100}%`;
        $('#overview-l2-val').textContent = `${Math.round(l2 * 100)}%`;
        $('#overview-r2-val').textContent = `${Math.round(r2 * 100)}%`;
    }

    function drawMiniStick(canvasId, x, y) {
        const canvas = $(`#${canvasId}`);
        const ctx = canvas.getContext('2d');
        const w = canvas.width, h = canvas.height;
        const cx = w / 2, cy = h / 2, r = w / 2 - 10;

        ctx.clearRect(0, 0, w, h);

        ctx.beginPath();
        ctx.arc(cx, cy, r, 0, Math.PI * 2);
        ctx.strokeStyle = '#1e1e2e';
        ctx.lineWidth = 2;
        ctx.stroke();

        ctx.beginPath();
        ctx.moveTo(cx, cy - r); ctx.lineTo(cx, cy + r);
        ctx.moveTo(cx - r, cy); ctx.lineTo(cx + r, cy);
        ctx.strokeStyle = 'rgba(255,255,255,0.05)';
        ctx.lineWidth = 1;
        ctx.stroke();

        const px = cx + x * r;
        const py = cy + y * r;
        ctx.beginPath();
        ctx.arc(px, py, 8, 0, Math.PI * 2);
        ctx.fillStyle = '#0070f3';
        ctx.shadowColor = 'rgba(0, 112, 243, 0.5)';
        ctx.shadowBlur = 12;
        ctx.fill();
        ctx.shadowBlur = 0;
    }

    // === BUTTONS TEST ===
    function updateButtons(gp) {
        let testedCount = 0;
        gp.buttons.forEach((btn, i) => {
            const el = document.querySelectorAll(`.ps-btn[data-btn="${i}"]`);
            el.forEach(e => {
                e.classList.toggle('pressed', btn.pressed);
                if (btn.pressed) {
                    state.buttonsTested.add(i);
                    e.classList.add('tested');
                }
            });
            if (state.buttonsTested.has(i)) testedCount++;
        });

        const total = Math.min(gp.buttons.length, 18);
        const pct = (state.buttonsTested.size / total) * 100;
        $('#buttons-progress').style.width = `${pct}%`;
        $('#buttons-progress-text').textContent = `${state.buttonsTested.size} / ${total} boutons testés`;
    }

    $('#btn-reset-buttons')?.addEventListener('click', () => {
        state.buttonsTested.clear();
        $$('.ps-btn').forEach(el => el.classList.remove('tested'));
    });

    // === STICKS TEST ===
    function updateSticks(gp) {
        const lx = gp.axes[0], ly = gp.axes[1];
        const rx = gp.axes[2], ry = gp.axes[3];

        drawStickCanvas('stick-l-canvas', lx, ly, state.stickLHistory);
        drawStickCanvas('stick-r-canvas', rx, ry, state.stickRHistory);

        state.stickLHistory.push({ x: lx, y: ly });
        state.stickRHistory.push({ x: rx, y: ry });
        if (state.stickLHistory.length > 2000) state.stickLHistory.shift();
        if (state.stickRHistory.length > 2000) state.stickRHistory.shift();

        const lDist = Math.sqrt(lx * lx + ly * ly);
        const rDist = Math.sqrt(rx * rx + ry * ry);
        const lAngle = Math.round(Math.atan2(ly, lx) * 180 / Math.PI);
        const rAngle = Math.round(Math.atan2(ry, rx) * 180 / Math.PI);

        $('#stick-l-x').textContent = lx.toFixed(3);
        $('#stick-l-y').textContent = ly.toFixed(3);
        $('#stick-l-angle').textContent = `${lAngle}°`;
        $('#stick-l-dist').textContent = lDist.toFixed(3);

        $('#stick-r-x').textContent = rx.toFixed(3);
        $('#stick-r-y').textContent = ry.toFixed(3);
        $('#stick-r-angle').textContent = `${rAngle}°`;
        $('#stick-r-dist').textContent = rDist.toFixed(3);

        if (lDist > 0.3) {
            const sector = Math.floor(((lAngle + 180) / 360) * 36);
            state.stickLSectors.add(sector);
        }
        if (rDist > 0.3) {
            const sector = Math.floor(((rAngle + 180) / 360) * 36);
            state.stickRSectors.add(sector);
        }

        const lCov = Math.round((state.stickLSectors.size / 36) * 100);
        const rCov = Math.round((state.stickRSectors.size / 36) * 100);
        $('#stick-l-coverage').style.width = `${lCov}%`;
        $('#stick-l-coverage-text').textContent = `${lCov}%`;
        $('#stick-r-coverage').style.width = `${rCov}%`;
        $('#stick-r-coverage-text').textContent = `${rCov}%`;
    }

    function drawStickCanvas(canvasId, x, y, history) {
        const canvas = $(`#${canvasId}`);
        const ctx = canvas.getContext('2d');
        const w = canvas.width, h = canvas.height;
        const cx = w / 2, cy = h / 2, r = w / 2 - 20;

        ctx.clearRect(0, 0, w, h);

        ctx.beginPath();
        ctx.arc(cx, cy, r, 0, Math.PI * 2);
        ctx.strokeStyle = '#1e1e2e';
        ctx.lineWidth = 2;
        ctx.stroke();

        [0.25, 0.5, 0.75].forEach(s => {
            ctx.beginPath();
            ctx.arc(cx, cy, r * s, 0, Math.PI * 2);
            ctx.strokeStyle = 'rgba(255,255,255,0.04)';
            ctx.lineWidth = 1;
            ctx.stroke();
        });

        ctx.beginPath();
        ctx.moveTo(cx, cy - r); ctx.lineTo(cx, cy + r);
        ctx.moveTo(cx - r, cy); ctx.lineTo(cx + r, cy);
        ctx.strokeStyle = 'rgba(255,255,255,0.06)';
        ctx.lineWidth = 1;
        ctx.stroke();

        if (history.length > 1) {
            ctx.beginPath();
            history.forEach((p, i) => {
                const px = cx + p.x * r;
                const py = cy + p.y * r;
                if (i === 0) ctx.moveTo(px, py);
                else ctx.lineTo(px, py);
            });
            ctx.strokeStyle = 'rgba(0, 112, 243, 0.15)';
            ctx.lineWidth = 1.5;
            ctx.stroke();
        }

        const px = cx + x * r;
        const py = cy + y * r;

        ctx.beginPath();
        ctx.moveTo(cx, cy);
        ctx.lineTo(px, py);
        ctx.strokeStyle = 'rgba(0, 112, 243, 0.4)';
        ctx.lineWidth = 2;
        ctx.stroke();

        ctx.beginPath();
        ctx.arc(px, py, 10, 0, Math.PI * 2);
        ctx.fillStyle = '#0070f3';
        ctx.shadowColor = 'rgba(0, 112, 243, 0.6)';
        ctx.shadowBlur = 16;
        ctx.fill();
        ctx.shadowBlur = 0;
    }

    $('#btn-reset-sticks')?.addEventListener('click', () => {
        state.stickLHistory = [];
        state.stickRHistory = [];
        state.stickLSectors.clear();
        state.stickRSectors.clear();
    });

    // === TRIGGERS ===
    function updateTriggers(gp) {
        const l2 = gp.buttons[6]?.value || 0;
        const r2 = gp.buttons[7]?.value || 0;

        drawTriggerArc('trigger-l2-arc', l2, '#0070f3');
        drawTriggerArc('trigger-r2-arc', r2, '#e74c8b');

        $('#trigger-l2-percent').textContent = `${Math.round(l2 * 100)}%`;
        $('#trigger-r2-percent').textContent = `${Math.round(r2 * 100)}%`;

        state.triggerL2History.push(l2);
        state.triggerR2History.push(r2);
        if (state.triggerL2History.length > 200) state.triggerL2History.shift();
        if (state.triggerR2History.length > 200) state.triggerR2History.shift();

        drawTriggerHistory('trigger-l2-history', state.triggerL2History, '#0070f3');
        drawTriggerHistory('trigger-r2-history', state.triggerR2History, '#e74c8b');

        if (l2 > 0.01) { state.triggerL2Min = Math.min(state.triggerL2Min, l2); state.triggerL2Max = Math.max(state.triggerL2Max, l2); }
        if (r2 > 0.01) { state.triggerR2Min = Math.min(state.triggerR2Min, r2); state.triggerR2Max = Math.max(state.triggerR2Max, r2); }

        $('#trigger-l2-min').textContent = state.triggerL2Max > 0 ? state.triggerL2Min.toFixed(2) : '0.00';
        $('#trigger-l2-max').textContent = state.triggerL2Max.toFixed(2);
        $('#trigger-r2-min').textContent = state.triggerR2Max > 0 ? state.triggerR2Min.toFixed(2) : '0.00';
        $('#trigger-r2-max').textContent = state.triggerR2Max.toFixed(2);

        const l2Prec = state.triggerL2Max >= 0.95 ? 'Excellent' : state.triggerL2Max >= 0.7 ? 'Bon' : state.triggerL2Max > 0 ? 'Faible' : '—';
        const r2Prec = state.triggerR2Max >= 0.95 ? 'Excellent' : state.triggerR2Max >= 0.7 ? 'Bon' : state.triggerR2Max > 0 ? 'Faible' : '—';
        $('#trigger-l2-precision').textContent = l2Prec;
        $('#trigger-r2-precision').textContent = r2Prec;
    }

    function drawTriggerArc(canvasId, value, color) {
        const canvas = $(`#${canvasId}`);
        const ctx = canvas.getContext('2d');
        const w = canvas.width, h = canvas.height;

        ctx.clearRect(0, 0, w, h);

        const cx = w / 2, cy = h - 10, radius = 100;
        const startAngle = Math.PI;
        const endAngle = 2 * Math.PI;

        ctx.beginPath();
        ctx.arc(cx, cy, radius, startAngle, endAngle);
        ctx.strokeStyle = '#1e1e2e';
        ctx.lineWidth = 20;
        ctx.lineCap = 'round';
        ctx.stroke();

        if (value > 0) {
            const angle = startAngle + (endAngle - startAngle) * value;
            ctx.beginPath();
            ctx.arc(cx, cy, radius, startAngle, angle);
            ctx.strokeStyle = color;
            ctx.lineWidth = 20;
            ctx.lineCap = 'round';
            ctx.shadowColor = color;
            ctx.shadowBlur = 15;
            ctx.stroke();
            ctx.shadowBlur = 0;
        }
    }

    function drawTriggerHistory(canvasId, history, color) {
        const canvas = $(`#${canvasId}`);
        const ctx = canvas.getContext('2d');
        const w = canvas.width, h = canvas.height;

        ctx.clearRect(0, 0, w, h);

        if (history.length < 2) return;

        ctx.beginPath();
        history.forEach((v, i) => {
            const x = (i / (history.length - 1)) * w;
            const y = h - v * h;
            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        });
        ctx.strokeStyle = color;
        ctx.lineWidth = 2;
        ctx.stroke();

        ctx.lineTo(w, h);
        ctx.lineTo(0, h);
        ctx.closePath();
        ctx.fillStyle = color.replace(')', ', 0.1)').replace('rgb', 'rgba');
        ctx.fill();
    }

    // === VIBRATION ===
    $$('.vibration-btn[data-intensity]').forEach(btn => {
        btn.addEventListener('click', () => {
            const gp = getGamepad();
            if (!gp || !gp.vibrationActuator) return;

            const intensity = btn.dataset.intensity;
            const duration = parseInt(btn.dataset.duration);

            btn.classList.add('active');
            setTimeout(() => btn.classList.remove('active'), duration);

            if (intensity === 'weak') {
                gp.vibrationActuator.playEffect('dual-rumble', { duration, weakMagnitude: 0.5, strongMagnitude: 0 });
            } else if (intensity === 'strong') {
                gp.vibrationActuator.playEffect('dual-rumble', { duration, weakMagnitude: 0, strongMagnitude: 0.8 });
            } else if (intensity === 'both') {
                gp.vibrationActuator.playEffect('dual-rumble', { duration, weakMagnitude: 0.5, strongMagnitude: 0.8 });
            } else if (intensity === 'pulse') {
                let count = 0;
                const iv = setInterval(() => {
                    gp.vibrationActuator.playEffect('dual-rumble', { duration: 150, weakMagnitude: 0.4, strongMagnitude: 0.6 });
                    count++;
                    if (count >= 8) clearInterval(iv);
                }, 250);
                setTimeout(() => btn.classList.remove('active'), duration);
            }
        });
    });

    ['vib-weak', 'vib-strong', 'vib-duration'].forEach(id => {
        const el = $(`#${id}`);
        if (el) el.addEventListener('input', () => {
            $(`#${id}-val`).textContent = el.value;
        });
    });

    $('#vib-custom-btn')?.addEventListener('click', () => {
        const gp = getGamepad();
        if (!gp || !gp.vibrationActuator) return;

        const weak = parseFloat($('#vib-weak').value);
        const strong = parseFloat($('#vib-strong').value);
        const duration = parseInt($('#vib-duration').value);

        const btn = $('#vib-custom-btn');
        btn.classList.add('active');
        setTimeout(() => btn.classList.remove('active'), duration);

        gp.vibrationActuator.playEffect('dual-rumble', { duration, weakMagnitude: weak, strongMagnitude: strong });
    });

    // === DEADZONE ===
    function updateDeadzone(gp) {
        const lx = gp.axes[0], ly = gp.axes[1];
        const rx = gp.axes[2], ry = gp.axes[3];

        const dzL = parseFloat($('#dz-l-range')?.value || 0.05);
        const dzR = parseFloat($('#dz-r-range')?.value || 0.05);

        drawDeadzoneCanvas('deadzone-l', lx, ly, dzL);
        drawDeadzoneCanvas('deadzone-r', rx, ry, dzR);

        const lDrift = Math.sqrt(lx * lx + ly * ly);
        const rDrift = Math.sqrt(rx * rx + ry * ry);

        $('#dz-l-x').textContent = lx.toFixed(3);
        $('#dz-l-y').textContent = ly.toFixed(3);
        $('#dz-l-total').textContent = lDrift.toFixed(3);
        $('#dz-r-x').textContent = rx.toFixed(3);
        $('#dz-r-y').textContent = ry.toFixed(3);
        $('#dz-r-total').textContent = rDrift.toFixed(3);

        updateDriftStatus('dz-l-status', lDrift);
        updateDriftStatus('dz-r-status', rDrift);

        state.deadzoneHistory.push({ t: Date.now(), l: lDrift, r: rDrift });
        if (state.deadzoneHistory.length > 300) state.deadzoneHistory.shift();
        drawDeadzoneHistory();
    }

    function updateDriftStatus(id, drift) {
        const el = $(`#${id}`);
        if (drift < 0.02) { el.textContent = 'OK'; el.className = 'status-ok'; }
        else if (drift < 0.08) { el.textContent = 'Léger drift'; el.className = 'status-warn'; }
        else { el.textContent = 'DRIFT !'; el.className = 'status-bad'; }
    }

    function drawDeadzoneCanvas(canvasId, x, y, dz) {
        const canvas = $(`#${canvasId}`);
        const ctx = canvas.getContext('2d');
        const w = canvas.width, h = canvas.height;
        const cx = w / 2, cy = h / 2, r = w / 2 - 20;

        ctx.clearRect(0, 0, w, h);

        ctx.beginPath();
        ctx.arc(cx, cy, r, 0, Math.PI * 2);
        ctx.strokeStyle = '#1e1e2e';
        ctx.lineWidth = 2;
        ctx.stroke();

        ctx.beginPath();
        ctx.arc(cx, cy, r * dz, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(255, 193, 7, 0.1)';
        ctx.strokeStyle = 'rgba(255, 193, 7, 0.4)';
        ctx.lineWidth = 2;
        ctx.setLineDash([4, 4]);
        ctx.fill();
        ctx.stroke();
        ctx.setLineDash([]);

        for (let i = 0; i < 8; i++) {
            const angle = (i / 8) * Math.PI * 2;
            ctx.beginPath();
            ctx.moveTo(cx + Math.cos(angle) * r * dz, cy + Math.sin(angle) * r * dz);
            ctx.lineTo(cx + Math.cos(angle) * r, cy + Math.sin(angle) * r);
            ctx.strokeStyle = 'rgba(255,255,255,0.04)';
            ctx.lineWidth = 1;
            ctx.stroke();
        }

        const px = cx + x * r;
        const py = cy + y * r;
        const dist = Math.sqrt(x * x + y * y);
        const dotColor = dist < dz ? '#ffc107' : dist < 0.08 ? '#ff5252' : '#0070f3';

        ctx.beginPath();
        ctx.arc(px, py, 7, 0, Math.PI * 2);
        ctx.fillStyle = dotColor;
        ctx.shadowColor = dotColor;
        ctx.shadowBlur = 12;
        ctx.fill();
        ctx.shadowBlur = 0;
    }

    function drawDeadzoneHistory() {
        const canvas = $('#deadzone-history');
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        const w = canvas.width, h = canvas.height;

        ctx.clearRect(0, 0, w, h);

        const hist = state.deadzoneHistory;
        if (hist.length < 2) return;

        ctx.beginPath();
        hist.forEach((d, i) => {
            const x = (i / (hist.length - 1)) * w;
            const y = h - Math.min(d.l, 1) * h;
            if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
        });
        ctx.strokeStyle = '#0070f3';
        ctx.lineWidth = 1.5;
        ctx.stroke();

        ctx.beginPath();
        hist.forEach((d, i) => {
            const x = (i / (hist.length - 1)) * w;
            const y = h - Math.min(d.r, 1) * h;
            if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
        });
        ctx.strokeStyle = '#e74c8b';
        ctx.lineWidth = 1.5;
        ctx.stroke();
    }

    ['dz-l-range', 'dz-r-range'].forEach(id => {
        $(`#${id}`)?.addEventListener('input', (e) => {
            $(`#${id}-val`).textContent = `${Math.round(e.target.value * 100)}%`;
        });
    });

    // === LATENCY TEST ===
    $('#latency-start')?.addEventListener('click', startLatencyRound);

    function startLatencyRound() {
        const s = state.latency;
        if (s.running) return;
        s.running = true;
        s.state = 'waiting';
        $('#latency-start').disabled = true;
        $('#latency-circle').className = 'latency-circle waiting';
        $('#latency-instruction').innerHTML = 'Attends...';

        const delay = 1500 + Math.random() * 3500;
        s.timeout = setTimeout(() => {
            s.state = 'go';
            s.greenAt = performance.now();
            $('#latency-circle').className = 'latency-circle go';
            $('#latency-instruction').innerHTML = '<strong>APPUIE !</strong>';
        }, delay);
    }

    function updateLatency(gp) {
        const s = state.latency;
        if (!s.running) return;

        const pressed = gp.buttons[0]?.pressed;
        if (!pressed) return;

        if (s.state === 'waiting') {
            clearTimeout(s.timeout);
            s.running = false;
            s.state = 'idle';
            $('#latency-circle').className = 'latency-circle early';
            $('#latency-instruction').innerHTML = 'Trop tôt ! Réessaie.';
            $('#latency-start').disabled = false;
            setTimeout(() => {
                $('#latency-circle').className = 'latency-circle';
                $('#latency-instruction').innerHTML = 'Appuie sur <strong>X</strong> quand le cercle devient vert';
            }, 1500);
            return;
        }

        if (s.state === 'go') {
            const time = Math.round(performance.now() - s.greenAt);
            s.times.push(time);
            s.running = false;
            s.state = 'idle';

            $('#latency-circle').className = 'latency-circle result';
            $('#latency-instruction').innerHTML = `<strong>${time} ms</strong>`;
            $('#latency-last').textContent = `${time} ms`;
            $('#latency-count').textContent = s.times.length;

            const avg = Math.round(s.times.reduce((a, b) => a + b, 0) / s.times.length);
            const best = Math.min(...s.times);
            const worst = Math.max(...s.times);

            $('#latency-avg').textContent = `${avg} ms`;
            $('#latency-best').textContent = `${best} ms`;
            $('#latency-worst').textContent = `${worst} ms`;

            drawLatencyChart();

            $('#latency-start').disabled = false;

            setTimeout(() => {
                if (s.state === 'idle') {
                    $('#latency-circle').className = 'latency-circle';
                    $('#latency-instruction').innerHTML = 'Appuie sur <strong>X</strong> quand le cercle devient vert';
                }
            }, 2000);
        }
    }

    function drawLatencyChart() {
        const canvas = $('#latency-chart');
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        const w = canvas.width, h = canvas.height;
        const times = state.latency.times;

        ctx.clearRect(0, 0, w, h);

        if (times.length < 1) return;

        const max = Math.max(...times, 300);
        const barW = Math.min(40, (w - 40) / times.length);

        times.forEach((t, i) => {
            const x = 20 + i * barW;
            const barH = (t / max) * (h - 40);
            const y = h - 20 - barH;

            let color = '#00e676';
            if (t > 300) color = '#ff5252';
            else if (t > 200) color = '#ffc107';
            else if (t > 150) color = '#0070f3';

            ctx.fillStyle = color;
            ctx.beginPath();
            ctx.roundRect(x + 2, y, barW - 4, barH, 4);
            ctx.fill();

            if (barW > 20) {
                ctx.fillStyle = 'rgba(255,255,255,0.5)';
                ctx.font = '10px Inter';
                ctx.textAlign = 'center';
                ctx.fillText(`${t}`, x + barW / 2, y - 4);
            }
        });

        const avg = state.latency.times.reduce((a, b) => a + b, 0) / times.length;
        const avgY = h - 20 - (avg / max) * (h - 40);
        ctx.beginPath();
        ctx.moveTo(20, avgY);
        ctx.lineTo(w - 20, avgY);
        ctx.strokeStyle = 'rgba(255, 193, 7, 0.5)';
        ctx.lineWidth = 1;
        ctx.setLineDash([4, 4]);
        ctx.stroke();
        ctx.setLineDash([]);
    }

    // === STRESS TEST ===
    function initStressHeatmap() {
        const grid = $('#stress-heatmap-grid');
        if (!grid) return;
        grid.innerHTML = '';
        BUTTON_NAMES.forEach((name, i) => {
            const cell = document.createElement('div');
            cell.className = 'heatmap-cell';
            cell.id = `hm-${i}`;
            cell.innerHTML = `${name}<span class="count">0</span>`;
            grid.appendChild(cell);
            state.stress.heatmap[i] = 0;
        });
    }

    $('#stress-start')?.addEventListener('click', () => {
        const s = state.stress;
        if (s.running) return;

        s.running = true;
        s.timer = 30;
        s.total = 0;
        s.perSecond = [];
        s.lastButtons = [];
        s.startTime = Date.now();
        Object.keys(s.heatmap).forEach(k => s.heatmap[k] = 0);

        $('#stress-timer').textContent = '30';
        $('#stress-timer').classList.add('running');
        $('#stress-start').disabled = true;
        $('#stress-total').textContent = '0';
        $('#stress-rate').textContent = '0';
        $('#stress-missed').textContent = '0';
        $('#stress-score').textContent = '—';

        initStressHeatmap();

        let lastSecondTotal = 0;
        s.interval = setInterval(() => {
            s.timer--;
            $('#stress-timer').textContent = s.timer;

            s.perSecond.push(s.total - lastSecondTotal);
            lastSecondTotal = s.total;

            const elapsed = (Date.now() - s.startTime) / 1000;
            $('#stress-rate').textContent = (s.total / elapsed).toFixed(1);

            drawStressChart();

            if (s.timer <= 0) {
                clearInterval(s.interval);
                s.running = false;
                $('#stress-timer').classList.remove('running');
                $('#stress-start').disabled = false;

                const rate = s.total / 30;
                let score = 'E';
                if (rate >= 15) score = 'S';
                else if (rate >= 10) score = 'A';
                else if (rate >= 7) score = 'B';
                else if (rate >= 4) score = 'C';
                else if (rate >= 2) score = 'D';
                $('#stress-score').textContent = score;
            }
        }, 1000);
    });

    function updateStress(gp) {
        const s = state.stress;
        if (!s.running) return;

        gp.buttons.forEach((btn, i) => {
            const wasPressed = s.lastButtons[i] || false;
            if (btn.pressed && !wasPressed) {
                s.total++;
                s.heatmap[i] = (s.heatmap[i] || 0) + 1;

                const cell = $(`#hm-${i}`);
                if (cell) {
                    const count = cell.querySelector('.count');
                    if (count) count.textContent = s.heatmap[i];

                    const maxHeat = Math.max(...Object.values(s.heatmap), 1);
                    const intensity = s.heatmap[i] / maxHeat;
                    cell.style.background = `rgba(0, 112, 243, ${intensity * 0.6})`;
                    cell.style.borderColor = `rgba(0, 112, 243, ${intensity})`;
                }
            }
            s.lastButtons[i] = btn.pressed;
        });

        $('#stress-total').textContent = s.total;
    }

    function drawStressChart() {
        const canvas = $('#stress-chart');
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        const w = canvas.width, h = canvas.height;
        const data = state.stress.perSecond;

        ctx.clearRect(0, 0, w, h);

        if (data.length < 1) return;

        const max = Math.max(...data, 5);

        ctx.beginPath();
        data.forEach((v, i) => {
            const x = (i / 29) * (w - 40) + 20;
            const y = h - 20 - (v / max) * (h - 40);
            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        });
        ctx.strokeStyle = '#0070f3';
        ctx.lineWidth = 2;
        ctx.stroke();

        ctx.lineTo((data.length - 1) / 29 * (w - 40) + 20, h - 20);
        ctx.lineTo(20, h - 20);
        ctx.closePath();
        ctx.fillStyle = 'rgba(0, 112, 243, 0.1)';
        ctx.fill();

        data.forEach((v, i) => {
            const x = (i / 29) * (w - 40) + 20;
            const y = h - 20 - (v / max) * (h - 40);
            ctx.beginPath();
            ctx.arc(x, y, 3, 0, Math.PI * 2);
            ctx.fillStyle = '#0070f3';
            ctx.fill();
        });
    }

    // Auto-detect gamepad on page load
    function checkExistingGamepad() {
        const gamepads = navigator.getGamepads();
        for (let i = 0; i < gamepads.length; i++) {
            if (gamepads[i]) {
                state.gamepadIndex = i;
                state.connected = true;
                $('#connection-status').className = 'status connected';
                $('.status-text').textContent = gamepads[i].id.substring(0, 40);
                $('#connect-screen').classList.add('hidden');
                $('#test-area').classList.remove('hidden');
                $('#controller-info').textContent = gamepads[i].id;
                initOverviewButtons();
                initStressHeatmap();
                loop();
                break;
            }
        }
    }

    setTimeout(checkExistingGamepad, 500);
})();
