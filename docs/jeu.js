/* La chasse aux zéros de Riemann : version web (même jeu que riemann_jeu.py).
   Souris, clavier ou doigt. Tout est dessiné en coordonnées virtuelles 1200 × 760. */
"use strict";
(() => {
  const VW = 1200, VH = 760;
  const FOND = "#0d1024", PANNEAU = "#161b3a", BORD = "#2c3566", TEXTE = "#eef1ff", GRIS = "#8f97c4";
  const JAUNE = "#ffd54f", BLEU = "#4fc3f7", VIOLET = "#b388ff", ROSE = "#ff5c8a", ROUGE = "#ff6e6e";
  const VERT = "#69f0ae", ORANGE = "#ffab40";
  const POLICE = '"Segoe UI", system-ui, -apple-system, "Helvetica Neue", Roboto, Arial, sans-serif';
  const PATREON = "https://www.patreon.com/c/snowdiablo";
  const TACTILE = window.matchMedia("(pointer: coarse)").matches;
  const K_ESPACE = TACTILE ? "bouton Lancer" : "ESPACE";
  const { zeta, eta, newtonZero, ZEROS, couleur } = window.RZ;

  const fr = (x, n = 2) => x.toFixed(n).replace(".", ",");
  const module = ([r, i]) => Math.hypot(r, i);
  const compteur = (n) => (n <= 3 ? `Zéros trouvés : ${n} / 3` : `Zéros trouvés : 3 / 3  (+${n - 3} bonus)`);
  function eclaircir(c, a = 0.3) {
    const v = [1, 3, 5].map((i) => parseInt(c.slice(i, i + 2), 16));
    return "#" + v.map((x) => Math.round(x + (255 - x) * a).toString(16).padStart(2, "0")).join("");
  }

  const cv = document.getElementById("jeu");
  const ctx = cv.getContext("2d");
  let echelle = 1;

  // ------------------------------------------------------------ dessin
  const D = {
    ligne(pts, coul, larg = 1, tirets = null) {
      ctx.beginPath();
      ctx.moveTo(pts[0], pts[1]);
      for (let i = 2; i < pts.length; i += 2) ctx.lineTo(pts[i], pts[i + 1]);
      ctx.strokeStyle = coul; ctx.lineWidth = larg; ctx.lineCap = "round";
      ctx.setLineDash(tirets || []); ctx.stroke(); ctx.setLineDash([]);
    },
    fleche(xa, ya, xb, yb, coul, larg, [d1, d2, d3] = [14, 18, 6]) {
      const n = Math.hypot(xb - xa, yb - ya);
      if (n < 0.5) return;
      const ux = (xb - xa) / n, uy = (yb - ya) / n;
      const nx = xb - ux * d1, ny = yb - uy * d1, bx = xb - ux * d2, by = yb - uy * d2;
      D.ligne([xa, ya, nx, ny], coul, larg);
      ctx.beginPath();
      ctx.moveTo(xb, yb); ctx.lineTo(bx - uy * d3, by + ux * d3); ctx.lineTo(nx, ny); ctx.lineTo(bx + uy * d3, by - ux * d3);
      ctx.closePath(); ctx.fillStyle = coul; ctx.fill();
    },
    rond(x, y, r, { fill, stroke, width = 1, tirets } = {}) {
      ctx.beginPath(); ctx.arc(x, y, Math.max(r, 0), 0, 2 * Math.PI);
      if (fill) { ctx.fillStyle = fill; ctx.fill(); }
      if (stroke) {
        ctx.strokeStyle = stroke; ctx.lineWidth = width; ctx.setLineDash(tirets || []); ctx.stroke(); ctx.setLineDash([]);
      }
    },
    rect(x0, y0, x1, y1, { fill, stroke, width = 1 } = {}) {
      if (fill) { ctx.fillStyle = fill; ctx.fillRect(x0, y0, x1 - x0, y1 - y0); }
      if (stroke) { ctx.strokeStyle = stroke; ctx.lineWidth = width; ctx.strokeRect(x0, y0, x1 - x0, y1 - y0); }
    },
    poly(pts, fill) {
      ctx.beginPath(); ctx.moveTo(pts[0], pts[1]);
      for (let i = 2; i < pts.length; i += 2) ctx.lineTo(pts[i], pts[i + 1]);
      ctx.closePath(); ctx.fillStyle = fill; ctx.fill();
    },
    texte(x, y, txt, taille = 18, gras = false, coul = TEXTE, ancre = "c", largeur = null) {
      ctx.font = `${gras ? "bold " : ""}${taille}px ${POLICE}`;
      ctx.fillStyle = coul; ctx.textBaseline = "middle";
      ctx.textAlign = ancre === "w" ? "left" : ancre === "e" ? "right" : "center";
      if (!largeur) { ctx.fillText(txt, x, y); return; }
      const lignes = [];
      let l = "";
      for (const m of txt.split(" ")) {
        const t = l ? `${l} ${m}` : m;
        if (l && ctx.measureText(t).width > largeur) { lignes.push(l); l = m; } else l = t;
      }
      lignes.push(l);
      lignes.forEach((li, i) => ctx.fillText(li, x, y + (i - (lignes.length - 1) / 2) * taille * 1.3));
    },
    etoile(x, y, r, coul = ROSE) {
      ctx.beginPath();
      for (let i = 0; i < 10; i++) {
        const a = -Math.PI / 2 + i * Math.PI / 5, rr = i % 2 === 0 ? r : r * 0.45;
        if (i === 0) ctx.moveTo(x + rr * Math.cos(a), y + rr * Math.sin(a));
        else ctx.lineTo(x + rr * Math.cos(a), y + rr * Math.sin(a));
      }
      ctx.closePath(); ctx.fillStyle = coul; ctx.fill(); ctx.strokeStyle = "white"; ctx.lineWidth = 1; ctx.stroke();
    },
  };

  // ------------------------------------------------------------ écrans
  class Ecran {
    constructor(jeu) { this.jeu = jeu; this.msg = []; this.msgCouleur = TEXTE; this.fini = false; }
    maj() {}
    dessiner() {}
    touche() {}
    relache() {}
    appui() {}
    glisse() {}
    lache() {}
    dire(lignes, coul = TEXTE) { this.msg = lignes; this.msgCouleur = coul; }
    cadre() {
      D.rect(0, 0, VW, 62, { fill: "#11163a" });
      D.texte(40, 32, this.constructor.TITRE, 26, true, JAUNE, "w");
      D.texte(1022, 32, `Niveau ${this.constructor.NUMERO} / 4`, 15, false, GRIS, "e");
      this.jeu.bouton(1040, 8, 1184, 56, "Menu", () => this.jeu.aller(0), BLEU, 19);   // grand : facile au doigt
      D.rect(40, 622, VW - 40, 742, { fill: "#1b2150", stroke: BORD, width: 2 });
      const y0 = 682 - (this.msg.length - 1) * 21;
      this.msg.forEach((l, i) => D.texte(70, y0 + i * 42, l, 24, i === 0, i === 0 ? this.msgCouleur : TEXTE, "w"));
      if (this.fini) this.jeu.bouton(950, 652, 1140, 712, "Suivant  ▶", () => this.jeu.suivant(), VERT);
    }
  }

  class Menu extends Ecran {
    touche(k) {
      if ("1234".includes(k)) this.jeu.aller(Number(k));
      else if (k === "Return") this.jeu.aller(1);
    }
    dessiner() {
      D.ligne([1080, 90, 1080, 700], VIOLET, 2, [6, 5]);
      ZEROS.forEach((z, i) => D.etoile(1080, 680 - z * 11.5, i < 5 ? 9 : 7));
      D.texte(560, 110, "La chasse aux zéros de Riemann", 40, true, JAUNE);
      D.texte(560, 168, "4 petits jeux pour VOIR les zéros de zeta.", 21);
      ["1    La machine zeta", "2    Le miroir", "3    Les flèches qui tournent", "4    π sort de nulle part"]
        .forEach((nom, i) => {
          const y = 240 + i * 92;
          this.jeu.bouton(260, y, 860, y + 68, nom, () => this.jeu.aller(i + 1), [BLEU, VIOLET, VERT, JAUNE][i], 24);
        });
      D.texte(560, 650, TACTILE ? "Touche un jeu pour commencer." : "Clique sur un jeu (ou appuie sur Entrée pour commencer).", 18, false, GRIS);
      D.texte(560, 690, TACTILE ? "Le bouton Menu, en haut, ramène ici." : "Échap = revenir ici à tout moment.", 18, false, GRIS);
    }
  }

  // Carte de |zeta| du niveau 1, calculée petit à petit (quelques lignes par image).
  function nouvelleCarte(M) {
    const L = 240, H = 247;
    const c = document.createElement("canvas");
    c.width = L; c.height = H;
    const cx = c.getContext("2d"), img = cx.createImageData(L, H);
    let y = 0;
    return {
      canvas: c, prete: false,
      avancer(budgetMs) {
        const t0 = performance.now();
        while (y < H && performance.now() - t0 < budgetMs) {
          const t = M.TMAX - (y + 0.5) / H * (M.TMAX - M.TMIN);
          for (let x = 0; x < L; x++) {
            const s = M.SMIN + (x + 0.5) / L * (M.SMAX - M.SMIN);
            const [r, g, b] = couleur(module(zeta(s, t)));
            const o = 4 * (y * L + x);
            img.data[o] = r; img.data[o + 1] = g; img.data[o + 2] = b; img.data[o + 3] = 255;
          }
          y++;
        }
        if (y >= H && !this.prete) { cx.putImageData(img, 0, 0); this.prete = true; }
      },
    };
  }

  class Machine extends Ecran {
    static TITRE = "1. La machine zeta";
    static NUMERO = 1;
    static G = [40, 95, 520, 588];
    static D = [600, 95, 1160, 588];
    // De 0 à 2 en largeur : à gauche de 0 il y a des zéros "faciles" (-2, -4...) dont la conjecture ne parle pas.
    static SMIN = 0; static SMAX = 2; static TMIN = 0; static TMAX = 35;
    static ECH = 85;
    static CAPTURE = 0.35;   // assez près de 0 : la machine "aimante" le zéro (testé : aucun faux zéro)
    static BRULANT = 0.38;   // au-dessus, le coin en bas à gauche (|zeta| ≈ 0,39) aurait l'air "brûlant" sans zéro

    constructor(jeu) {
      super(jeu);
      this.s = [1.5, 10];    // testé : suivre "plus chaud" depuis ici mène au 1er zéro
      this.val = zeta(...this.s);
      this.trace = [];
      this.trouves = [];
      this.fige = 0;
      this.sortir = false;
      this.chrono = 0;
      this.astuce = false;
      this.tient = false;
      if (!jeu.carte) jeu.carte = nouvelleCarte(Machine);
      this.dire([TACTILE ? "Fais glisser le point bleu avec ton doigt." : "Bouge le point bleu (souris ou flèches du clavier).",
        "But : amener le point jaune, à droite, sur le centre."]);
    }

    versPx([re, im]) {
      const M = Machine, [x0, y0, x1, y1] = M.G;
      return [x0 + (re - M.SMIN) / (M.SMAX - M.SMIN) * (x1 - x0), y1 - (im - M.TMIN) / (M.TMAX - M.TMIN) * (y1 - y0)];
    }
    depuisPx(x, y) {
      const M = Machine, [x0, y0, x1, y1] = M.G;
      return this.borner([M.SMIN + (x - x0) / (x1 - x0) * (M.SMAX - M.SMIN), M.TMIN + (y1 - y) / (y1 - y0) * (M.TMAX - M.TMIN)]);
    }
    borner([re, im]) {
      return [Math.min(Math.max(re, Machine.SMIN), Machine.SMAX), Math.min(Math.max(im, 0.3), Machine.TMAX)];
    }
    versDroite([re, im]) {
      const [X0, Y0, X1, Y1] = Machine.D;
      return [(X0 + X1) / 2 + re * Machine.ECH, (Y0 + Y1) / 2 - im * Machine.ECH];
    }

    appui(x, y) {
      const [x0, y0, x1, y1] = Machine.G;
      if (x >= x0 && x <= x1 && y >= y0 && y <= y1 && this.fige <= 0) { this.tient = true; this.s = this.depuisPx(x, y); }
    }
    glisse(x, y) { if (this.tient && this.fige <= 0) this.s = this.depuisPx(x, y); }
    lache() { this.tient = false; }

    maj(dt) {
      if (!this.jeu.carte.prete) this.jeu.carte.avancer(5);
      if (this.trouves.length < 3) this.chrono += dt;
      if (this.fige > 0) { this.fige -= dt; return; }
      const k = this.jeu.touches;
      const dr = 0.5 * dt * (k.has("Right") - k.has("Left")), di = 3 * dt * (k.has("Up") - k.has("Down"));
      if (dr || di) this.s = this.borner([this.s[0] + dr, this.s[1] + di]);
      this.val = zeta(...this.s);
      this.trace.push(this.val);
      if (this.trace.length > 70) this.trace.shift();
      const a = module(this.val);
      if (this.sortir) { if (a > 0.6) this.sortir = false; }
      else if (a < Machine.CAPTURE) this.capturer();
      if (this.chrono > 25 && !this.astuce && this.trouves.length < 3) {
        this.astuce = true;
        this.dire(["Astuce : pose le point sur la ligne pointillée 1/2,",
          TACTILE ? "puis fais-le monter tout doucement." : "puis monte doucement avec la flèche du haut."], ORANGE);
      }
    }

    capturer() {
      const z = newtonZero(...this.s);
      if (!z || Math.hypot(z[0] - this.s[0], z[1] - this.s[1]) > 1.5 || !(z[1] > Machine.TMIN && z[1] < Machine.TMAX)) {
        this.sortir = true;    // pas de zéro ici : on ne recalcule pas à chaque image
        return;
      }
      this.s = z; this.val = [0, 0]; this.fige = 1.2; this.sortir = true; this.tient = false;
      if (this.trouves.some((f) => Math.hypot(f[0] - z[0], f[1] - z[1]) < 1e-3)) {
        this.dire(["Celui-là, tu l'as déjà trouvé !", "Cherche plus haut ou plus bas sur la ligne."], ORANGE);
        return;
      }
      this.trouves.push(z);
      this.chrono = 0; this.astuce = false;
      const n = this.trouves.length;
      if (n < 3) {
        this.dire([`Zéro n°${n} trouvé : il est à ${fr(z[0], 3)} + ${fr(z[1])} i`,
          `${fr(z[0], 3)} = 1/2 : pile sur la ligne ! Encore ${3 - n} à trouver.`], VERT);
      } else {
        this.fini = true;
        this.dire(["Voici la carte : chaque trou noir est un zéro.", "Tous sur la ligne 1/2 ! Riemann dit : à l'infini aussi."], VERT);
      }
    }

    dessiner() {
      const [x0, y0, x1, y1] = Machine.G;
      D.texte((x0 + x1) / 2, 79, "Ce que tu donnes à la machine", 16, false, GRIS);
      D.rect(x0, y0, x1, y1, { fill: PANNEAU, stroke: BORD, width: 2 });
      if (this.fini && this.jeu.carte.prete) {
        ctx.imageSmoothingEnabled = true;
        ctx.drawImage(this.jeu.carte.canvas, x0, y0, x1 - x0, y1 - y0);
      }
      for (const h of [10, 20, 30]) {
        const [, y] = this.versPx([0, h]);
        D.ligne([x0 - 8, y, x0, y], GRIS);
        D.texte(x0 - 10, y, String(h), 13, false, GRIS, "e");
      }
      for (const [sg, lab] of [[0, "0"], [1, "1"], [2, "2"]]) {
        const [x] = this.versPx([sg, 0]);
        D.ligne([x, y0, x, y1], "#3a4580");
        D.texte(x, y1 + 14, lab, 15, false, GRIS);
      }
      const [xm] = this.versPx([0.5, 0]);
      D.ligne([xm, y0, xm, y1], VIOLET, 2, [6, 5]);
      D.texte(xm, y1 + 14, "1/2", 15, true, VIOLET);
      for (const z of this.trouves) D.etoile(...this.versPx(z), 11);
      const [x, y] = this.versPx(this.s);
      if (this.fige > 0) D.rond(x, y, 14 + (1.2 - this.fige) * 40, { stroke: VERT, width: 3 });
      D.rond(x, y, 11, { fill: BLEU, stroke: "white", width: 2 });

      D.texte(560, 330, "→", 40, true, GRIS);
      D.texte(560, 372, "zeta", 15, false, GRIS);

      const [X0, Y0, X1, Y1] = Machine.D;
      const cx = (X0 + X1) / 2, cy = (Y0 + Y1) / 2;
      D.texte(cx, 79, "Ce que la machine sort", 16, false, GRIS);
      D.rect(X0, Y0, X1, Y1, { fill: PANNEAU, stroke: BORD, width: 2 });
      D.ligne([X0, cy, X1, cy], "#3a4580");
      D.ligne([cx, Y0, cx, Y1], "#3a4580");
      const a = module(this.val);
      D.rond(cx, cy, Machine.CAPTURE * Machine.ECH, { stroke: a < Machine.BRULANT ? VERT : "#3f6f5a", width: 2, tirets: [4, 4] });
      D.texte(cx + 36, cy + 20, "0", 15, true, VERT, "w");
      for (const v of this.trace.slice(0, -1)) {
        const [tx, ty] = this.versDroite(v);
        if (tx > X0 && tx < X1 && ty > Y0 && ty < Y1) D.rond(tx, ty, 2.5, { fill: "#8a7330" });
      }
      let [ox, oy] = this.versDroite(this.val);
      const dehors = !(ox > X0 + 12 && ox < X1 - 12 && oy > Y0 + 12 && oy < Y1 - 12);
      ox = Math.min(Math.max(ox, X0 + 12), X1 - 12); oy = Math.min(Math.max(oy, Y0 + 12), Y1 - 12);
      D.rond(ox, oy, 11, { fill: JAUNE, stroke: dehors ? ROUGE : "white", width: 2 });

      const [mot, c] = a < Machine.BRULANT ? ["Brûlant !", ROUGE] : a < 1 ? ["Chaud", ORANGE] : a < 2 ? ["Tiède", JAUNE] : ["Froid", BLEU];
      D.rect(X0 + 14, Y0 + 14, X0 + 214, Y0 + 58, { fill: c });
      D.texte(X0 + 114, Y0 + 36, mot, 20, true, "#0b0e1f");
      D.texte(X1 - 16, Y0 + 36, compteur(this.trouves.length), 17, true, TEXTE, "e");
      D.texte(X1 - 16, Y1 - 22, `Distance au centre : ${fr(Math.min(a, 999))}`, 15, false, GRIS, "e");
      this.cadre();
    }
  }

  class Miroir extends Ecran {
    static TITRE = "2. Le miroir";
    static NUMERO = 2;
    static G = [40, 95, 640, 588];
    static SMIN = -0.5; static SMAX = 1.5; static TMIN = 0; static TMAX = 35;

    constructor(jeu) {
      super(jeu);
      this.s = [0.18, 20];
      this.anim = 0;
      this.tient = false;
      this.dire(["Ce point violet est un zéro imaginaire (pour l'exemple).",
        "Pose-le SUR le miroir pour qu'il n'ait plus de jumeau."]);
    }
    versPx([re, im]) {
      const M = Miroir, [x0, y0, x1, y1] = M.G;
      return [x0 + (re - M.SMIN) / (M.SMAX - M.SMIN) * (x1 - x0), y1 - (im - M.TMIN) / (M.TMAX - M.TMIN) * (y1 - y0)];
    }
    depuisPx(x, y) {
      const M = Miroir, [x0, y0, x1, y1] = M.G;
      return [M.SMIN + (x - x0) / (x1 - x0) * (M.SMAX - M.SMIN), M.TMIN + (y1 - y) / (y1 - y0) * (M.TMAX - M.TMIN)];
    }
    placer([re, im]) {
      const M = Miroir;
      re = Math.min(Math.max(re, M.SMIN + 0.02), M.SMAX - 0.02);
      im = Math.min(Math.max(im, 1), M.TMAX - 1);
      if (!this.fini && ((this.s[0] - 0.5) * (re - 0.5) <= 0 || Math.abs(re - 0.5) < 0.015)) {
        re = 0.5;
        this.fini = true; this.anim = 1.2; this.tient = false;
        this.dire(["Bravo : sur le miroir, le zéro est son propre reflet.",
          "Les vrais zéros (étoiles) sont tous collés au miroir."], VERT);
      }
      this.s = [re, im];
    }
    appui(x, y) {
      const [x0, y0, x1, y1] = Miroir.G;
      if (x >= x0 && x <= x1 && y >= y0 && y <= y1) { this.tient = true; this.placer(this.depuisPx(x, y)); }
    }
    glisse(x, y) { if (this.tient) this.placer(this.depuisPx(x, y)); }
    lache() { this.tient = false; }
    maj(dt) {
      this.anim = Math.max(0, this.anim - dt);
      const k = this.jeu.touches;
      const dr = 0.35 * dt * (k.has("Right") - k.has("Left")), di = 4 * dt * (k.has("Up") - k.has("Down"));
      if (dr || di) this.placer([this.s[0] + dr, this.s[1] + di]);
    }
    dessiner() {
      const [x0, y0, x1, y1] = Miroir.G;
      D.rect(x0, y0, x1, y1, { fill: PANNEAU, stroke: BORD, width: 2 });
      const [a] = this.versPx([0, 0]), [b] = this.versPx([1, 0]), [xm] = this.versPx([0.5, 0]);
      D.rect(a, y0, b, y1, { fill: "#1d2450" });
      D.ligne([xm, y0, xm, y1], "#3b2f6e", 16);
      D.ligne([xm, y0, xm, y1], VIOLET, 3);
      D.texte(xm, 79, "le miroir (la ligne 1/2)", 16, true, VIOLET);
      for (const [sg, lab] of [[0, "0"], [0.5, "1/2"], [1, "1"]]) {
        const [x] = this.versPx([sg, 0]);
        D.texte(x, y1 + 14, lab, 15, sg === 0.5, sg === 0.5 ? VIOLET : GRIS);
      }
      if (this.fini) for (const z of ZEROS) if (z < Miroir.TMAX) D.etoile(...this.versPx([0.5, z]), 11);
      const [x, y] = this.versPx(this.s);
      if (Math.abs(this.s[0] - 0.5) > 1e-9) {
        const [xj, yj] = this.versPx([1 - this.s[0], this.s[1]]);
        D.ligne([x, y, xj, yj], VIOLET, 2, [5, 5]);
        D.rond(xj, yj, 13, { stroke: VIOLET, width: 3 });
        D.texte(xj, yj - 30, "son jumeau", 15, true, VIOLET);
        D.rond(x, y, 13, { fill: VIOLET, stroke: "white", width: 2 });
        D.texte(x, y - 30, "zéro imaginaire", 15, true, TEXTE);
      } else {
        if (this.anim > 0) D.rond(x, y, 16 + (1.2 - this.anim) * 45, { stroke: VERT, width: 3 });
        D.rond(x, y, 19, { stroke: VIOLET, width: 3 });
        D.rond(x, y, 13, { fill: VIOLET, stroke: "white", width: 2 });
        D.texte(x + 28, y, "son propre reflet", 15, true, TEXTE, "w");
      }
      if (!this.fini) {
        D.texte(910, 150, "La règle du miroir", 24, true, VIOLET);
        D.texte(910, 200, "(trouvée par Riemann en 1859)", 16, false, GRIS);
        D.texte(910, 300, "Si un zéro est à côté du miroir, il a forcément un jumeau, pile en face.", 20, false, TEXTE, "c", 440);
        D.texte(910, 430, "Bouge le point violet : son jumeau le suit.", 20, false, TEXTE, "c", 440);
      } else this.jauge();
      this.cadre();
    }
    jauge() {
      D.texte(910, 100, "Ce qui est prouvé aujourd'hui", 20, true);
      const bx0 = 760, bx1 = 830, by0 = 140, by1 = 540, haut = (pc) => by1 - pc / 100 * (by1 - by0);
      D.rect(bx0, by0, bx1, by1, { fill: "#232a5a", stroke: BORD, width: 2 });
      D.rect(bx0, haut(67.2), bx1, by1, { fill: VERT });
      D.ligne([bx0 - 8, haut(41.7), bx1 + 8, haut(41.7)], ORANGE, 3);
      D.texte(bx1 + 20, haut(100) + 4, "100 % = Riemann (pas prouvé)", 16, true, GRIS, "w");
      D.texte(bx1 + 20, haut(67.2), "2026 : 67 % (avec Claude)", 17, true, VERT, "w");
      D.texte(bx1 + 20, haut(41.7), "avant : 41 %", 17, true, ORANGE, "w");
      D.texte(910, 568, "Les autres zéros ? Personne ne sait encore.", 16);
    }
  }

  class Fleches extends Ecran {
    static TITRE = "3. Les flèches qui tournent";
    static NUMERO = 3;
    static G = [40, 95, 620, 588];
    static ORIG = [243, 341];   // le centre (le "0") dans le panneau
    static ECH = 76;            // le plus grand qui ne sort jamais du cadre (testé de 0 à 50)
    static N = 80;
    static TMAX = 50;
    static COULEURS = [ORANGE, JAUNE, VERT];

    constructor(jeu) {
      super(jeu);
      this.t = 10;
      this.joue = false;
      this.trouves = [];
      this.fige = 0;
      this.amp = Array.from({ length: Fleches.N }, (_, i) => ((i + 1) % 2 === 1 ? 1 : -1) / Math.sqrt(i + 1));
      this.lns = Array.from({ length: Fleches.N }, (_, i) => Math.log(i + 1));
      this.calculer();
      this.dire([TACTILE ? "Le bouton Lancer fait avancer le temps : tout tourne." : "ESPACE lance le temps : chaque flèche tourne à sa vitesse.",
        TACTILE ? "Touche Arrêter quand le point jaune touche la croix." : "Rappuie sur ESPACE quand le point jaune touche la croix."]);
    }
    calculer() {
      const [ox, oy] = Fleches.ORIG;
      let sr = 0, si = 0;
      this.chaine = [[ox, oy]];
      for (let i = 0; i < Fleches.N; i++) {
        sr += this.amp[i] * Math.cos(-this.t * this.lns[i]);
        si += this.amp[i] * Math.sin(-this.t * this.lns[i]);
        this.chaine.push([ox + sr * Fleches.ECH, oy - si * Fleches.ECH]);
      }
      this.eta = eta(0.5, this.t);
    }
    touche(k) {
      if (k === "space" && this.fige <= 0) {
        if (this.joue) { this.joue = false; this.verifier(true); } else this.joue = true;
      }
    }
    relache(k) { if ((k === "Left" || k === "Right") && !this.joue && this.fige <= 0) this.verifier(false); }
    verifier(manuel) {
      const proche = ZEROS.reduce((a, g) => (Math.abs(g - this.t) < Math.abs(a - this.t) ? g : a));
      if (module(this.eta) < 0.25 && Math.abs(proche - this.t) < 0.6) {
        this.t = proche; this.joue = false; this.fige = 1.4;
        this.calculer();
        if (this.trouves.includes(proche)) {
          this.dire(["Celui-là, tu l'as déjà !", `Relance le temps (${K_ESPACE}) pour trouver le suivant.`], ORANGE);
          return;
        }
        this.trouves.push(proche);
        const n = this.trouves.length;
        if (n >= 3) {
          this.fini = true;
          this.dire(["Bravo ! Toutes les flèches s'annulent pile au centre.", "C'est exactement ça, un zéro de zeta."], VERT);
        } else {
          this.dire([`Zéro n°${n} : temps = ${fr(proche)}, tout s'annule !`, `Relance le temps (${K_ESPACE}) pour trouver le suivant.`], VERT);
        }
      } else if (manuel) {
        this.dire(["Pas encore : le point jaune n'est pas sur la croix.", `Relance (${K_ESPACE}) ou ajuste doucement avec ◀ et ▶.`], ORANGE);
      }
    }
    maj(dt) {
      if (this.fige > 0) { this.fige -= dt; return; }
      const k = this.jeu.touches;
      const v = (this.joue ? 0.8 : 0) + 0.5 * (k.has("Right") - k.has("Left"));
      if (v) {
        this.t = Math.min(Math.max(this.t + v * dt, 0), Fleches.TMAX);
        if (this.t >= Fleches.TMAX && this.joue) {
          this.joue = false;
          this.dire(["Fin de la piste !", "Reviens en arrière avec ◀."], ORANGE);
        }
        this.calculer();
      }
    }
    dessiner() {
      const [x0, y0, x1, y1] = Fleches.G, [ox, oy] = Fleches.ORIG;
      D.rect(x0, y0, x1, y1, { fill: PANNEAU, stroke: BORD, width: 2 });
      const c = module(this.eta) < 0.25 ? VERT : "#cfd6ff";
      if (this.fige > 0) D.rond(ox, oy, 16 + (1.4 - this.fige) * 60, { stroke: VERT, width: 3 });
      D.ligne([ox - 16, oy, ox + 16, oy], c, 3);
      D.ligne([ox, oy - 16, ox, oy + 16], c, 3);
      D.texte(ox - 22, oy + 22, "0", 15, true, c);
      const p = this.chaine;
      for (let i = Fleches.N; i >= 1; i--) {
        const [xa, ya] = p[i - 1], [xb, yb] = p[i];
        if (i <= 3) D.fleche(xa, ya, xb, yb, Fleches.COULEURS[i - 1], 5);
        else {
          const f = (i - 4) / (Fleches.N - 4);
          D.ligne([xa, ya, xb, yb], `rgb(${Math.round(79 + 100 * f)},${Math.round(195 - 110 * f)},247)`, i < 15 ? 2.5 : 1.5);
        }
      }
      const places = [];   // chaque numéro va du côté le plus loin des numéros déjà posés
      for (let i = 1; i <= 3; i++) {
        const [xa, ya] = p[i - 1], [xb, yb] = p[i];
        const dx = xb - xa, dy = yb - ya, n = Math.hypot(dx, dy) || 1, mx = (xa + xb) / 2, my = (ya + yb) / 2;
        const cotes = [[mx - dy / n * 20, my + dx / n * 20], [mx + dy / n * 20, my - dx / n * 20]];
        const loin = (q) => (places.length ? Math.min(...places.map(([px, py]) => Math.hypot(q[0] - px, q[1] - py))) : 1e9);
        const best = loin(cotes[1]) > loin(cotes[0]) ? cotes[1] : cotes[0];
        places.push(best);
        D.texte(best[0], best[1], String(i), 18, true, Fleches.COULEURS[i - 1]);
      }
      D.rond(ox + this.eta[0] * Fleches.ECH, oy - this.eta[1] * Fleches.ECH, 10, { fill: JAUNE, stroke: "white", width: 2 });

      D.texte(910, 112, `temps = ${fr(this.t)}`, 28, true);
      const tx0 = 720, tx1 = 1140, ty = 168, px = (g) => tx0 + g / Fleches.TMAX * (tx1 - tx0);
      D.ligne([tx0, ty, tx1, ty], GRIS, 3);
      for (let g = 0; g <= 50; g += 10) {
        D.ligne([px(g), ty - 6, px(g), ty + 6], GRIS, 2);
        D.texte(px(g), ty + 20, String(g), 13, false, GRIS);
      }
      for (const g of this.trouves) D.etoile(px(g), ty, 10);
      D.poly([px(this.t), ty - 10, px(this.t) - 9, ty - 26, px(this.t) + 9, ty - 26], JAUNE);
      [[ORANGE, "la 1 : ne tourne pas"], [JAUNE, "la 2 : tourne doucement"], [VERT, "la 3 : un peu plus vite"],
        [BLEU, "les autres : encore plus vite"]].forEach(([coul, txt], i) => {
        const y = 230 + i * 40;
        D.fleche(712, y, 762, y, coul, i < 3 ? 5 : 2, [12, 15, 5]);
        D.texte(778, y, txt, 17, false, TEXTE, "w");
      });
      D.rond(737, 390, 10, { fill: JAUNE, stroke: "white", width: 2 });
      D.texte(778, 390, "le total de TOUTES les flèches", 17, false, TEXTE, "w");
      D.texte(910, 440, compteur(this.trouves.length), 20, true);
      this.jeu.bouton(712, 470, 792, 520, "◀", null, "#5c6699", 22, "Left");
      this.jeu.bouton(806, 470, 1014, 520, this.joue ? "Arrêter" : "Lancer", () => this.jeu.taper("space"),
        this.joue ? ORANGE : VERT, 21);
      this.jeu.bouton(1028, 470, 1108, 520, "▶", null, "#5c6699", 22, "Right");
      D.texte(910, 552, "Petit secret : ici zeta a des + et des -.", 14, false, GRIS);
      D.texte(910, 574, "Sur la ligne 1/2, elle a les mêmes zéros.", 14, false, GRIS);
      this.cadre();
    }
  }

  class Pi extends Ecran {
    static TITRE = "4. π sort de nulle part";
    static NUMERO = 4;
    static PI2_6 = Math.PI ** 2 / 6;

    constructor(jeu) {
      super(jeu);
      this.n = 0; this.total = 0; this.objectif = 1; this.tenu = 0; this.reserve = 0;
      this.dire([TACTILE ? "Le bouton jaune ajoute un carré : 1, puis 1/4, puis 1/9..." : "ESPACE = ajouter un carré : 1, puis 1/4, puis 1/9...",
        TACTILE ? "Objectif : π ≈ 3,1. Garde le doigt dessus pour aller vite !" : "Objectif : π ≈ 3,1. Garde ESPACE appuyé pour aller vite !"]);
    }
    touche(k) { if (k === "space") this.ajouter(1); }
    ajouter(m) {
      for (let i = 0; i < m; i++) { this.n++; this.total += 1 / (this.n * this.n); }
      const estim = Math.sqrt(6 * this.total);
      if (this.objectif === 1 && estim >= 3.1) {
        this.objectif = 2;
        this.dire([`Bravo : π ≈ 3,1 avec seulement ${this.n} carrés !`,
          TACTILE ? "Objectif 2 : π ≈ 3,14. Garde le doigt appuyé !" : "Objectif 2 : π ≈ 3,14. Garde ESPACE appuyé !"], VERT);
      } else if (this.objectif === 2 && estim >= 3.14) {
        this.objectif = 3; this.fini = true;
        this.dire(["π sort tout seul, alors qu'il n'y a aucun cercle !", "C'est zeta de 2 : Euler l'a trouvé en 1734."], VERT);
      }
    }
    maj(dt) {
      if (this.jeu.touches.has("space")) {
        this.tenu = Math.min(this.tenu + dt, 10);   // sans limite, 2,2 ** ... finirait par déborder
        if (this.tenu > 0.35) {
          this.reserve += Math.min(3000, 4 * 2.2 ** ((this.tenu - 0.35) * 3)) * dt;
          const m = Math.floor(this.reserve);
          this.reserve -= m;
          if (m) this.ajouter(m);
        }
      } else { this.tenu = 0; this.reserve = 0; }
    }
    dessiner() {
      D.rect(40, 95, 700, 588, { fill: PANNEAU, stroke: BORD, width: 2 });
      D.texte(370, 150, "1 + 1/4 + 1/9 + 1/16 + ...", 30, true);
      D.texte(370, 200, "= la surface de tous les carrés ensemble", 18, false, GRIS);
      let x = 62;
      const bas = 540;
      for (let i = 1; i <= Math.min(this.n, 10); i++) {
        const c = 190 / i;
        D.rect(x, bas - c, x + c, bas, { fill: i === this.n ? JAUNE : "#3d7fbf", stroke: "white", width: 1 });
        if (i <= 4) D.texte(x + c / 2, bas + 18, i === 1 ? "1" : `1/${i * i}`, 15, true);
        x += c + 6;
      }
      if (this.n > 10) {
        D.texte(680, 300, `+ ${this.n - 10} carrés`, 18, true, TEXTE, "e");
        D.texte(680, 328, "tout petits", 18, false, GRIS, "e");
      }
      if (this.n === 0) D.texte(370, 380, TACTILE ? "Touche le bouton jaune !" : "Appuie sur ESPACE !", 26, true, JAUNE);

      const bx0 = 760, bx1 = 830, by0 = 120, by1 = 560, haut = (v) => by1 - v / 1.8 * (by1 - by0);
      D.rect(bx0, by0, bx1, by1, { fill: "#232a5a", stroke: BORD, width: 2 });
      if (this.total > 0) D.rect(bx0, haut(this.total), bx1, by1, { fill: BLEU });
      D.ligne([bx0 - 10, haut(Pi.PI2_6), bx1 + 10, haut(Pi.PI2_6)], ROUGE, 3);
      D.texte(bx0 - 14, haut(Pi.PI2_6), "π²/6", 16, true, ROUGE, "e");
      const estim = Math.sqrt(6 * this.total);
      D.texte(870, 150, `Carrés : ${this.n}`, 21, true, TEXTE, "w");
      D.texte(870, 192, `Total : ${fr(this.total, 4)}`, 21, false, TEXTE, "w");
      D.texte(870, 262, "π ≈ √(6 × total)", 18, false, GRIS, "w");
      D.texte(870, 312, `= ${fr(estim, 4)}`, 36, true, JAUNE, "w");
      D.texte(870, 370, "Le vrai π :", 17, false, GRIS, "w");
      D.texte(870, 398, "3,14159...", 21, true, TEXTE, "w");
      const obj = { 1: "Objectif : 3,1", 2: "Objectif : 3,14", 3: "Objectifs réussis !" }[this.objectif];
      D.texte(870, 450, obj, 19, true, this.objectif === 3 ? VERT : ORANGE, "w");
      this.jeu.bouton(870, 490, 1150, 560, "+ un carré", null, JAUNE, 22, "space");
      this.cadre();
    }
  }

  class Fin extends Ecran {
    touche(k) { if (k === "Return") this.jeu.aller(0); }
    dessiner() {
      D.texte(VW / 2, 90, "Bravo, tu as tout vu !", 38, true, JAUNE);
      [[BLEU, "1. Les zéros qu'on a trouvés sont tous sur la ligne 1/2."],
        [VIOLET, "2. Le miroir : un zéro hors de la ligne aurait un jumeau."],
        [VERT, "3. Un zéro = toutes les flèches qui tournent s'annulent."],
        [JAUNE, "4. π se cache dans zeta : 1 + 1/4 + 1/9 + ... = π²/6."]]
        .forEach(([c, t], i) => D.texte(140, 180 + i * 56, t, 21, false, c, "w"));
      D.rect(140, 420, 1060, 560, { fill: "#1b2150", stroke: BORD, width: 2 });
      D.texte(VW / 2, 462, "Prouvé en 2026 : au moins 67 % des zéros sont sur la ligne.", 20, true, VERT);
      D.texte(VW / 2, 516, "Les 33 % restants : personne ne sait. Le million attend toujours !", 18);
      this.jeu.bouton(300, 600, 580, 670, "Rejouer", () => this.jeu.aller(0), BLEU);
      this.jeu.bouton(620, 600, 900, 670, "Soutenir (Patreon)", () => {
        const w = window.open(PATREON, "_blank");
        if (w) w.opener = null; else window.location.href = PATREON;   // fenêtre bloquée : on y va dans cet onglet
      }, ROSE);
    }
  }

  // ------------------------------------------------------------ le jeu
  const ECRANS = [Menu, Machine, Miroir, Fleches, Pi, Fin];
  const jeu = {
    touches: new Set(), boutons: [], souris: [-1, -1], ecran: null, index: 0, carte: null,
    aller(i) { this.index = i; this.ecran = new ECRANS[i](this); this.boutons = []; },
    suivant() { this.aller(Math.min(this.index + 1, ECRANS.length - 1)); },
    bouton(x0, y0, x1, y1, txt, action, coul = BLEU, taille = 21, maintien = null) {
      const [mx, my] = this.souris;
      const dessus = mx >= x0 && mx <= x1 && my >= y0 && my <= y1;
      D.rect(x0, y0, x1, y1, { fill: dessus || (maintien && this.touches.has(maintien)) ? eclaircir(coul) : coul });
      D.texte((x0 + x1) / 2, (y0 + y1) / 2, txt, taille, true, "#0b0e1f");
      this.boutons.push({ x0, y0, x1, y1, action, maintien });
    },
    appuyer(k) {
      if (this.touches.has(k)) return;
      this.touches.add(k);
      if (k === "Escape") this.aller(0);
      else if (k === "Return" && this.ecran.fini) this.suivant();
      else this.ecran.touche(k);
    },
    relacher(k) { this.touches.delete(k); this.ecran.relache(k); },
    taper(k) { this.appuyer(k); this.relacher(k); },
  };

  // souris / doigt
  // pointerId -> "Left"/"space"... (touche maintenue), { bouton } (clic au doigt, lancé au lever) ou null (glisser)
  const pointeurs = new Map();
  function capturer(id) {        // garder le doigt même s'il sort du jeu ; ne doit jamais bloquer un bouton
    try { cv.setPointerCapture(id); } catch (_) { /* pointeur déjà relâché */ }
  }
  function versVirtuel(e) {
    const r = cv.getBoundingClientRect();
    return [(e.clientX - r.left) * VW / r.width, (e.clientY - r.top) * VH / r.height];
  }
  const dedans = (b, x, y) => x >= b.x0 && x <= b.x1 && y >= b.y0 && y <= b.y1;
  function relacherSiLibre(k) {  // ne relâche pas une touche qu'un autre doigt tient encore
    if (![...pointeurs.values()].includes(k)) jeu.relacher(k);
  }
  cv.addEventListener("pointerdown", (e) => {
    if (e.pointerType === "mouse" && e.button !== 0) return;          // seulement le clic gauche
    e.preventDefault();
    if (document.activeElement && document.activeElement !== document.body) document.activeElement.blur();
    const ancien = pointeurs.get(e.pointerId);                        // un ancien appui jamais relâché
    if (typeof ancien === "string") { pointeurs.delete(e.pointerId); relacherSiLibre(ancien); }
    const [x, y] = versVirtuel(e);
    jeu.souris = [x, y];
    for (let i = jeu.boutons.length - 1; i >= 0; i--) {
      const b = jeu.boutons[i];
      if (!dedans(b, x, y)) continue;
      if (b.maintien) { pointeurs.set(e.pointerId, b.maintien); jeu.appuyer(b.maintien); capturer(e.pointerId); }
      else if (e.pointerType === "mouse") b.action();
      else pointeurs.set(e.pointerId, { bouton: b });   // au doigt : l'action part au lever (sinon le lien Patreon est bloqué)
      return;
    }
    pointeurs.set(e.pointerId, null);
    jeu.ecran.appui(x, y);
    capturer(e.pointerId);
  });
  cv.addEventListener("pointermove", (e) => {
    const p = versVirtuel(e);
    if (e.pointerType !== "touch") jeu.souris = p;
    if (pointeurs.get(e.pointerId) === null) jeu.ecran.glisse(...p);
  });
  function finPointeur(e) {
    if (!pointeurs.has(e.pointerId)) return;
    const v = pointeurs.get(e.pointerId);
    pointeurs.delete(e.pointerId);
    const [x, y] = versVirtuel(e);
    if (typeof v === "string") relacherSiLibre(v);
    else if (v && v.bouton) { if (e.type === "pointerup" && dedans(v.bouton, x, y)) v.bouton.action(); }
    else jeu.ecran.lache(x, y);
    if (e.pointerType === "touch") jeu.souris = [-1, -1];
  }
  cv.addEventListener("pointerup", finPointeur);
  cv.addEventListener("pointercancel", finPointeur);
  cv.addEventListener("contextmenu", (e) => e.preventDefault());   // pas de menu du navigateur sur le jeu

  // clavier (les chiffres par e.code : marche aussi en AZERTY sans Maj)
  const CLES = { ArrowLeft: "Left", ArrowRight: "Right", ArrowUp: "Up", ArrowDown: "Down", " ": "space", Enter: "Return", Escape: "Escape" };
  const cle = (e) => (/^(Digit|Numpad)[1-4]$/.test(e.code) ? e.code.slice(-1) : CLES[e.key] || null);
  const surUnLien = (e) => e.target instanceof Element && e.target.closest("a, button, input, select, textarea");
  window.addEventListener("keydown", (e) => {
    const k = cle(e);
    if (!k || e.ctrlKey || e.altKey || e.metaKey || surUnLien(e)) return;   // Entrée sur un lien du bas : on laisse le lien s'ouvrir
    e.preventDefault();
    if (!e.repeat) jeu.appuyer(k);
  });
  window.addEventListener("keyup", (e) => { const k = cle(e); if (k) jeu.relacher(k); });
  window.addEventListener("blur", () => { for (const k of [...jeu.touches]) jeu.relacher(k); });

  // taille : le jeu remplit l'écran sans se déformer, net sur les écrans haute densité
  function redimensionner() {
    const pied = document.getElementById("pied").offsetHeight;
    const k = Math.max(0.2, Math.min(window.innerWidth / VW, (window.innerHeight - pied - 4) / VH));
    const dpr = window.devicePixelRatio || 1;
    cv.style.width = `${Math.floor(VW * k)}px`;
    cv.style.height = `${Math.floor(VH * k)}px`;
    cv.width = Math.round(VW * k * dpr);
    cv.height = Math.round(VH * k * dpr);
    echelle = cv.width / VW;
  }
  window.addEventListener("resize", redimensionner);

  function image(dt) {           // une image du jeu : logique puis dessin
    jeu.ecran.maj(dt);
    ctx.setTransform(echelle, 0, 0, echelle, 0, 0);
    ctx.fillStyle = FOND;
    ctx.fillRect(0, 0, VW, VH);
    jeu.boutons = [];
    jeu.ecran.dessiner();
  }

  let dernier = performance.now();
  function boucle(t) {
    try {
      const dt = Math.min(0.1, Math.max(0, (t - dernier) / 1000));
      dernier = t;
      image(dt);
    } finally {
      requestAnimationFrame(boucle);   // une image ratée ne doit jamais figer le jeu
    }
  }

  redimensionner();
  jeu.aller(0);
  jeu.image = image;
  window.RZJeu = jeu;   // pour les tests automatiques (RZJeu.image(dt) fait avancer d'une image)
  requestAnimationFrame(boucle);
})();
