"""dot_background.py - black background with animated white dots (used on the login page)."""
import streamlit.components.v1 as components

_HTML = r'''
<script>
(function () {
  const P = (window.parent && window.parent !== window) ? window.parent : window;
  const D = P.document;
  if (P.__sudokuBg) { try { P.__sudokuBg(); } catch (e) {} }

  const css = D.createElement('style'); css.id = 'sudoku-bg-css';
  css.textContent = `
    html { background: #000 !important; }
    body { background: transparent !important; }
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stMain"] { background: transparent !important; }
  `;
  const oldCss = D.getElementById('sudoku-bg-css'); if (oldCss) oldCss.remove();
  D.head.appendChild(css);

  const old = D.getElementById('sudoku-bg-canvas'); if (old) old.remove();
  const wrap = D.createElement('div'); wrap.id = 'sudoku-bg-canvas';
  wrap.style.cssText = 'position:fixed;inset:0;z-index:-1;background:#000;pointer-events:none;';
  const canvas = D.createElement('canvas');
  canvas.style.cssText = 'position:absolute;inset:0;width:100%;height:100%;display:block;';
  const vig = D.createElement('div');
  vig.style.cssText = 'position:absolute;inset:0;background:radial-gradient(circle at center,rgba(0,0,0,0.75) 0%,rgba(0,0,0,0) 100%);';
  wrap.appendChild(canvas); wrap.appendChild(vig); D.body.prepend(wrap);

  const gl = canvas.getContext('webgl2', { alpha: true, antialias: false });
  if (!gl) { return; }

  const VERT = `#version 300 es
precision highp float;
in vec2 aPos;
uniform vec2 u_resolution;
out vec2 fragCoord;
void main() {
  gl_Position = vec4(aPos, 0.0, 1.0);
  fragCoord = (aPos + 1.0) * 0.5 * u_resolution;
  fragCoord.y = u_resolution.y - fragCoord.y;
}`;
  const FRAG = `#version 300 es
precision highp float;
in vec2 fragCoord;
uniform float u_time;
uniform float u_opacities[10];
uniform vec3 u_colors[6];
uniform float u_total_size;
uniform float u_dot_size;
uniform vec2 u_resolution;
out vec4 fragColor;
float PHI = 1.61803398874989484820459;
float random(vec2 xy) { return fract(tan(distance(xy * PHI, xy) * 0.5) * xy.x); }
void main() {
  vec2 st = fragCoord.xy;
  st.x -= abs(floor((mod(u_resolution.x, u_total_size) - u_dot_size) * 0.5));
  st.y -= abs(floor((mod(u_resolution.y, u_total_size) - u_dot_size) * 0.5));
  float opacity = step(0.0, st.x) * step(0.0, st.y);
  vec2 st2 = vec2(int(st.x / u_total_size), int(st.y / u_total_size));
  float frequency = 5.0;
  float show_offset = random(st2);
  float rand = random(st2 * floor((u_time / frequency) + show_offset + frequency));
  opacity *= u_opacities[int(rand * 10.0)];
  opacity *= 1.0 - step(u_dot_size / u_total_size, fract(st.x / u_total_size));
  opacity *= 1.0 - step(u_dot_size / u_total_size, fract(st.y / u_total_size));
  vec3 color = u_colors[int(show_offset * 6.0)];
  float animation_speed_factor = 3.0;
  vec2 center_grid = u_resolution / 2.0 / u_total_size;
  float dist_from_center = distance(center_grid, st2);
  float timing_offset_intro = dist_from_center * 0.01 + (random(st2) * 0.15);
  opacity *= step(timing_offset_intro, u_time * animation_speed_factor);
  opacity *= clamp((1.0 - step(timing_offset_intro + 0.1, u_time * animation_speed_factor)) * 1.25, 1.0, 1.25);
  fragColor = vec4(color, opacity);
  fragColor.rgb *= fragColor.a;
}`;
  const sh = (t, s) => { const x = gl.createShader(t); gl.shaderSource(x, s); gl.compileShader(x);
    if (!gl.getShaderParameter(x, gl.COMPILE_STATUS)) console.error(gl.getShaderInfoLog(x)); return x; };
  const prog = gl.createProgram();
  gl.attachShader(prog, sh(gl.VERTEX_SHADER, VERT)); gl.attachShader(prog, sh(gl.FRAGMENT_SHADER, FRAG));
  gl.linkProgram(prog);
  if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) { console.error(gl.getProgramInfoLog(prog)); return; }
  gl.useProgram(prog);
  const buf = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, buf);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1, 1,-1, -1,1, -1,1, 1,-1, 1,1]), gl.STATIC_DRAW);
  const loc = gl.getAttribLocation(prog, 'aPos'); gl.enableVertexAttribArray(loc); gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
  const U = n => gl.getUniformLocation(prog, n);
  gl.uniform1fv(U('u_opacities'), new Float32Array([0.3,0.3,0.3,0.5,0.5,0.5,0.8,0.8,0.8,1.0]));
  gl.uniform3fv(U('u_colors'), new Float32Array(18).fill(1));
  gl.uniform1f(U('u_total_size'), 20.0); gl.uniform1f(U('u_dot_size'), 6.0);
  gl.enable(gl.BLEND); gl.blendFunc(gl.SRC_ALPHA, gl.ONE);
  const uTime = U('u_time'), uRes = U('u_resolution');

  const resize = () => {
    const dpr = Math.min(P.devicePixelRatio || 1, 2);
    canvas.width = Math.round(P.innerWidth * dpr); canvas.height = Math.round(P.innerHeight * dpr);
    gl.viewport(0, 0, canvas.width, canvas.height);
    gl.uniform2f(uRes, P.innerWidth * 2, P.innerHeight * 2);
  };
  resize(); P.addEventListener('resize', resize);
  const start = performance.now(); let raf = 0;
  const frame = () => {
    raf = P.requestAnimationFrame(frame);
    gl.uniform1f(uTime, (performance.now() - start) / 1000);
    gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT);
    gl.drawArrays(gl.TRIANGLES, 0, 6);
  };
  raf = P.requestAnimationFrame(frame);
  P.__sudokuBg = () => { P.cancelAnimationFrame(raf); P.removeEventListener('resize', resize); wrap.remove(); };
})();
</script>
'''


def add_dot_background():
    components.html(_HTML, height=0)
