// =============================================================
// brain.js — internal neurons, edges, spiking animation
// =============================================================

const BRAIN_SCALE = 0.55;          // shrink so brain fits inside head
const TRANSITION_SPEED = 0.08;

let DATA = null;
let wineMean = null, indMean = null;

let brainGroup = null;
let ornPts = null, pnPts = null, kcPts = null;
let ornLine = null, pnKcLine = null;

// Activity state: target = what we want, current = smoothed toward target
const target  = { orn: null, pn: null, kc: null };
const current = { orn: null, pn: null, kc: null };
const pulses  = { orn: null, pn: null, kc: null };

async function loadBrainData() {
  const r = await fetch("brain_data.json");
  DATA = await r.json();

  // Compute class means for the fallback blend
  const wineIdx = [], indIdx = [];
  DATA.samples.forEach(s => s.true_label === 0 ? wineIdx.push(s) : indIdx.push(s));
  wineMean = new Array(20).fill(0);
  indMean  = new Array(20).fill(0);
  wineIdx.forEach(s => s.orn.forEach((v, i) => wineMean[i] += v));
  indIdx.forEach(s => s.orn.forEach((v, i) => indMean[i] += v));
  wineMean = wineMean.map(v => v / wineIdx.length);
  indMean  = indMean.map(v => v / indIdx.length);
}

function makePoints(positions, size, baseCol) {
  const g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  const n = positions.length / 3;
  const colors = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) {
    colors[i*3] = baseCol[0];
    colors[i*3+1] = baseCol[1];
    colors[i*3+2] = baseCol[2];
  }
  g.setAttribute("color", new THREE.BufferAttribute(colors, 3));
  return new THREE.Points(g, new THREE.PointsMaterial({
    size, map: DOT_TEXTURE, vertexColors: true, transparent: true,
    opacity: 0.95, depthWrite: false,
    blending: THREE.AdditiveBlending, sizeAttenuation: true,
  }));
}

function buildBrain(scene) {
  brainGroup = new THREE.Group();
  brainGroup.scale.set(BRAIN_SCALE, BRAIN_SCALE, BRAIN_SCALE);
  scene.add(brainGroup);

  ornPts = makePoints(DATA.neurons.orn.positions, 0.22, [0.27, 0.88, 0.79]);
  pnPts  = makePoints(DATA.neurons.pn.positions,  0.18, [0.48, 0.62, 0.88]);
  kcPts  = makePoints(DATA.neurons.kc.positions,  0.16, [0.95, 0.72, 0.02]);
  brainGroup.add(ornPts, pnPts, kcPts);

  buildBrainEdges();

  // Init state arrays
  const nOrn = DATA.neurons.orn.positions.length / 3;
  const nPn  = DATA.neurons.pn.positions.length / 3;
  const nKc  = DATA.neurons.kc.positions.length / 3;
  pulses.orn = new Float32Array(nOrn);
  pulses.pn  = new Float32Array(nPn);
  pulses.kc  = new Float32Array(nKc);
  target.orn = new Float32Array(20);
  target.pn  = new Float32Array(nPn);
  target.kc  = new Float32Array(nKc);
  current.orn = new Float32Array(20);
  current.pn  = new Float32Array(nPn);
  current.kc  = new Float32Array(nKc);
}

function buildBrainEdges() {
  const ornPos = DATA.neurons.orn.positions;
  const pnPos  = DATA.neurons.pn.positions;
  const kcPos  = DATA.neurons.kc.positions;
  const e1 = DATA.edges.orn_pn;
  const e2 = DATA.edges.pn_kc;

  // ORN -> PN
  const p1 = new Float32Array((e1.length / 3) * 6);
  for (let i = 0, j = 0; i < e1.length; i += 3, j += 6) {
    const oi = e1[i] * 3, pi = e1[i+1] * 3;
    p1[j]   = ornPos[oi];   p1[j+1] = ornPos[oi+1]; p1[j+2] = ornPos[oi+2];
    p1[j+3] = pnPos[pi];    p1[j+4] = pnPos[pi+1];  p1[j+5] = pnPos[pi+2];
  }
  const g1 = new THREE.BufferGeometry();
  g1.setAttribute("position", new THREE.BufferAttribute(p1, 3));
  g1.setAttribute("color", new THREE.BufferAttribute(new Float32Array((e1.length/3)*6), 3));
  ornLine = new THREE.LineSegments(g1, new THREE.LineBasicMaterial({
    vertexColors: true, transparent: true, opacity: 0.6,
    blending: THREE.AdditiveBlending, depthWrite: false,
  }));
  brainGroup.add(ornLine);

  // PN -> KC
  const p2 = new Float32Array((e2.length / 3) * 6);
  for (let i = 0, j = 0; i < e2.length; i += 3, j += 6) {
    const pi = e2[i] * 3, ki = e2[i+1] * 3;
    p2[j]   = pnPos[pi];    p2[j+1] = pnPos[pi+1];  p2[j+2] = pnPos[pi+2];
    p2[j+3] = kcPos[ki];    p2[j+4] = kcPos[ki+1];  p2[j+5] = kcPos[ki+2];
  }
  const g2 = new THREE.BufferGeometry();
  g2.setAttribute("position", new THREE.BufferAttribute(p2, 3));
  g2.setAttribute("color", new THREE.BufferAttribute(new Float32Array((e2.length/3)*6), 3));
  pnKcLine = new THREE.LineSegments(g2, new THREE.LineBasicMaterial({
    vertexColors: true, transparent: true, opacity: 0.22,
    blending: THREE.AdditiveBlending, depthWrite: false,
  }));
  brainGroup.add(pnKcLine);
}

