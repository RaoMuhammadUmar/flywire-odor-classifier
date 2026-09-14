// =============================================================
// app.js — scene, camera, orchestrator, boot
// =============================================================

const wrap = document.getElementById("canvas-wrap");
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(40, innerWidth / innerHeight, 0.1, 200);

let camDist = 14, camAz = 0.55, camEl = 0.35;
function updateCamera() {
  camera.position.set(
    camDist * Math.cos(camEl) * Math.sin(camAz),
    camDist * Math.sin(camEl),
    camDist * Math.cos(camEl) * Math.cos(camAz)
  );
  camera.lookAt(0, 0, 0);
}
updateCamera();

const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.setSize(innerWidth, innerHeight);
wrap.appendChild(renderer.domElement);

addEventListener("resize", () => {
  camera.aspect = innerWidth / innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight);
});

// Lights
scene.add(new THREE.AmbientLight(0xffffff, 0.9));
const key = new THREE.DirectionalLight(0xfff2e0, 0.8); key.position.set(4, 6, 5); scene.add(key);
const rim = new THREE.DirectionalLight(0x6fd8ff, 0.4); rim.position.set(-5, 2, -4); scene.add(rim);

// ---------- Orchestration state ----------
let mode = "real";
let currentIdx = 0;
let autoPlay = false;
let autoPlayTimer = 0;

// Fallback blend (used only if dummy samples are missing)
let barSmooth = { orn: 0, pn: 0, kc: 0 };

function applyRealSample(i) {
  currentIdx = i;
  const s = DATA.samples[i];
  setBrainActivity(s.orn, s.pn, s.kc);
  updateReadoutPanel(s.orn, s.pn, s.kc);
  updatePredictionPanel(s.predictions);
  updatePerceptionPanel(s);
  updateStatePanel(s);

  const t = document.getElementById("truth");
  t.style.display = "flex";
  const isWine = s.true_label === 0;
  t.style.background = isWine ? "rgba(169,69,93,0.15)" : "rgba(201,138,31,0.15)";
  t.style.color = isWine ? "#e08a9c" : "#e0b25a";
  t.innerHTML = `<span>ground truth</span><b>${isWine ? "wine" : "industrial"}</b>`;

  document.getElementById("timeline").value = i;
  document.getElementById("playback-label").textContent = `#${i}`;
  const sel = document.getElementById("sample-sel");
  if (+sel.value !== i) sel.value = i;
}

function applyBlend(alpha) {
  if (DATA.dummy && DATA.dummy.length > 0) {
    const idx = Math.round(alpha * (DATA.dummy.length - 1));
    const s = DATA.dummy[idx];
    setBrainActivity(s.orn, s.pn, s.kc);
    updateReadoutPanel(s.orn, s.pn, s.kc);
    updatePredictionPanel(s.predictions);
    updatePerceptionPanel(s);
    document.getElementById("blend-label").textContent =
      `Wine ↔ industrial — α=${s.alpha.toFixed(2)}`;
    document.getElementById("truth").style.display = "none";
    document.getElementById("playback-label").textContent = `α=${s.alpha.toFixed(2)}`;
    return;
  }
  // Fallback: nearest real sample by ORN distance
  const orn = wineMean.map((v, i) => Math.round(lerp(v, indMean[i], alpha)));
  let best = 0, bestD = Infinity;
  DATA.samples.forEach((s, i) => {
    let d = 0;
    for (let k = 0; k < 20; k++) d += (s.orn[k] - orn[k]) ** 2;
    if (d < bestD) { bestD = d; best = i; }
  });
  const s = DATA.samples[best];
  setBrainActivity(orn, s.pn, s.kc);
  updateReadoutPanel(orn, s.pn, s.kc);
  updatePredictionPanel(s.predictions);
  updatePerceptionPanel(s);
  document.getElementById("blend-label").textContent =
    `Wine ↔ industrial — α=${alpha.toFixed(2)}`;
  document.getElementById("truth").style.display = "none";
}

