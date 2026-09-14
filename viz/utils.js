// =============================================================
// utils.js — shared constants and helpers
// =============================================================

const COLORMAP = [
  [0.02, 0.03, 0.06],
  [0.08, 0.28, 0.55],
  [0.20, 0.78, 0.72],
  [0.98, 0.70, 0.02],
  [1.00, 0.30, 0.04],
];

function colorMap(v) {
  const t = Math.max(0, Math.min(1, v)) * (COLORMAP.length - 1);
  const i = Math.floor(t), f = t - i;
  const a = COLORMAP[i], b = COLORMAP[Math.min(i + 1, COLORMAP.length - 1)];
  return [a[0] + (b[0]-a[0])*f, a[1] + (b[1]-a[1])*f, a[2] + (b[2]-a[2])*f];
}

const lerp = (a, b, t) => a + (b - a) * t;

function hexFromColor(c) {
  return "#" + c.map(x => Math.round(x*255).toString(16).padStart(2,"0")).join("");
}

function makeDotTexture() {
  const s = 64, c = document.createElement("canvas");
  c.width = c.height = s;
  const ctx = c.getContext("2d");
  const g = ctx.createRadialGradient(s/2, s/2, 0, s/2, s/2, s/2);
  g.addColorStop(0, "rgba(255,255,255,1)");
  g.addColorStop(0.35, "rgba(255,255,255,0.75)");
  g.addColorStop(1, "rgba(255,255,255,0)");
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, s, s);
  return new THREE.CanvasTexture(c);
}

const DOT_TEXTURE = makeDotTexture();