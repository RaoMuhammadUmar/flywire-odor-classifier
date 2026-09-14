// =============================================================
// brain_only.js — no external fly body. Pure neural network view.
// Returns an empty group so app.js can keep the same call shape.
// =============================================================

function buildFlyBody() {
  // External fly appearance intentionally removed.
  // The brain region (neurons + edges) is the entire visual.
  return new THREE.Group();
}