// ---------- UI wiring ----------
function wireUI() {
  // === Element references ===
  const mReal = document.getElementById("m-real");
  const mBlend = document.getElementById("m-blend");
  const mHazard = document.getElementById("m-hazard");
  const realCtl = document.getElementById("real-ctl");
  const blendCtl = document.getElementById("blend-ctl");
  const hazardCtl = document.getElementById("hazard-ctl");
  const hazardSel = document.getElementById("hazard-sel");
  const hazardCompound = document.getElementById("hazard-compound");
  const hazardDesc = document.getElementById("hazard-desc");
  const sel = document.getElementById("sample-sel");
  const randBtn = document.getElementById("rand-btn");
  const slider = document.getElementById("blend-sld");
  const timeline = document.getElementById("timeline");
  const playBtn = document.getElementById("play-btn");

  // === Hazard category helpers ===
  const CATEGORIES = ["explosive", "drug", "toxic", "radioactive"];
  CATEGORIES.forEach(c => {
    const o = document.createElement("option");
    o.value = c;
    o.textContent = c.charAt(0).toUpperCase() + c.slice(1) + "s";
    hazardSel.appendChild(o);
  });

  function populateCompounds(cat) {
    hazardCompound.innerHTML = "";
    (DATA.extra_scents || []).forEach((sc, i) => {
      if (sc.category !== cat) return;
      const o = document.createElement("option");
      o.value = i;
      o.textContent = sc.name;
      hazardCompound.appendChild(o);
    });
    const first = hazardCompound.options[0];
    if (first) showHazard(+first.value);
  }

  function showHazard(idx) {
    const sc = DATA.extra_scents[idx];
    if (!sc) return;
    setBrainActivity(sc.orn, sc.pn, sc.kc);
    updateReadoutPanel(sc.orn, sc.pn, sc.kc);
    const fakeSample = {
      orn: sc.orn, pn: sc.pn, kc: sc.kc,
      predictions: {
        LogReg: {pred: 1, proba: 0.5},
        SVM:    {pred: 1, proba: 0.5},
        RF:     {pred: 1, proba: 0.5},
        MLP:    {pred: 1, proba: 0.5},
      }
    };
    updatePerceptionPanel(fakeSample);
    updateStatePanel(fakeSample);
    hazardDesc.textContent = sc.desc;
    document.getElementById("truth").style.display = "none";
    document.getElementById("playback-label").textContent = sc.name.slice(0, 20);
  }

  hazardSel.onchange = () => populateCompounds(hazardSel.value);
  hazardCompound.onchange = () => showHazard(+hazardCompound.value);

  // === Mode buttons ===
  mReal.onclick = () => {
    mode = "real";
    mReal.classList.add("active");
    mBlend.classList.remove("active");
    mHazard.classList.remove("active");
    realCtl.style.display = "block";
    blendCtl.style.display = "none";
    hazardCtl.style.display = "none";
    applyRealSample(+sel.value);
  };
  mBlend.onclick = () => {
    mode = "blend";
    mBlend.classList.add("active");
    mReal.classList.remove("active");
    mHazard.classList.remove("active");
    realCtl.style.display = "none";
    blendCtl.style.display = "block";
    hazardCtl.style.display = "none";
    applyBlend(+slider.value / 100);
  };
  mHazard.onclick = () => {
    mode = "hazard";
    mHazard.classList.add("active");
    mReal.classList.remove("active");
    mBlend.classList.remove("active");
    realCtl.style.display = "none";
    blendCtl.style.display = "none";
    hazardCtl.style.display = "block";
    populateCompounds(hazardSel.value);
  };

  // === Sample / random / slider / timeline / play / info ===
  sel.onchange = () => applyRealSample(+sel.value);
  randBtn.onclick = () => {
    const i = Math.floor(Math.random() * DATA.samples.length);
    sel.value = i;
    applyRealSample(i);
  };
  slider.oninput = () => applyBlend(+slider.value / 100);

  timeline.oninput = () => {
    if (mode === "real") applyRealSample(+timeline.value);
    else {
      const a = +timeline.value / 70;
      applyBlend(a);
      slider.value = a * 100;
    }
  };

  playBtn.onclick = () => {
    autoPlay = !autoPlay;
    playBtn.textContent = autoPlay ? "❚❚" : "▶";
    playBtn.classList.toggle("playing", autoPlay);
    autoPlayTimer = 999;
  };
  addEventListener("keydown", (e) => {
    if (e.code === "Space") { e.preventDefault(); playBtn.click(); }
  });

  const infoBtn = document.getElementById("info-btn");
  const infoPanel = document.getElementById("info-panel");
  infoBtn.onclick = () => {
    infoPanel.style.display = infoPanel.style.display === "block" ? "none" : "block";
  };
}



