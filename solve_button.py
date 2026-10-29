"""solve_button.py - big, centred "water" Solve button.

Usage in app.py:
    from solve_button import solve_clicked, water_button
    clicked = solve_clicked()
    ... solve the puzzle if clicked ...
    water_button(drained=st.session_state.solved)
"""
import streamlit as st
import streamlit.components.v1 as components

_HTML = r'''<!doctype html>
<html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@600&display=swap" rel="stylesheet">
<style>
  html, body { margin: 0; padding: 0; background: transparent; }
  body { height: 100vh; display: flex; align-items: center; justify-content: center; overflow: hidden; }
  #btn { position: relative; display: inline-flex; align-items: center; justify-content: center;
         box-sizing: border-box; padding: 52px 80px; border-radius: 70px; cursor: pointer;
         isolation: isolate; transition: transform .25s cubic-bezier(.3,1.6,.5,1); -webkit-tap-highlight-color: transparent; outline: none; }
  #btn:active { transform: scale(0.96); }
  #btn .frost { position: absolute; inset: 0; border-radius: inherit; overflow: hidden; pointer-events: none;
         background: hsl(0 0% 100% / 0.10); backdrop-filter: blur(13px); -webkit-backdrop-filter: blur(13px); }
  #btn .tint { position: absolute; inset: 0; border-radius: inherit; background: #42EFE41F; pointer-events: none; }
  #btn .cv { position: absolute; inset: 0; pointer-events: none; }
  #btn canvas { display: block; width: 100%; height: 100%; }
  #btn .label { position: relative; z-index: 3; color: #000; text-align: center; white-space: pre; user-select: none; line-height: 1;
         display: block; font-family: "Plus Jakarta Sans", Inter, system-ui, sans-serif; font-size: 32px; font-weight: 600; letter-spacing: -0.01em; }
</style></head>
<body>
<div id="btn" role="button" tabindex="0" aria-label="Solve">
  <div class="frost"></div><div class="tint"></div><div class="cv"><canvas id="cv"></canvas></div>
  <span class="label">SOLVE</span>
</div>
<script>
(function () {
  // ---- settings (bigger than the original preset) ----
  const ROUNDED = 70;
  const WATER_AMOUNT = 78, WATER_COLOR = "#22ABEB";
  const BORDER = true, BORDER_STROKE = 1, BORDER_COLOR = "rgba(120, 120, 120, 0.7)";

  // ---- click: press the hidden real Streamlit "Solve" button ----
  function pressStreamlitSolve() {
    try {
      const D = window.parent.document;
      let b = D.querySelector('.st-key-solve_real button');
      if (!b) b = Array.from(D.querySelectorAll('button')).find(x => x.innerText.trim() === 'Solve');
      if (b) b.click();
    } catch (e) { console.error(e); }
  }

  // ---- water physics (ported from the Originkit water button) ----
  const COLUMNS = 64, SUBSTEPS = 6, GRAVITY = 6000, VISCOSITY = 2.6, CURSOR_REACH = 46, SWEEP_FORCE = 3, DIP_FORCE = 1.5,
        CLICK_FORCE = 260, MAX_KICK = 8, MAX_FILL = 0.9, STILL = 0.05, SLEEP_FRAMES = 20;
  const MAX_DROPS = 96, DROP_GRAVITY = 1400, DROP_DRAG = 0.6, DROP_VOLUME = 0.18, DROP_RADIUS = 1.25,
        SPRAY_THRESHOLD = 1.6, SPRAY_RATE = 0.5, SPRAY_PER_FRAME = 4, SPRAY_LIFT = 150, BREAK_SPEED = 210, MIN_SPRAY_DEPTH = 2;
  const RIPPLE = 1, MAX_PIXEL_SCALE = 8, MAX_PIXELS = 2000000;

  // ---- water level: drains slowly after solving, refills when the grid is cleared ----
  const DRAINED = __DRAINED__;          // set by Python: true once a puzzle has been solved
  const DRAIN_SECONDS = 6, REFILL_SECONDS = 1.5;
  // the current level (0 = empty, 1 = full) is remembered in the main page, so it
  // survives Streamlit reloading this little frame
  let lvl = 1;
  try { if (typeof window.parent.__sudokuWaterLvl === "number") lvl = window.parent.__sudokuWaterLvl; } catch (e) {}
  const labelEl = document.querySelector("#btn .label");
  const tintLabel = () => { labelEl.style.color = lvl < 0.45 ? "#fff" : "#000"; };   // white text when the glass is empty
  tintLabel();
  const saveLvl = () => { try { window.parent.__sudokuWaterLvl = lvl; } catch (e) {} };

  function parseColor(color) {
    const value = (color || "").trim(); const hex = value.replace("#", "");
    if (/^[0-9a-f]{6}$/i.test(hex)) return [parseInt(hex.slice(0,2),16), parseInt(hex.slice(2,4),16), parseInt(hex.slice(4,6),16), 1];
    const m = value.match(/rgba?\(([^)]+)\)/i);
    if (m) { const p = m[1].split(",").map(parseFloat); return [p[0]||0, p[1]||0, p[2]||0, p[3]===undefined?1:p[3]]; }
    return [62,155,214,1];
  }
  const clampKick = v => Math.max(-MAX_KICK, Math.min(MAX_KICK, v));
  const shift = (c, f) => Math.round(Math.max(0, Math.min(255, c + (f > 0 ? (255 - c) * f : c * f))));
  function roundRectPath(ctx, x, y, w, h, radius) {
    const r = Math.max(0, Math.min(radius, Math.min(w, h) / 2));
    ctx.beginPath(); ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r); ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r); ctx.arcTo(x, y, x + w, y, r); ctx.closePath();
  }

  const root = document.getElementById("btn"), canvas = document.getElementById("cv"), ctx = canvas.getContext("2d");
  let alive = true, raf = 0, last = 0, pixScale = 1, W = 0, H = 0;
  const h = new Float32Array(COLUMNS), u = new Float32Array(COLUMNS + 1), flux = new Float32Array(COLUMNS + 1);
  let rest = 0, fullRest = 0, colW = 1;
  const dropX = new Float32Array(MAX_DROPS), dropY = new Float32Array(MAX_DROPS), dropVX = new Float32Array(MAX_DROPS),
        dropVY = new Float32Array(MAX_DROPS), dropLive = new Uint8Array(MAX_DROPS);
  let flying = 0, hovering = false, asleep = false, quiet = 0;
  const pointer = { x: -9999, y: -9999, vx: 0, vy: 0 };
  const amount = Math.min(MAX_FILL, Math.max(0, WATER_AMOUNT / 100)), ripple = RIPPLE;

  const [cr, cg, cb, ca] = parseColor(WATER_COLOR);
  const surfaceTone = `rgba(${shift(cr,0.45)}, ${shift(cg,0.45)}, ${shift(cb,0.45)}, ${ca})`;
  const bodyTone = `rgba(${cr}, ${cg}, ${cb}, ${ca})`;
  const depthTone = `rgba(${shift(cr,-0.35)}, ${shift(cg,-0.35)}, ${shift(cb,-0.35)}, ${ca})`;
  const glintTone = `rgba(${shift(cr,0.75)}, ${shift(cg,0.75)}, ${shift(cb,0.75)}, ${Math.min(1, ca + 0.25)})`;
  const [rr, rg, rb, ra] = parseColor(BORDER_COLOR);
  const borderTone = `rgba(${rr}, ${rg}, ${rb}, ${ra})`, borderBase = `rgba(${rr}, ${rg}, ${rb}, ${ra*0.35})`, borderFade = `rgba(${rr}, ${rg}, ${rb}, 0)`;
  const colX = i => (i + 0.5) * colW;

  function pixelScale() {
    const rect = root.getBoundingClientRect(); const zoom = rect.width > 1 && W > 1 ? rect.width / W : 1;
    let s = Math.min(MAX_PIXEL_SCALE, (window.devicePixelRatio || 1) * zoom);
    const area = Math.max(1, W * H); if (area * s * s > MAX_PIXELS) s = Math.sqrt(MAX_PIXELS / area);
    return Math.max(1, s);
  }
  function raster() { pixScale = pixelScale(); canvas.width = Math.round(W * pixScale); canvas.height = Math.round(H * pixScale); ctx.setTransform(pixScale,0,0,pixScale,0,0); }
  function build() {
    W = Math.max(2, root.clientWidth); H = Math.max(2, root.clientHeight); raster();
    colW = W / COLUMNS; fullRest = H * amount; rest = fullRest * lvl; h.fill(rest); u.fill(0); dropLive.fill(0); flying = 0; asleep = true; quiet = 0;
  }
  function freeze() { h.fill(rest); u.fill(0); dropLive.fill(0); flying = 0; asleep = true; quiet = 0; }

  function drive(dt) {
    const reach = CURSOR_REACH, kx = clampKick(pointer.vx) * 60, ky = clampKick(pointer.vy) * 60;
    const first = Math.max(1, Math.floor((pointer.x - reach) / colW)), lastI = Math.min(COLUMNS - 1, Math.ceil((pointer.x + reach) / colW));
    for (let i = first; i <= lastI; i++) {
      const dx = i * colW - pointer.x, fall = 1 - Math.abs(dx) / reach;
      if (fall <= 0) continue; if (pointer.y < H - h[i] - reach) continue;
      const bite = fall * ripple * dt; u[i] += kx * SWEEP_FORCE * bite; u[i] += Math.sign(dx) * ky * DIP_FORCE * bite;
    }
  }
  function splash(px) {
    const reach = CURSOR_REACH, first = Math.max(1, Math.floor((px - reach) / colW)), lastI = Math.min(COLUMNS - 1, Math.ceil((px + reach) / colW));
    for (let i = first; i <= lastI; i++) { const dx = i * colW - px, fall = 1 - Math.abs(dx) / reach; if (fall <= 0) continue; u[i] += Math.sign(dx || 1) * CLICK_FORCE * fall * ripple; }
  }
  function tear(i, vx, vy) {
    if (h[i] <= MIN_SPRAY_DEPTH) return; let slot = -1;
    for (let d = 0; d < MAX_DROPS; d++) if (!dropLive[d]) { slot = d; break; }
    if (slot < 0) return;
    dropLive[slot] = 1; flying++; dropX[slot] = colX(i); dropY[slot] = H - h[i] - DROP_RADIUS; dropVX[slot] = vx; dropVY[slot] = vy; h[i] -= DROP_VOLUME / colW;
  }
  function spray(dt) {
    if (hovering) {
      const kx = clampKick(pointer.vx), ky = clampKick(pointer.vy), speed = Math.abs(kx) + Math.abs(ky);
      if (speed > SPRAY_THRESHOLD) {
        const want = Math.min(SPRAY_PER_FRAME, Math.round((speed - SPRAY_THRESHOLD) * SPRAY_RATE * ripple));
        for (let k = 0; k < want; k++) {
          const x = pointer.x + (Math.random() - 0.5) * CURSOR_REACH * 0.7;
          const i = Math.max(0, Math.min(COLUMNS - 1, Math.floor(x / colW)));
          if (pointer.y < H - h[i] - CURSOR_REACH * 0.5) continue;
          tear(i, kx * 60 * 0.45 + (Math.random() - 0.5) * 70, -(SPRAY_LIFT * (0.6 + Math.random() * 0.9)) + ky * 60 * 0.25);
        }
      }
    }
    for (let i = 1; i < COLUMNS - 1; i++) {
      const flow = Math.abs(u[i]); if (flow < BREAK_SPEED) continue;
      if (Math.random() > (flow - BREAK_SPEED) * 0.004 * ripple * dt * 60) continue;
      tear(i, u[i] * 0.5 + (Math.random() - 0.5) * 40, -(SPRAY_LIFT * 0.5 * (0.5 + Math.random())));
    }
  }
  function fall(dt) {
    if (flying === 0) return;
    for (let d = 0; d < MAX_DROPS; d++) {
      if (!dropLive[d]) continue;
      dropVY[d] += DROP_GRAVITY * dt; dropVX[d] -= dropVX[d] * Math.min(1, DROP_DRAG * dt);
      dropX[d] += dropVX[d] * dt; dropY[d] += dropVY[d] * dt;
      if (dropX[d] < 0) { dropX[d] = 0; dropVX[d] = -dropVX[d] * 0.35; } else if (dropX[d] > W) { dropX[d] = W; dropVX[d] = -dropVX[d] * 0.35; }
      const i = Math.max(0, Math.min(COLUMNS - 1, Math.floor(dropX[d] / colW)));
      if (dropVY[d] > 0 && dropY[d] >= H - h[i]) { h[i] += DROP_VOLUME / colW; if (i > 0 && i < COLUMNS) u[i] += dropVX[d] * 0.25; dropLive[d] = 0; flying--; }
    }
  }
  function step(dt) {
    spray(dt); fall(dt);
    const sub = dt / SUBSTEPS;
    for (let s = 0; s < SUBSTEPS; s++) {
      if (hovering) drive(sub);
      for (let i = 1; i < COLUMNS; i++) { u[i] += ((-GRAVITY * (h[i] - h[i-1])) / colW) * sub; u[i] -= u[i] * Math.min(1, VISCOSITY * sub); }
      u[0] = 0; u[COLUMNS] = 0;
      for (let i = 1; i < COLUMNS; i++) flux[i] = (u[i] > 0 ? h[i-1] : h[i]) * u[i];
      flux[0] = 0; flux[COLUMNS] = 0;
      for (let i = 0; i < COLUMNS; i++) { h[i] -= ((flux[i+1] - flux[i]) / colW) * sub; if (h[i] < 0) h[i] = 0; }
    }
    let worst = 0; for (let i = 0; i < COLUMNS; i++) { const off = Math.abs(h[i] - rest); if (off > worst) worst = off; }
    return worst;
  }
  function draw() {
    ctx.clearRect(0, 0, W, H); ctx.save(); roundRectPath(ctx, 0, 0, W, H, ROUNDED); ctx.clip();
    const surfaceAt = i => H - h[i];
    let maxH = 0; for (let i = 0; i < COLUMNS; i++) if (h[i] > maxH) maxH = h[i];
    if (maxH < 0.5 && flying === 0) { ctx.restore(); drawBorder(); return; }   // empty glass
    ctx.beginPath(); ctx.moveTo(0, surfaceAt(0)); for (let i = 0; i < COLUMNS; i++) ctx.lineTo(colX(i), surfaceAt(i));
    ctx.lineTo(W, surfaceAt(COLUMNS - 1)); ctx.lineTo(W, H); ctx.lineTo(0, H); ctx.closePath();
    const grad = ctx.createLinearGradient(0, H - rest, 0, H);
    grad.addColorStop(0, surfaceTone); grad.addColorStop(0.35, bodyTone); grad.addColorStop(1, depthTone);
    ctx.fillStyle = grad; ctx.fill();
    ctx.beginPath(); ctx.moveTo(0, surfaceAt(0)); for (let i = 0; i < COLUMNS; i++) ctx.lineTo(colX(i), surfaceAt(i));
    ctx.lineTo(W, surfaceAt(COLUMNS - 1)); ctx.strokeStyle = glintTone; ctx.lineWidth = 1.5; ctx.stroke();
    if (flying > 0) {
      ctx.beginPath();
      for (let d = 0; d < MAX_DROPS; d++) { if (!dropLive[d]) continue; ctx.moveTo(dropX[d] + DROP_RADIUS, dropY[d]); ctx.arc(dropX[d], dropY[d], DROP_RADIUS, 0, Math.PI * 2); }
      ctx.fillStyle = surfaceTone; ctx.fill();
    }
    ctx.restore();
    drawBorder();
  }
  function drawBorder() {
    if (!BORDER || BORDER_STROKE <= 0) return;
    const half = BORDER_STROKE / 2;
    roundRectPath(ctx, half, half, W - BORDER_STROKE, H - BORDER_STROKE, ROUNDED - half);
    ctx.lineWidth = BORDER_STROKE; ctx.strokeStyle = borderBase; ctx.stroke();
    const rim = ctx.createLinearGradient(W, H, 0, 0);
    rim.addColorStop(0, borderTone); rim.addColorStop(0.3, borderFade); rim.addColorStop(0.7, borderFade); rim.addColorStop(1, borderTone);
    ctx.strokeStyle = rim; ctx.stroke();
  }
  function loop(now) {
    if (!alive) return;
    const dt = last ? Math.min((now - last) / 1000, 1/30) : 1/60; last = now;
    pointer.vx *= 0.8; pointer.vy *= 0.8;
    const target = DRAINED ? 0 : 1;
    if (lvl !== target) {
      lvl = lvl > target ? Math.max(target, lvl - dt / DRAIN_SECONDS) : Math.min(target, lvl + dt / REFILL_SECONDS);
      const newRest = fullRest * lvl, d = newRest - rest;
      for (let i = 0; i < COLUMNS; i++) h[i] = Math.max(0, h[i] + d);
      rest = newRest; asleep = false; quiet = 0; saveLvl(); tintLabel();
    }
    if (!asleep) {
      const worst = step(dt); draw();
      if (!hovering && flying === 0 && worst < STILL) quiet++; else quiet = 0;
      if (quiet > SLEEP_FRAMES) { freeze(); draw(); }
    }
    raf = requestAnimationFrame(loop);
  }
  const wake = () => { asleep = false; quiet = 0; };
  const toLocal = e => { const rect = root.getBoundingClientRect(); return { x: (e.clientX - rect.left) * (rect.width > 0 ? W / rect.width : 1), y: (e.clientY - rect.top) * (rect.height > 0 ? H / rect.height : 1) }; };
  root.addEventListener("mouseenter", e => { hovering = true; const p = toLocal(e); pointer.x = p.x; pointer.y = p.y; pointer.vx = 0; pointer.vy = 0; wake(); });
  root.addEventListener("mousemove", e => { const p = toLocal(e); pointer.vx = p.x - pointer.x; pointer.vy = p.y - pointer.y; pointer.x = p.x; pointer.y = p.y; wake(); });
  root.addEventListener("mouseleave", () => { hovering = false; pointer.x = -9999; pointer.y = -9999; pointer.vx = 0; pointer.vy = 0; wake(); });
  root.addEventListener("pointerdown", e => { const p = toLocal(e); pointer.x = p.x; pointer.y = p.y; splash(p.x); wake(); });
  root.addEventListener("click", pressStreamlitSolve);
  root.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); splash(W / 2); wake(); pressStreamlitSolve(); } });
  new ResizeObserver(() => { build(); draw(); }).observe(root);
  setInterval(() => { if (Math.abs(pixelScale() - pixScale) < 0.02) return; raster(); draw(); }, 300);
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(() => { build(); draw(); });
  build(); draw(); raf = requestAnimationFrame(loop);
})();
</script></body></html>
'''

# Streamlit can't receive clicks from the water button directly, so a normal
# (hidden) Streamlit button does the real work and the water button presses it.
_HIDE_REAL_BUTTON = """
<style>
.st-key-solve_real { position: absolute !important; left: -9999px !important; height: 0 !important; overflow: hidden !important; }
</style>
"""


def solve_clicked():
    """Draws the hidden real Solve button. Returns True on the run when the water button was clicked."""
    st.markdown(_HIDE_REAL_BUTTON, unsafe_allow_html=True)
    return st.button("Solve", key="solve_real", type="primary")


def water_button(drained=False):
    """Draws the water button.
    drained=False -> glass is full.   drained=True -> the water slowly drains away.
    Going from True back to False makes the water fill up again."""
    components.html(_HTML.replace("__DRAINED__", "true" if drained else "false"), height=190)