/* La chasse aux zéros de Riemann : les maths (mêmes calculs que riemann_jeu.py).
   eta par l'algorithme de Borwein, puis zeta = eta / (1 - 2^(1-s)) ;
   à gauche de la ligne 1/2, on passe par le miroir de Riemann (équation fonctionnelle). */
"use strict";
(function (global) {
  const N = 120;
  const LOG2 = Math.log(2);
  const LOGPI = Math.log(Math.PI);

  // Poids de Borwein : W[k] = (-1)^k (1 - d_k / d_N), calculés par les queues de somme (précis).
  const logfact = new Float64Array(2 * N + 1);
  for (let k = 1; k <= 2 * N; k++) logfact[k] = logfact[k - 1] + Math.log(k);
  const L = new Float64Array(N + 1);
  for (let i = 0; i <= N; i++) L[i] = logfact[N + i - 1] + i * Math.log(4) - logfact[N - i] - logfact[2 * i];
  let Lmax = -Infinity;
  for (let i = 0; i <= N; i++) Lmax = Math.max(Lmax, L[i]);
  const terme = Array.from(L, (v) => Math.exp(v - Lmax));
  let total = 0;
  for (const v of terme) total += v;
  const W = new Float64Array(N);
  let queue = 0;
  for (let k = N; k >= 0; k--) {
    if (k < N) W[k] = (k % 2 === 0 ? 1 : -1) * queue / total;
    queue += terme[k];
  }
  const LOGK = Float64Array.from({ length: N }, (_, k) => Math.log(k + 1));

  function cmul(ar, ai, br, bi) { return [ar * br - ai * bi, ar * bi + ai * br]; }
  function cdiv(ar, ai, br, bi) {
    const d = br * br + bi * bi;
    return [(ar * br + ai * bi) / d, (ai * br - ar * bi) / d];
  }

  /** eta(s) = 1 - 1/2^s + 1/3^s - ...  → [re, im] */
  function eta(re, im) {
    let sr = 0, si = 0;
    for (let k = 0; k < N; k++) {
      const m = W[k] * Math.exp(-re * LOGK[k]);
      const a = -im * LOGK[k];
      sr += m * Math.cos(a);
      si += m * Math.sin(a);
    }
    return [sr, si];
  }

  function zetaDroite(re, im) {          // pour Re(s) >= 0,5
    const [er, ei] = eta(re, im);
    const m = Math.exp((1 - re) * LOG2), a = -im * LOG2;
    let dr = 1 - m * Math.cos(a), di = -m * Math.sin(a);
    if (Math.hypot(dr, di) < 1e-12) { dr = 1e-12; di = 0; }
    return cdiv(er, ei, dr, di);
  }

  const LANCZOS = [0.99999999999980993, 676.5203681218851, -1259.1392167224028,
    771.32342877765313, -176.61502916214059, 12.507343278686905,
    -0.13857109526572012, 9.9843695780195716e-6, 1.5056327351493116e-7];

  function gamma(ur, ui) {               // Gamma complexe (Lanczos), pour Re >= 0,5
    const zr = ur - 1, zi = ui;
    let xr = LANCZOS[0], xi = 0;
    for (let i = 1; i < 9; i++) {
      const [qr, qi] = cdiv(LANCZOS[i], 0, zr + i, zi);
      xr += qr; xi += qi;
    }
    const tr = zr + 7.5, ti = zi;
    const lr = Math.log(Math.hypot(tr, ti)), li = Math.atan2(ti, tr);
    const er = (zr + 0.5) * lr - zi * li - tr, ei = (zr + 0.5) * li + zi * lr - ti;
    const m = Math.sqrt(2 * Math.PI) * Math.exp(er);
    return cmul(m * Math.cos(ei), m * Math.sin(ei), xr, xi);
  }

  /** zeta(s) → [re, im] */
  function zeta(re, im) {
    if (re >= 0.5) return zetaDroite(re, im);
    const er = re * LOG2 + (re - 1) * LOGPI, ei = im * (LOG2 + LOGPI);
    const m = Math.exp(er);
    let f = [m * Math.cos(ei), m * Math.sin(ei)];
    const a = Math.PI * re / 2, b = Math.PI * im / 2;
    f = cmul(f[0], f[1], Math.sin(a) * Math.cosh(b), Math.cos(a) * Math.sinh(b));
    f = cmul(f[0], f[1], ...gamma(1 - re, -im));
    return cmul(f[0], f[1], ...zetaDroite(1 - re, -im));
  }

  /** Cherche le zéro de zeta le plus proche de s. → [re, im] ou null */
  function newtonZero(re, im, iters = 40) {
    const h = 1e-6;
    for (let n = 0; n < iters; n++) {
      const [fr, fi] = zeta(re, im);
      if (Math.hypot(fr, fi) < 1e-10) return [re, im];
      const [pr, pi] = zeta(re + h, im), [mr, mi] = zeta(re - h, im);
      const dr = (pr - mr) / (2 * h), di = (pi - mi) / (2 * h);
      if (dr === 0 && di === 0) return null;
      let [sr, si] = cdiv(fr, fi, dr, di);
      const t = Math.hypot(sr, si);
      if (t > 1) { sr /= t; si /= t; }
      re -= sr; im -= si;
    }
    const [fr, fi] = zeta(re, im);
    return Math.hypot(fr, fi) < 1e-8 ? [re, im] : null;
  }

  // Hauteurs des 10 premiers zéros (ils sont tous à 1/2 + hauteur × i).
  const ZEROS = [14.134725141734693, 21.022039638771555, 25.010857580145688,
    30.424876125859513, 32.935061587739189, 37.586178158825671,
    40.918719012147495, 43.327073280914999, 48.005150881167159,
    49.773832477672302];

  const DEGRADE = [[0, 0, 4], [40, 11, 84], [101, 21, 110], [159, 42, 99],
    [212, 72, 66], [245, 125, 21], [250, 193, 39], [252, 240, 150]];

  /** Couleur de la carte : noir = la machine sort 0, jaune clair = loin de 0. → [r, g, b] */
  function couleur(mag) {
    if (!Number.isFinite(mag)) mag = 1e6;
    const f = Math.min(Math.max(Math.tanh(mag / 1.6), 0), 1) * (DEGRADE.length - 1);
    const i = Math.min(Math.floor(f), DEGRADE.length - 2), a = f - i;
    return DEGRADE[i].map((c, j) => Math.floor((c * (1 - a) + DEGRADE[i + 1][j] * a) * 0.85));
  }

  const RZ = { N, W, eta, zeta, newtonZero, ZEROS, couleur };
  if (typeof module !== "undefined" && module.exports) module.exports = RZ;
  else global.RZ = RZ;
})(typeof window !== "undefined" ? window : globalThis);