// ---------- Camera controls ----------
let dragging = false, lx = 0, ly = 0;
renderer.domElement.addEventListener("pointerdown", e => {
  dragging = true; lx = e.clientX; ly = e.clientY;
});
addEventListener("pointerup", () => dragging = false);
addEventListener("pointermove", e => {
  if (!dragging) return;
  camAz -= (e.clientX - lx) * 0.005;
  camEl = Math.max(-1.3, Math.min(1.3, camEl + (e.clientY - ly) * 0.004));
  lx = e.clientX; ly = e.clientY;
  updateCamera();
});
renderer.domElement.addEventListener("wheel", e => {
  camDist = Math.max(6, Math.min(40, camDist + e.deltaY * 0.008));
  updateCamera();
}, { passive: true });

// ---------- Animation loop ----------
const clock = new THREE.Clock();
let autoRotate = true;
renderer.domElement.addEventListener("pointerdown", () => autoRotate = false);

function animate() {
  requestAnimationFrame(animate);
  const dt = clock.getDelta();
  const t = clock.getElapsedTime();

  if (autoRotate) { camAz += dt * 0.05; updateCamera(); }

  if (autoPlay) {
    autoPlayTimer += dt;
    if (autoPlayTimer > 1.8) {
      autoPlayTimer = 0;
      if (mode === "real") {
        applyRealSample((currentIdx + 1) % DATA.samples.length);
      } else {
        const sld = document.getElementById("blend-sld");
        const next = (+sld.value + 5) % 105;
        sld.value = next > 100 ? 0 : next;
        applyBlend(sld.value / 100);
      }
    }
  }

  if (current.orn) {
    updateBrainVisuals();
    const m = getBrainRegionMeans();
    barSmooth.orn = barSmooth.orn * 0.85 + m.orn * 0.15;
    barSmooth.pn  = barSmooth.pn  * 0.85 + m.pn  * 0.15;
    barSmooth.kc  = barSmooth.kc  * 0.85 + m.kc  * 0.15;
    updateRegionBars(barSmooth);
  }

  if (ornLine) ornLine.material.opacity = 0.6 * (0.85 + 0.15 * Math.sin(t * 7));
  if (pnKcLine) pnKcLine.material.opacity = 0.22 * (0.85 + 0.15 * Math.sin(t * 5 + 1));

  renderer.render(scene, camera);
}

// ---------- Boot ----------
(async function init() {
  try {
    await loadBrainData();
    buildBrain(scene);
    const flyGroup = buildFlyBody();
    scene.add(flyGroup);

    populateSampleDropdown(DATA.samples);
    wireTabs();
    wireUI();
    applyRealSample(0);

    document.getElementById("stat-kc").textContent =
      DATA.meta.kc_total.toLocaleString();
    document.getElementById("loading").style.display = "none";
    animate();
  } catch (err) {
    document.getElementById("loading").textContent = "ERROR: " + err.message;
    console.error(err);
  }
})();