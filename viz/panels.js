// =============================================================
// panels.js — tab UI, prediction, perception, analytics
// =============================================================

const CV_ACCURACY = { LogReg: 76.4, SVM: 83.0, RF: 81.9, MLP: 50.7 };

const PERCEPT_TEXTS = {
  wine: [
    "Sweet, fermented aroma. The fly's olfactory system responds like it would to ripe fruit — a food signal.",
    "Yeasty, fruity profile. Antennal lobe activity clusters in DM1, DM4, and DM5 — typical of fermentation volatiles.",
    "Fruity and acetous. The mushroom body encodes this as a beneficial, approach-worthy odor.",
  ],
  ind: [
    "Sharp, chemical signature. The antennal lobe lights up strongly — an aversive stimulus for the fly.",
    "Industrial solvent profile. ORN populations DM2, VM5d, and VM7d dominate the response.",
    "Toxic-cue signature. The circuit recruits a broad KC population, typical of unfamiliar or hazardous volatiles.",
  ],
};

function wireTabs() {
  const btns = document.querySelectorAll(".tab-btn");
  const panes = document.querySelectorAll(".tab-pane");
  btns.forEach(btn => btn.onclick = () => {
    btns.forEach(b => b.classList.remove("active"));
    panes.forEach(p => p.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById("pane-" + btn.dataset.tab).classList.add("active");
  });
}

function populateSampleDropdown(samples) {
  const sel = document.getElementById("sample-sel");
  sel.innerHTML = "";
  samples.forEach((s, i) => {
    const o = document.createElement("option");
    o.value = i;
    o.textContent = `#${i} — ${s.true_label === 0 ? "wine" : "industrial"}`;
    sel.appendChild(o);
  });
}

function updateReadoutPanel(orn, pn, kc) {
  document.getElementById("ro-orn").textContent =
    `${orn.filter(v => v > 80).length} / 20`;
  document.getElementById("ro-pn").textContent =
    `${pn.filter(v => v > 40).length} / ${DATA.meta.pn_total}`;
  document.getElementById("ro-kc").textContent =
    `${kc.filter(v => v > 40).length} / ${DATA.meta.kc_total.toLocaleString()}`;
  document.getElementById("ro-kcm").textContent =
    (kc.reduce((a,b)=>a+b,0) / kc.length).toFixed(0);
}

function updatePredictionPanel(preds) {
  const box = document.getElementById("model-bars");
  box.innerHTML = "";
  const names = ["LogReg", "SVM", "RF", "MLP"];
  let votes = 0;
  let bestModel = names[0], bestConf = 0;
  names.forEach(n => {
    const p = preds[n];
    if (p.pred === 1) votes++;
    const conf = Math.max(p.proba, 1 - p.proba);
    if (conf > bestConf) { bestConf = conf; bestModel = n; }
    const c = colorMap(p.proba);
    const hex = hexFromColor(c);
    const row = document.createElement("div");
    row.className = "mrow" + (n === bestModel ? " winner" : "");
    row.innerHTML =
      `<div class="top"><span>${n}</span><span>${(p.proba*100).toFixed(1)}%</span></div>
       <div class="bar-track"><div class="bar-fill"
         style="width:${(p.proba*100).toFixed(1)}%;background:${hex}"></div></div>`;
    box.appendChild(row);
  });
  const v = votes >= 3 ? "industrial" : (votes <= 1 ? "wine" : "split");
  const el = document.getElementById("verdict");
  el.textContent = v + (v !== "split"
    ? ` (${Math.max(votes, 4 - votes)}/4)`
    : " (2/4)");
  el.style.color = v === "industrial" ? "#e0b25a"
                : v === "wine" ? "#e08a9c"
                : "#c9cdd3";
  updateAnalyticsPanel(preds);
}

function updatePerceptionPanel(sample) {
  const preds = sample.predictions;
  const names = ["LogReg", "SVM", "RF", "MLP"];
  let votes = 0, sumP = 0;
  names.forEach(n => {
    if (preds[n].pred === 1) votes++;
    sumP += preds[n].proba;
  });
  const avgP = sumP / 4;
  const isInd = votes >= 3 || (votes === 2 && avgP > 0.55);
  const isWine = votes <= 1 || (votes === 2 && avgP < 0.45);

  const badge = document.getElementById("percept-badge");
  const desc = document.getElementById("percept-desc");
  const idx = Math.floor(Math.random() * 3);

  if (isInd) {
    badge.className = "percept-badge ind";
    badge.textContent = "⚠ Industrial / Hazardous";
    desc.textContent = PERCEPT_TEXTS.ind[idx];
  } else if (isWine) {
    badge.className = "percept-badge wine";
    badge.textContent = "🍇 Wine / Neutral";
    desc.textContent = PERCEPT_TEXTS.wine[idx];
  } else {
    badge.className = "percept-badge split";
    badge.textContent = "? Ambiguous";
    desc.textContent = "The models disagree. The odorant sits between the two class prototypes.";
  }

  // Dominant glomeruli chips
  const sensilla = DATA.meta.sensilla;
  const top = sample.orn
    .map((v, i) => [i, v])
    .sort((a, b) => b[1] - a[1])
    .slice(0, 6);
  const chipBox = document.getElementById("percept-chips");
  chipBox.innerHTML = "";
  top.forEach(([i, v]) => {
    const chip = document.createElement("span");
    chip.className = "chip" + (v > 150 ? " hot" : "");
    chip.textContent = `${sensilla[i]} (${v})`;
    chipBox.appendChild(chip);
  });

  // Sensory stats
  const statsBox = document.getElementById("percept-stats");
  statsBox.innerHTML = "";
  const activeCount = sample.orn.filter(v => v > 80).length;
  const peak = Math.max(...sample.orn);
  const mean = sample.orn.reduce((a, b) => a + b, 0) / 20;
  [
    ["Active glomeruli", `${activeCount} / 20`],
    ["Peak response", `${peak} Hz`],
    ["Mean response", `${mean.toFixed(0)} Hz`],
    ["Model agreement", `${Math.max(votes, 4 - votes)} / 4`],
  ].forEach(([k, v]) => {
    const line = document.createElement("div");
    line.className = "stat-line";
    line.innerHTML = `<span>${k}</span><b>${v}</b>`;
    statsBox.appendChild(line);
  });
}

function updateAnalyticsPanel(preds) {
  const rankBox = document.getElementById("analytics-rank");
  if (!rankBox) return;
  rankBox.innerHTML = "";
  const names = ["LogReg", "SVM", "RF", "MLP"];
  const ranked = names
    .map(n => {
      const p = preds[n];
      return {
        name: n,
        conf: Math.max(p.proba, 1 - p.proba),
        pred: p.pred,
      };
    })
    .sort((a, b) => b.conf - a.conf);

  ranked.forEach((r, i) => {
    const row = document.createElement("div");
    row.className = "model-rank" + (i === 0 ? " winner" : "");
    row.innerHTML =
      `<span class="rank">#${i+1}</span>
       <span class="name">${r.name}</span>
       <span class="acc">${(r.conf*100).toFixed(1)}% ${r.pred === 1 ? "▲" : "▼"}</span>`;
    rankBox.appendChild(row);
  });

  const trainBox = document.getElementById("analytics-train");
  if (trainBox && trainBox.innerHTML === "") {
    names.forEach(n => {
      const row = document.createElement("div");
      row.className = "stat-line";
      row.innerHTML = `<span>${n} (5-fold CV)</span><b>${CV_ACCURACY[n].toFixed(1)}%</b>`;
      trainBox.appendChild(row);
    });
  }

  const dataBox = document.getElementById("analytics-data");
  if (dataBox && dataBox.innerHTML === "") {
    [
      ["Source", "de Bruyne 2014 (CSIRO)"],
      ["Classes", "wine · industrial"],
      ["Samples", "71 total"],
      ["Features", "20 sensilla"],
      ["Connectome", "FAFB v783"],
    ].forEach(([k, v]) => {
      const row = document.createElement("div");
      row.className = "stat-line";
      row.innerHTML = `<span>${k}</span><b>${v}</b>`;
      dataBox.appendChild(row);
    });
  }
}

function updateRegionBars(means) {
  document.getElementById("bar-orn").style.width = (means.orn * 100).toFixed(0) + "%";
  document.getElementById("bar-pn").style.width  = (means.pn  * 100).toFixed(0) + "%";
  document.getElementById("bar-kc").style.width  = (means.kc  * 100).toFixed(0) + "%";
  document.getElementById("val-orn").textContent = (means.orn * 100).toFixed(0) + "%";
  document.getElementById("val-pn").textContent  = (means.pn  * 100).toFixed(0) + "%";
  document.getElementById("val-kc").textContent  = (means.kc  * 100).toFixed(0) + "%";
}

// =============================================================
// Neural state classification
// =============================================================

const STATE_LABELS = {
  null: {
    name: "Null",
    color: "#6a7080",
    badge: "— Null response",
    desc: "The antenna detects essentially nothing. To the fly, this stimulus does not exist — it has no receptor pathway that responds to it.",
  },
  resting: {
    name: "Resting",
    color: "#5c7a9c",
    badge: "· Resting",
    desc: "No clear sensory drive, but some intrinsic mushroom-body activity. The fly is not attending to anything in particular.",
  },
  attentive: {
    name: "Attentive",
    color: "#45e0c9",
    badge: "~ Attentive",
    desc: "A focused signal from one or two ORN channels. The signal propagates to the mushroom body and recruits a small KC ensemble. The fly has detected a specific, recognizable molecule.",
  },
  alert: {
    name: "Alert",
    color: "#f2b705",
    badge: "! Alert",
    desc: "Multiple sensory channels activate simultaneously. The signal propagates cleanly, and a broad KC ensemble fires. The fly perceives a rich, complex odor — the kind of pattern that drives approach or avoidance behaviour.",
  },
  saturated: {
    name: "Saturated",
    color: "#e07b3a",
    badge: "▲ Saturated",
    desc: "Receptors fire heavily but the signal does not propagate cleanly to the mushroom body. There is a bottleneck between the antenna and the brain — the fly is being flooded at the receptor level.",
  },
  overwhelmed: {
    name: "Overwhelmed",
    color: "#e04a2c",
    badge: "⚠ Overwhelmed",
    desc: "Extremely broad activation across all three layers. The circuit fires in a diffuse, undifferentiated pattern — a response shape the fly rarely produces for anything it has evolved to recognise.",
  },
};

function classifyState(orn, pn, kc) {
  const ornMean = orn.reduce((a, b) => a + b, 0) / orn.length / 255;
  const pnMean  = pn.reduce((a, b) => a + b, 0) / pn.length / 255;
  const kcMean  = kc.reduce((a, b) => a + b, 0) / kc.length / 255;
  const kcActive = kc.filter(v => v > 30).length;

  let key;
  if (ornMean < 0.05 && pnMean < 0.05 && kcMean < 0.05)          key = "null";
  else if (ornMean > 0.25 && pnMean < 0.08)                       key = "saturated";
  else if (ornMean > 0.30 && pnMean > 0.15 && kcMean > 0.15)      key = "overwhelmed";
  else if (ornMean > 0.18 && kcMean > 0.08)                       key = "alert";
  else if (ornMean < 0.10 && kcMean > 0.06)                       key = "resting";
  else                                                             key = "attentive";

  return {
    ...STATE_LABELS[key],
    key, ornMean, pnMean, kcMean,
    breadth: ornMean * pnMean,
    kcActive,
    kcActiveFrac: kcActive / kc.length,
  };
}

function updateStatePanel(sample) {
  const s = classifyState(sample.orn, sample.pn, sample.kc);

  const badge = document.getElementById("state-badge");
  badge.textContent = s.badge;
  badge.style.background = s.color + "26";
  badge.style.color = s.color;
  badge.style.border = "1px solid " + s.color + "66";

  document.getElementById("state-desc").textContent = s.desc;

  document.getElementById("signal-orn").style.width = (s.ornMean * 100).toFixed(0) + "%";
  document.getElementById("signal-pn").style.width  = (s.pnMean  * 100).toFixed(0) + "%";
  document.getElementById("signal-kc").style.width  = (s.kcMean  * 100).toFixed(0) + "%";

  // Propagation efficiency = how much ORN signal reaches the MB
  const prop = s.ornMean > 0.01 ? Math.min(1, s.pnMean / s.ornMean) : 0;
  const propEl = document.getElementById("state-prop");
  propEl.textContent = (prop * 100).toFixed(0) + "%";
  propEl.style.color = prop < 0.10 ? "#e07b3a"
                     : prop > 0.40 ? "#45e0c9"
                     : "#e8e6df";

  // Breadth — how many ORN channels contribute
  const activeOrn = sample.orn.filter(v => v > 50).length;
  document.getElementById("state-breadth").textContent =
    `${activeOrn} / 20 channels`;

  // KC ensemble
  document.getElementById("state-kc-ens").textContent =
    `${s.kcActive.toLocaleString()} cells`;
}