// Set target activity — animation slides `current` toward it
function setBrainActivity(ornV, pnV, kcV) {
  for (let i = 0; i < 20; i++) target.orn[i] = ornV[i] / 255;
  const nPn = Math.min(pnV.length, target.pn.length);
  for (let i = 0; i < nPn; i++) target.pn[i] = pnV[i] / 255;
  const nKc = Math.min(kcV.length, target.kc.length);
  for (let i = 0; i < nKc; i++) target.kc[i] = kcV[i] / 255;
}

function updateBrainVisuals() {
  // Smooth toward target
  for (let i = 0; i < current.orn.length; i++)
    current.orn[i] += (target.orn[i] - current.orn[i]) * TRANSITION_SPEED;
  for (let i = 0; i < current.pn.length; i++)
    current.pn[i] += (target.pn[i] - current.pn[i]) * TRANSITION_SPEED;
  for (let i = 0; i < current.kc.length; i++)
    current.kc[i] += (target.kc[i] - current.kc[i]) * TRANSITION_SPEED;

  // ORNs
  const gn = DATA.neurons.orn.glom_idx;
  const oc = ornPts.geometry.attributes.color;
  for (let i = 0; i < gn.length; i++) {
    const act = current.orn[gn[i]];
    if (pulses.orn[i] <= 0) { if (Math.random() < act * act * 0.35) pulses.orn[i] = 1; }
    else { pulses.orn[i] -= 0.09; if (pulses.orn[i] < 0) pulses.orn[i] = 0; }
    const p = pulses.orn[i];
    const c = colorMap(act);
    oc.array[i*3]   = Math.min(1, c[0] + p * 0.8);
    oc.array[i*3+1] = Math.min(1, c[1] + p * 0.8);
    oc.array[i*3+2] = Math.min(1, c[2] + p * 0.8);
  }
  oc.needsUpdate = true;

  // PNs
  const pc = pnPts.geometry.attributes.color;
  for (let i = 0; i < current.pn.length; i++) {
    const act = current.pn[i];
    if (pulses.pn[i] <= 0) { if (Math.random() < act * act * 0.30) pulses.pn[i] = 1; }
    else { pulses.pn[i] -= 0.08; if (pulses.pn[i] < 0) pulses.pn[i] = 0; }
    const p = pulses.pn[i];
    const c = colorMap(act);
    pc.array[i*3]   = Math.min(1, c[0] + p * 0.75);
    pc.array[i*3+1] = Math.min(1, c[1] + p * 0.75);
    pc.array[i*3+2] = Math.min(1, c[2] + p * 0.75);
  }
  pc.needsUpdate = true;

  // KCs
  const kcC = kcPts.geometry.attributes.color;
  for (let i = 0; i < current.kc.length; i++) {
    const act = current.kc[i];
    if (pulses.kc[i] <= 0) { if (Math.random() < act * act * 0.22) pulses.kc[i] = 1; }
    else { pulses.kc[i] -= 0.07; if (pulses.kc[i] < 0) pulses.kc[i] = 0; }
    const p = pulses.kc[i];
    const c = colorMap(act);
    kcC.array[i*3]   = Math.min(1, c[0] + p * 0.7);
    kcC.array[i*3+1] = Math.min(1, c[1] + p * 0.7);
    kcC.array[i*3+2] = Math.min(1, c[2] + p * 0.7);
  }
  kcC.needsUpdate = true;

  // Edges
  const e1 = DATA.edges.orn_pn, c1 = ornLine.geometry.attributes.color;
  for (let i = 0, j = 0; i < e1.length; i += 3, j += 6) {
    const act = current.orn[gn[e1[i]]];
    const bright = act * e1[i+2] * 1.5;
    const c = colorMap(bright);
    c1.array[j]=c[0]; c1.array[j+1]=c[1]; c1.array[j+2]=c[2];
    c1.array[j+3]=c[0]; c1.array[j+4]=c[1]; c1.array[j+5]=c[2];
  }
  c1.needsUpdate = true;

  const e2 = DATA.edges.pn_kc, c2 = pnKcLine.geometry.attributes.color;
  for (let i = 0, j = 0; i < e2.length; i += 3, j += 6) {
    const act = current.pn[e2[i]];
    const bright = act * e2[i+2] * 2.0;
    const c = colorMap(bright);
    c2.array[j]=c[0]; c2.array[j+1]=c[1]; c2.array[j+2]=c[2];
    c2.array[j+3]=c[0]; c2.array[j+4]=c[1]; c2.array[j+5]=c[2];
  }
  c2.needsUpdate = true;
}

function getBrainRegionMeans() {
  let so = 0, sp = 0, sk = 0;
  for (let i = 0; i < current.orn.length; i++) so += current.orn[i];
  for (let i = 0; i < current.pn.length; i++) sp += current.pn[i];
  for (let i = 0; i < current.kc.length; i++) sk += current.kc[i];
  return {
    orn: so / current.orn.length,
    pn:  sp / current.pn.length,
    kc:  sk / current.kc.length,
  };
}