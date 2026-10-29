"""background.py - animated liquid background for the Streamlit site.

Usage in app.py:
    from background import add_background
    add_background()
(call it once, right after st.set_page_config)
"""
import streamlit.components.v1 as components

_HTML = r'''
<script>
(function () {
  const P = (window.parent && window.parent !== window) ? window.parent : window;
  const D = P.document;
  // clean up an older copy (Streamlit re-runs the script on every click)
  if (P.__sudokuBg) { try { P.__sudokuBg(); } catch (e) {} }

  // ---- page styling: make Streamlit transparent and put content on a dark glass panel
  const css = D.createElement('style'); css.id = 'sudoku-bg-css';
  css.textContent = `
    html { background: #060606 !important; }
    body { background: transparent !important; }
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stMain"] { background: transparent !important; }
    .block-container { background: rgba(6,6,6,0.72); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
      border: 1px solid rgba(255,255,255,0.08); border-radius: 24px; padding: 2rem 2.2rem 3rem !important; margin-top: 1.5rem; }
  `;
  const oldCss = D.getElementById('sudoku-bg-css'); if (oldCss) oldCss.remove();
  D.head.appendChild(css);

  const old = D.getElementById('sudoku-bg-canvas'); if (old) old.remove();
  const canvas = D.createElement('canvas'); canvas.id = 'sudoku-bg-canvas';
  canvas.style.cssText = 'position:fixed;inset:0;width:100vw;height:100vh;z-index:-1;display:block;pointer-events:none;';
  D.body.prepend(canvas);

  const gl = canvas.getContext('webgl2', { alpha: false, antialias: false, depth: false });
  if (!gl) { canvas.remove(); return; }

  const VERT = `#version 300 es
in vec2 aPos;
void main() { gl_Position = vec4(aPos, 0.0, 1.0); }`;
  const FRAG = `#version 300 es
precision highp float;
uniform vec2 uRes;
uniform float uTime;
uniform vec2 uMouse;
uniform float uHover;
uniform vec3 uBg;
uniform vec3 uBase;
uniform vec3 uAccent;
uniform float uScale;
uniform float uBands;
uniform float uThick;
uniform float uGloss;
uniform float uHoverK;
uniform vec3 uMagenta;
uniform vec3 uViolet;
uniform vec3 uYellow;
uniform vec3 uOrange;
uniform vec3 uFall;
uniform vec3 uShadow;
uniform vec3 uSheen;
uniform vec3 uGap;
uniform vec3 uChrome;
uniform float uFlow;
uniform float uPhase;
uniform float uDrift;
uniform float uAngle;
uniform float uWarp;
uniform float uFreq;
uniform int uOct;
uniform float uSeed;
uniform float uStretch;
uniform float uDrop;
uniform float uThin;
uniform float uOrangeShare;
uniform float uMaxW;
uniform float uFallW;
uniform float uFallFrac;
uniform float uLineGap;
uniform float uSpec;
uniform float uBump;
uniform float uLight;
uniform float uRad;
uniform float uGrain;
uniform float uVign;
out vec4 outColor;

vec2 hash2(vec2 p) {
    uvec2 q = uvec2(ivec2(p) + ivec2(8192));
    q = q * uvec2(1597334673u, 3812015801u);
    uint n = (q.x ^ q.y) * 1597334673u;
    uvec2 r = uvec2(n, (n ^ (n >> 15u)) * 2246822519u);
    return vec2(r >> 16u) / 32767.5 - 1.0;
}
float gnoise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = p - i;
    vec2 w = f * f * f * (f * (f * 6.0 - 15.0) + 10.0);
    float a = dot(hash2(i), f);
    float b = dot(hash2(i + vec2(1.0, 0.0)), f - vec2(1.0, 0.0));
    float c = dot(hash2(i + vec2(0.0, 1.0)), f - vec2(0.0, 1.0));
    float d = dot(hash2(i + vec2(1.0, 1.0)), f - vec2(1.0, 1.0));
    return mix(mix(a, b, w.x), mix(c, d, w.x), w.y);
}
const mat2 ROT = mat2(0.8, -0.6, 0.6, 0.8);
float fbm(vec2 p, int n) {
    float s = 0.0;
    float a = 0.5;
    for (int i = 0; i < 6; i++) {
        if (i >= n) break;
        s += a * gnoise(p);
        p = ROT * p * 2.03 + vec2(1.7, 9.2);
        a *= 0.45;
    }
    return s;
}

float field(vec2 p, vec2 c) {
    int lo = max(uOct - 1, 1);
    vec2 q = vec2(fbm(p + c, lo), fbm(p + vec2(5.2, 1.3) + vec2(-c.y, c.x), lo));
    vec2 r = vec2(fbm(p + uWarp * q + vec2(1.7, 9.2) + 1.5 * c.yx, lo),
                  fbm(p + uWarp * q + vec2(8.3, 2.8) - 1.3 * c, lo));
    return fbm(p + uWarp * r, uOct);
}
float seg(float x, float a, float b, float aa) {
    return clamp(smoothstep(a - aa, a + aa, x) - smoothstep(b - aa, b + aa, x), 0.0, 1.0);
}
void main() {
    vec2 res = max(uRes, vec2(1.0));
    vec2 uv = gl_FragCoord.xy / res;
    float aspect = res.x / res.y;
    vec2 P = (gl_FragCoord.xy - 0.5 * res) / res.y;

    vec2 M = (uMouse * res - 0.5 * res) / res.y;
    float hk = clamp(uHover, 0.0, 1.0) * uHoverK;
    vec2 dP = P - M;
    float rr = max(uRad * aspect, 1e-3);
    float pg = exp(-dot(dP, dP) / (rr * rr));
    P -= dP * pg * 0.45 * hk;

    float ph = 6.2831853 * uPhase;
    vec2 cyc = vec2(cos(ph), sin(ph));
    vec2 c = cyc * uFlow;
    vec2 dir = vec2(cos(uAngle), sin(uAngle));
    vec2 nrm = vec2(-dir.y, dir.x);
    float freq = uFreq / max(uScale, 0.05);
    vec2 p = vec2(dot(P, dir) / max(uStretch, 0.05), dot(P, nrm)) * freq;
    p += vec2(uSeed * 3.17, uSeed * 1.71) + uDrift * 3.0 * vec2(cyc.x, 0.5 * sin(2.0 * ph));

    float h = field(p, c);
    float hN = h * uBands * 2.0 + uSeed * 0.37;
    vec2 gp = vec2(dFdx(hN), dFdy(hN));
    float g = max(length(gp), 1e-5);
    vec2 gdir = gp / g;
    float id = floor(hN);
    float u = hN - id;
    float rnd = fract(sin(id * 91.37 + uSeed * 13.13) * 43758.5453);
    float kind = rnd < uDrop ? 0.0 : (rnd < uDrop + uThin ? 1.0 : (rnd < uDrop + uThin + uOrangeShare ? 2.0 : 3.0));
    float wk = kind > 2.5 ? 1.0 : (kind > 1.5 ? 0.16 : 0.42);
    float th = max(min(uThick, uMaxW * res.y * g) * wk, 1e-4);
    float fl = kind > 2.5 ? 1.0 : ((kind > 0.5 && kind < 1.5) ? 0.3 : 0.0);
    float fallLen = min(min(uFallFrac, uFallW * res.y * g) * fl, max(0.98 - th, 0.0));
    float x = u / th;
    float aa = g / th;

    vec3 L = normalize(vec3(cos(uLight), sin(uLight), 0.9));
    vec3 Hh = normalize(L + vec3(0.0, 0.0, 1.0));

    vec3 col = vec3(0.0);
    if (kind > 0.5) {
        float e0 = min(aa, 0.08);
        float G = uLineGap;
        vec3 lines = vec3(0.0);
        float cover = 0.0;
        if (kind > 2.5) {
            float a1 = seg(x, e0, 0.12, aa);
            float a2 = seg(x, 0.12 + G, 0.32, aa);
            float a3 = seg(x, 0.32 + G, 0.46, aa);
            float a4 = seg(x, 0.46 + G, 1.0, aa);
            float sheenBand = 1.0 - smoothstep(0.0, 0.08, abs(x - 0.66));
            lines = uAccent * a1
                  + mix(uMagenta, uViolet, smoothstep(0.12, 0.32, x)) * a2
                  + mix(uYellow, uOrange, 0.4 * smoothstep(0.32, 0.46, x)) * a3
                  + mix(mix(uBase, uSheen, 0.55 * sheenBand), uFall, smoothstep(0.72, 1.0, x)) * a4;
            cover = a1 + a2 + a3 + a4;
        } else if (kind > 1.5) {
            float a1 = seg(x, e0, 1.0, aa);
            lines = uOrange * a1;
            cover = a1;
        } else {
            float a1 = seg(x, e0, 0.3, aa);
            float a2 = seg(x, 0.3 + G * 2.0, 0.62, aa);
            float a3 = seg(x, 0.62 + G * 2.0, 1.0, aa);
            lines = uAccent * a1 + uMagenta * a2 + uBase * a3;
            cover = a1 + a2 + a3;
        }
        float inside = seg(x, e0, 1.0, aa);
        vec3 stackCol = lines + uGap * max(inside - cover, 0.0);
        float s = clamp(2.0 * x - 1.0, -1.0, 1.0);
        float hgt = sqrt(max(1.0 - s * s, 0.0));
        float slope = -s / max(hgt, 0.3);
        vec3 n = normalize(vec3(-gdir * slope * uBump, 1.0));
        float diff = max(dot(n, L), 0.0);
        float spec = pow(max(dot(n, Hh), 0.0), uSpec);
        stackCol *= mix(1.0, 0.65 + 0.55 * diff, 0.5 * uGloss);
        stackCol += uSheen * spec * uGloss * 0.75 * inside;
        col += stackCol;
        if (fallLen > 1e-4) {
            float y = clamp((u - th) / fallLen, 0.0, 1.0);
            float fall = exp(-4.0 * y) * (1.0 - y) * smoothstep(th - g, th + g, u);
            vec3 fc = mix(uFall, uShadow, smoothstep(0.0, 0.55, y)) * fall;
            vec3 nf = normalize(vec3(gdir * uBump * 1.5 * (1.0 - y), 1.0));
            float sf = pow(max(dot(nf, Hh), 0.0), max(uSpec * 0.5, 1.0));
            fc += uSheen * sf * uGloss * fall * 0.8;
            col += fc;
        }
    } else {
        float d = min(u, 1.0 - u) / g;
        col += uChrome * (1.0 - smoothstep(0.4, 1.4, d)) * 0.75;
        float d2 = abs(u - 0.5) / g;
        col += uViolet * (1.0 - smoothstep(0.3, 1.2, d2)) * 0.35;
    }

    float dense = smoothstep(0.25, 0.5, g);
    vec3 avg = uViolet * 0.14 + uChrome * 0.12 + uFall * 0.1;
    col = mix(col, avg, dense);

    col *= 1.0 + 0.3 * pg * hk;
    float v = smoothstep(0.3, 0.85, length(uv - 0.5) * 1.2);
    col *= 1.0 - uVign * v;
    col = uBg + col;
    float gr = fract(sin(dot(gl_FragCoord.xy + fract(uTime * 7.13) * 100.0, vec2(12.9898, 78.233))) * 43758.5453) - 0.5;
    col += gr * uGrain * 0.18;
    outColor = vec4(clamp(col, 0.0, 1.0), 1.0);
}`;

  const sh = (type, src) => { const s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) console.error(gl.getShaderInfoLog(s)); return s; };
  const prog = gl.createProgram();
  gl.attachShader(prog, sh(gl.VERTEX_SHADER, VERT));
  gl.attachShader(prog, sh(gl.FRAGMENT_SHADER, FRAG));
  gl.linkProgram(prog);
  if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) { console.error(gl.getProgramInfoLog(prog)); canvas.remove(); return; }
  gl.useProgram(prog);
  const buf = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, buf);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1, 3,-1, -1,3]), gl.STATIC_DRAW);
  const loc = gl.getAttribLocation(prog, 'aPos'); gl.enableVertexAttribArray(loc);
  gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
  const U = {}; const u = n => (n in U) ? U[n] : (U[n] = gl.getUniformLocation(prog, n));
  const hex = h => [1,3,5].map(i => parseInt(h.slice(i, i+2), 16) / 255);
  const rad = d => d * Math.PI / 180;

  // ---- settings (your preset). Change these numbers to restyle the background.
  const SPEED = 21;          // animation speed
  const RENDER_SCALE = 0.6;  // lower = faster on weak laptops (0.4 - 1)
  const set1 = (n, v) => gl.uniform1f(u(n), v);
  const set3 = (n, h) => { const c = hex(h); gl.uniform3f(u(n), c[0], c[1], c[2]); };
  function constants() {
    set1('uBands', 11); set1('uThick', 0.30); set1('uGloss', 0.25); set1('uHoverK', 41/50);
    set3('uMagenta', '#D43CFF'); set3('uViolet', '#5A3CFF'); set3('uYellow', '#FFD23A'); set3('uOrange', '#FF9A1E');
    set3('uFall', '#1E5AFF'); set3('uShadow', '#0A1450'); set3('uSheen', '#F2FAFF'); set3('uGap', '#0C0A2A'); set3('uChrome', '#5E6670');
    set1('uFlow', 0.45); set1('uDrift', 0.10); set1('uAngle', rad(-35)); set1('uWarp', 2.3); set1('uFreq', 1.2);
    gl.uniform1i(u('uOct'), 4); set1('uSeed', 7); set1('uStretch', 1.6); set1('uDrop', 0.22); set1('uThin', 0.26);
    set1('uOrangeShare', 0.14); set1('uMaxW', 0.06); set1('uFallW', 0.08); set1('uFallFrac', 0.34); set1('uLineGap', 0.03);
    set1('uSpec', 40); set1('uBump', 0.55); set1('uLight', rad(135)); set1('uRad', 0.15); set1('uGrain', 0); set1('uVign', 0);
    set3('uBg', '#060606'); set3('uBase', '#38F40B'); set3('uAccent', '#E93B60'); set1('uScale', 0.82);
  }
  constants();

  const resize = () => {
    canvas.width  = Math.max(1, Math.round(P.innerWidth  * RENDER_SCALE));
    canvas.height = Math.max(1, Math.round(P.innerHeight * RENDER_SCALE));
  };
  resize(); P.addEventListener('resize', resize);

  let mx = .5, my = .5, tx = .5, ty = .5, over = 0, hov = 0;
  const onMove = e => { tx = e.clientX / P.innerWidth; ty = 1 - e.clientY / P.innerHeight; over = 1; };
  const onLeave = () => { over = 0; };
  P.addEventListener('pointermove', onMove); D.addEventListener('pointerleave', onLeave);

  let clock = 0, phase = 0, raf = 0, last = -1;
  const frame = now => {
    raf = P.requestAnimationFrame(frame);
    const dt = last < 0 ? 0 : Math.min((now - last) / 1000, 1/20); last = now;
    const step = dt * (SPEED / 50);
    clock = (clock + step) % 3600; phase = (phase + step / 12) % 1;
    const k = 1 - Math.exp(-dt * 6);
    mx += (tx - mx) * k; my += (ty - my) * k; hov += (over - hov) * k;
    gl.viewport(0, 0, canvas.width, canvas.height);
    gl.uniform2f(u('uRes'), canvas.width, canvas.height);
    gl.uniform1f(u('uTime'), clock); gl.uniform1f(u('uPhase'), phase);
    gl.uniform2f(u('uMouse'), mx, my); gl.uniform1f(u('uHover'), hov);
    gl.drawArrays(gl.TRIANGLES, 0, 3);
  };
  raf = P.requestAnimationFrame(frame);

  P.__sudokuBg = () => {
    P.cancelAnimationFrame(raf);
    P.removeEventListener('resize', resize); P.removeEventListener('pointermove', onMove);
    D.removeEventListener('pointerleave', onLeave);
    canvas.remove();
  };
})();
</script>
'''


def add_background():
    # height=0: the tiny hidden frame only runs the script that draws the
    # background onto the main page.
    components.html(_HTML, height=0)
