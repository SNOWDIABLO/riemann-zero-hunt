# -*- coding: utf-8 -*-
"""
La chasse aux zéros de Riemann
==============================
Un petit jeu en 4 niveaux pour VOIR la fonction zeta et ses zéros :
  1. La machine zeta : bouge un point, trouve les zéros.
  2. Le miroir : pourquoi la ligne est à 1/2.
  3. Les flèches qui tournent : un zéro = toutes les flèches s'annulent.
  4. π sort de nulle part : 1 + 1/4 + 1/9 + ... = π²/6.

Lancer : double-clic sur "Lancer le jeu.bat"  (ou : python riemann_jeu.py)
Besoin : Python 3 + numpy. Rien d'autre à installer (tkinter est fourni avec Python).
"""

import math
import threading
import time
import tkinter as tk
from fractions import Fraction

import numpy as np

# ==================================================================
# 1. LES MATHS : calcul de zeta
# ==================================================================
# On calcule eta (zeta avec des + et des -) par l'algorithme de Borwein,
# puis zeta = eta / (1 - 2^(1-s)). A gauche de la ligne 1/2, on passe
# par le miroir de Riemann (équation fonctionnelle) pour rester précis.

N_TERMES = 120
LOG2 = math.log(2.0)
LOGPI = math.log(math.pi)


def _poids_borwein(n):
    d, acc = [], Fraction(0)
    for i in range(n + 1):
        acc += Fraction(math.factorial(n + i - 1) * 4 ** i,
                        math.factorial(n - i) * math.factorial(2 * i))
        d.append(n * acc)
    return np.array([(-1) ** k * float(1 - d[k] / d[n]) for k in range(n)])


_POIDS = _poids_borwein(N_TERMES)
_LOGK = np.log(np.arange(1, N_TERMES + 1, dtype=float))


def eta(s):
    """eta(s) = 1 - 1/2^s + 1/3^s - 1/4^s + ...  (tableau numpy de complexes)."""
    s = np.asarray(s, dtype=complex)
    plat = s.ravel()
    out = np.empty(plat.shape, dtype=complex)
    for a in range(0, plat.size, 4096):
        out[a:a + 4096] = np.exp(-np.multiply.outer(plat[a:a + 4096], _LOGK)) @ _POIDS
    return out.reshape(s.shape)


_LANCZOS = (0.99999999999980993, 676.5203681218851, -1259.1392167224028,
            771.32342877765313, -176.61502916214059, 12.507343278686905,
            -0.13857109526572012, 9.9843695780195716e-6, 1.5056327351493116e-7)


def _gamma(z):
    """Fonction Gamma complexe (Lanczos), pour Re(z) >= 0,5."""
    z = z - 1
    x = _LANCZOS[0] + sum(c / (z + i) for i, c in enumerate(_LANCZOS[1:], 1))
    t = z + 7.5
    return math.sqrt(2 * math.pi) * np.exp((z + 0.5) * np.log(t) - t) * x


def _zeta_droite(s):
    """zeta pour Re(s) >= 0,5."""
    den = 1 - np.exp((1 - s) * LOG2)
    den = np.where(np.abs(den) < 1e-12, 1e-12, den)
    return eta(s) / den


def zeta(s):
    """zeta(s) pour un tableau numpy de complexes."""
    s = np.asarray(s, dtype=complex)
    out = np.empty(s.shape, dtype=complex)
    d = s.real >= 0.5
    out[d] = _zeta_droite(s[d])
    g = ~d
    if g.any():
        sg = s[g]
        u = 1 - sg
        out[g] = (np.exp(sg * LOG2 + (sg - 1) * LOGPI) * np.sin(np.pi * sg / 2)
                  * _gamma(u) * _zeta_droite(u))
    return out


def zeta1(s):
    return complex(zeta(np.array([s]))[0])


def eta1(s):
    return complex(eta(np.array([s]))[0])


def newton_zero(s, iters=40):
    """Cherche le zéro de zeta le plus proche de s. Renvoie le zéro, ou None."""
    h = 1e-6
    for _ in range(iters):
        f = zeta1(s)
        if abs(f) < 1e-10:
            return s
        df = (zeta1(s + h) - zeta1(s - h)) / (2 * h)
        if df == 0:
            return None
        pas = f / df
        if abs(pas) > 1.0:
            pas = pas / abs(pas)
        s = s - pas
    return s if abs(zeta1(s)) < 1e-8 else None


# Hauteurs des 10 premiers zéros (ils sont tous à 1/2 + hauteur × i).
ZEROS = [14.134725141734693, 21.022039638771555, 25.010857580145688,
         30.424876125859513, 32.935061587739189, 37.586178158825671,
         40.918719012147495, 43.327073280914999, 48.005150881167159,
         49.773832477672302]


_DEGRADE = np.array([[0, 0, 4], [40, 11, 84], [101, 21, 110], [159, 42, 99],
                     [212, 72, 66], [245, 125, 21], [250, 193, 39], [252, 240, 150]], dtype=float)


def carte_couleurs(Z):
    """Image de |zeta| : noir = la machine sort 0 (un zéro), jaune clair = loin de 0."""
    mag = np.abs(np.nan_to_num(Z, nan=0.0, posinf=1e6, neginf=-1e6))
    f = np.clip(np.tanh(mag / 1.6), 0, 1) * (len(_DEGRADE) - 1)
    i = np.minimum(f.astype(int), len(_DEGRADE) - 2)
    a = (f - i)[..., None]
    rgb = _DEGRADE[i] * (1 - a) + _DEGRADE[i + 1] * a
    return (rgb * 0.85).astype(np.uint8)          # un peu assombri : les étoiles ressortent


def photo_depuis_rgb(rgb):
    h, w, _ = rgb.shape
    return tk.PhotoImage(data=b"P6 %d %d 255\n" % (w, h) + rgb.tobytes(), format="PPM")


# ==================================================================
# 2. L'AFFICHAGE
# ==================================================================
VW, VH = 1200, 760          # taille "virtuelle" ; tout est agrandi à l'écran
FOND = "#0d1024"
PANNEAU = "#161b3a"
BORD = "#2c3566"
TEXTE = "#eef1ff"
GRIS = "#8f97c4"
JAUNE = "#ffd54f"
BLEU = "#4fc3f7"
VIOLET = "#b388ff"
ROSE = "#ff5c8a"
ROUGE = "#ff6e6e"
VERT = "#69f0ae"
ORANGE = "#ffab40"
POLICE = "Segoe UI"         # lisible, et son π ne ressemble pas à un п


def fr(x, n=2):
    """Nombre à la française : 14,13 au lieu de 14.13."""
    return f"{x:.{n}f}".replace(".", ",")


def compteur(n):
    """« Zéros trouvés : 2 / 3 », puis les zéros en plus comptent en bonus."""
    return f"Zéros trouvés : {n} / 3" if n <= 3 else f"Zéros trouvés : 3 / 3  (+{n - 3} bonus)"


def eclaircir(couleur, a=0.3):
    r, g, b = (int(couleur[i:i + 2], 16) for i in (1, 3, 5))
    return "#%02x%02x%02x" % tuple(round(c + (255 - c) * a) for c in (r, g, b))


class Stylo:
    """Dessine en coordonnées virtuelles (1200 × 760), agrandies par k."""

    def __init__(self, cv, k):
        self.cv, self.k = cv, k

    def _w(self, kw):
        if "width" in kw:
            kw["width"] = max(1, kw["width"] * self.k)
        if "arrowshape" in kw:
            kw["arrowshape"] = tuple(v * self.k for v in kw["arrowshape"])
        return kw

    def ligne(self, pts, **kw):
        self.cv.create_line(*[v * self.k for v in pts], **self._w(kw))

    def rond(self, x, y, r, **kw):
        k = self.k
        self.cv.create_oval((x - r) * k, (y - r) * k, (x + r) * k, (y + r) * k, **self._w(kw))

    def rect(self, x0, y0, x1, y1, **kw):
        k = self.k
        self.cv.create_rectangle(x0 * k, y0 * k, x1 * k, y1 * k, **self._w(kw))

    def poly(self, pts, **kw):
        self.cv.create_polygon(*[v * self.k for v in pts], **self._w(kw))

    def texte(self, x, y, txt, taille=18, gras=False, couleur=TEXTE, anchor="center", largeur=None):
        kw = dict(text=txt, fill=couleur, anchor=anchor, justify="left" if anchor == "w" else "center",
                  font=(POLICE, -max(8, round(taille * self.k)), "bold" if gras else "normal"))
        if largeur:
            kw["width"] = largeur * self.k
        self.cv.create_text(x * self.k, y * self.k, **kw)

    def image(self, x, y, img):
        self.cv.create_image(x * self.k, y * self.k, image=img, anchor="nw")

    def etoile(self, x, y, r, couleur=ROSE):
        pts = []
        for i in range(10):
            a = -math.pi / 2 + i * math.pi / 5
            rr = r if i % 2 == 0 else r * 0.45
            pts += [x + rr * math.cos(a), y + rr * math.sin(a)]
        self.poly(pts, fill=couleur, outline="white", width=1)


# ==================================================================
# 3. LES ÉCRANS
# ==================================================================
class Ecran:
    TITRE = ""
    NUMERO = 0

    def __init__(self, jeu):
        self.jeu = jeu
        self.msg = []
        self.msg_couleur = TEXTE
        self.fini = False

    def maj(self, dt): pass
    def dessiner(self, p): pass
    def touche(self, k): pass
    def relache(self, k): pass
    def appui(self, x, y): pass
    def glisse(self, x, y): pass
    def lache(self, x, y): pass

    def dire(self, *lignes, couleur=TEXTE):
        self.msg, self.msg_couleur = list(lignes), couleur

    def cadre(self, p):
        """Barre du haut + boîte de message en bas (+ bouton Suivant quand c'est gagné)."""
        p.rect(0, 0, VW, 62, fill="#11163a", outline="")
        p.texte(40, 32, self.TITRE, 26, True, JAUNE, anchor="w")
        p.texte(VW - 40, 32, f"Niveau {self.NUMERO} / 4      Échap = menu", 15, couleur=GRIS, anchor="e")
        p.rect(40, 622, VW - 40, 742, fill="#1b2150", outline=BORD, width=2)
        y0 = 682 - (len(self.msg) - 1) * 21
        for i, ligne in enumerate(self.msg):
            p.texte(70, y0 + i * 42, ligne, 21, i == 0, self.msg_couleur if i == 0 else TEXTE, anchor="w")
        if self.fini:
            self.jeu.bouton(950, 652, 1140, 712, "Suivant  ▶", self.jeu.suivant, VERT)


class Menu(Ecran):
    TOUCHES = {"1": 1, "2": 2, "3": 3, "4": 4, "KP_1": 1, "KP_2": 2, "KP_3": 3, "KP_4": 4,
               "ampersand": 1, "eacute": 2, "quotedbl": 3, "apostrophe": 4}   # clavier AZERTY

    def touche(self, k):
        if k in self.TOUCHES:
            self.jeu.aller(self.TOUCHES[k])
        elif k == "Return":
            self.jeu.aller(1)

    def dessiner(self, p):
        # petite déco : la ligne 1/2 et ses zéros
        p.ligne((1080, 90, 1080, 700), fill=VIOLET, width=2, dash=(6, 5))
        for i, z in enumerate(ZEROS):
            p.etoile(1080, 680 - z * 11.5, 9 if i < 5 else 7)
        p.texte(560, 110, "La chasse aux zéros de Riemann", 40, True, JAUNE)
        p.texte(560, 168, "4 petits jeux pour VOIR les zéros de zeta.", 21, couleur=TEXTE)
        noms = ["1    La machine zeta", "2    Le miroir", "3    Les flèches qui tournent",
                "4    π sort de nulle part"]
        for i, nom in enumerate(noms):
            y = 240 + i * 92
            self.jeu.bouton(260, y, 860, y + 68, nom, lambda n=i + 1: self.jeu.aller(n),
                            [BLEU, VIOLET, VERT, JAUNE][i], 24)
        p.texte(560, 650, "Clique sur un jeu (ou appuie sur Entrée pour commencer).", 18, couleur=GRIS)
        p.texte(560, 690, "Échap = revenir ici à tout moment.", 18, couleur=GRIS)


class Machine(Ecran):
    TITRE = "1. La machine zeta"
    NUMERO = 1
    G = (40, 95, 520, 588)       # plan de gauche : ce qu'on donne
    D = (600, 95, 1160, 588)     # plan de droite : ce qui sort
    # De 0 à 2 en largeur : à gauche de 0 il y a des zéros "faciles" (-2, -4...)
    # dont la conjecture ne parle pas ; on les laisse hors du jeu.
    SMIN, SMAX, TMIN, TMAX = 0.0, 2.0, 0.0, 35.0
    ECH = 85                     # pixels par unité, à droite
    CAPTURE = 0.35               # assez près de 0 : la machine "aimante" le zéro (testé : aucun faux zéro)
    BRULANT = 0.38               # au-dessus, le coin en bas à gauche (|zeta| ≈ 0,39) aurait l'air "brûlant" sans zéro

    def __init__(self, jeu):
        super().__init__(jeu)
        self.s = complex(1.5, 10.0)  # testé : suivre "plus chaud" depuis ici mène au 1er zéro
        self.val = zeta1(self.s)
        self.trace = []
        self.trouves = []
        self.fige = 0.0
        self.sortir = False      # après une capture, il faut s'éloigner avant la suivante
        self.chrono = 0.0
        self.astuce = False
        self.tient = False
        self.carte = None
        if jeu.rgb_carte is None:
            threading.Thread(target=self._calcul_carte, daemon=True).start()
        self.dire("Bouge le point bleu (souris ou flèches du clavier).",
                  "But : amener le point jaune, à droite, sur le centre.")

    def _calcul_carte(self):
        k = self.jeu.k
        x0, y0, x1, y1 = self.G
        w, h = max(2, round((x1 - x0) * k / 2)), max(2, round((y1 - y0) * k / 2))
        sig = self.SMIN + (np.arange(w) + 0.5) / w * (self.SMAX - self.SMIN)
        t = self.TMAX - (np.arange(h) + 0.5) / h * (self.TMAX - self.TMIN)
        with np.errstate(all="ignore"):
            self.jeu.rgb_carte = carte_couleurs(zeta(sig[None, :] + 1j * t[:, None]))

    # --- coordonnées
    def vers_px(self, s):
        x0, y0, x1, y1 = self.G
        return (x0 + (s.real - self.SMIN) / (self.SMAX - self.SMIN) * (x1 - x0),
                y1 - (s.imag - self.TMIN) / (self.TMAX - self.TMIN) * (y1 - y0))

    def depuis_px(self, x, y):
        x0, y0, x1, y1 = self.G
        return self.borner(complex(self.SMIN + (x - x0) / (x1 - x0) * (self.SMAX - self.SMIN),
                                   self.TMIN + (y1 - y) / (y1 - y0) * (self.TMAX - self.TMIN)))

    def borner(self, s):
        return complex(min(max(s.real, self.SMIN), self.SMAX), min(max(s.imag, 0.3), self.TMAX))

    def vers_droite(self, v):
        X0, Y0, X1, Y1 = self.D
        return (X0 + X1) / 2 + v.real * self.ECH, (Y0 + Y1) / 2 - v.imag * self.ECH

    # --- souris
    def appui(self, x, y):
        x0, y0, x1, y1 = self.G
        if x0 <= x <= x1 and y0 <= y <= y1 and self.fige <= 0:
            self.tient = True
            self.s = self.depuis_px(x, y)

    def glisse(self, x, y):
        if self.tient and self.fige <= 0:
            self.s = self.depuis_px(x, y)

    def lache(self, x, y):
        self.tient = False

    # --- logique
    def maj(self, dt):
        if len(self.trouves) < 3:
            self.chrono += dt
        if self.fige > 0:
            self.fige -= dt
            return
        k = self.jeu.touches
        ds = complex(0.5 * dt * (("Right" in k) - ("Left" in k)), 3.0 * dt * (("Up" in k) - ("Down" in k)))
        if ds:
            self.s = self.borner(self.s + ds)
        self.val = zeta1(self.s)
        self.trace.append(self.val)
        del self.trace[:-70]
        a = abs(self.val)
        if self.sortir:
            if a > 0.6:
                self.sortir = False
        elif a < self.CAPTURE:
            self.capturer()
        if self.chrono > 25 and not self.astuce and len(self.trouves) < 3:
            self.astuce = True
            self.dire("Astuce : pose le point sur la ligne pointillée 1/2,",
                      "puis monte doucement avec la flèche du haut.", couleur=ORANGE)

    def capturer(self):
        z = newton_zero(self.s)
        if z is None or abs(z - self.s) > 1.5 or not (self.TMIN < z.imag < self.TMAX):
            self.sortir = True       # pas de zéro ici : on ne recalcule pas à chaque image
            return
        self.s, self.val, self.fige, self.sortir, self.tient = z, 0j, 1.2, True, False
        if any(abs(z - f) < 1e-3 for f in self.trouves):
            self.dire("Celui-là, tu l'as déjà trouvé !", "Cherche plus haut ou plus bas sur la ligne.",
                      couleur=ORANGE)
            return
        self.trouves.append(z)
        self.chrono, self.astuce = 0.0, False
        n = len(self.trouves)
        if n < 3:
            self.dire(f"Zéro n°{n} trouvé : il est à {fr(z.real, 3)} + {fr(z.imag)} i",
                      f"{fr(z.real, 3)} = 1/2 : pile sur la ligne ! Encore {3 - n} à trouver.",
                      couleur=VERT)
        else:
            self.fini = True
            self.dire("Voici la carte : chaque trou noir est un zéro.",
                      "Tous sur la ligne 1/2 ! Riemann dit : à l'infini aussi.", couleur=VERT)

    # --- dessin
    def dessiner(self, p):
        if self.fini and self.carte is None and self.jeu.rgb_carte is not None:
            self.carte = photo_depuis_rgb(self.jeu.rgb_carte).zoom(2, 2)
        x0, y0, x1, y1 = self.G
        p.texte((x0 + x1) / 2, 79, "Ce que tu donnes à la machine", 16, couleur=GRIS)
        p.rect(x0, y0, x1, y1, fill=PANNEAU, outline=BORD, width=2)
        if self.carte is not None:
            p.image(x0, y0, self.carte)
        for hauteur in (10, 20, 30):
            _, y = self.vers_px(complex(0, hauteur))
            p.ligne((x0 - 8, y, x0, y), fill=GRIS)
            p.texte(x0 - 10, y, str(hauteur), 13, couleur=GRIS, anchor="e")
        for sg, lab in ((0.0, "0"), (1.0, "1"), (2.0, "2")):
            x, _ = self.vers_px(complex(sg, 0))
            p.ligne((x, y0, x, y1), fill="#3a4580")
            p.texte(x, y1 + 14, lab, 15, couleur=GRIS)
        xm, _ = self.vers_px(complex(0.5, 0))
        p.ligne((xm, y0, xm, y1), fill=VIOLET, width=2, dash=(6, 5))
        p.texte(xm, y1 + 14, "1/2", 15, True, VIOLET)
        for z in self.trouves:
            p.etoile(*self.vers_px(z), 11)
        x, y = self.vers_px(self.s)
        if self.fige > 0:
            p.rond(x, y, 14 + (1.2 - self.fige) * 40, outline=VERT, width=3)
        p.rond(x, y, 11, fill=BLEU, outline="white", width=2)

        p.texte(560, 330, "→", 40, True, GRIS)
        p.texte(560, 372, "zeta", 15, couleur=GRIS)

        X0, Y0, X1, Y1 = self.D
        cx, cy = (X0 + X1) / 2, (Y0 + Y1) / 2
        p.texte(cx, 79, "Ce que la machine sort", 16, couleur=GRIS)
        p.rect(X0, Y0, X1, Y1, fill=PANNEAU, outline=BORD, width=2)
        p.ligne((X0, cy, X1, cy), fill="#3a4580")
        p.ligne((cx, Y0, cx, Y1), fill="#3a4580")
        a = abs(self.val)
        p.rond(cx, cy, self.CAPTURE * self.ECH, outline=VERT if a < self.BRULANT else "#3f6f5a", width=2,
               dash=(4, 4))
        p.texte(cx + 36, cy + 20, "0", 15, True, VERT, anchor="w")
        for v in self.trace[:-1]:
            tx, ty = self.vers_droite(v)
            if X0 < tx < X1 and Y0 < ty < Y1:
                p.rond(tx, ty, 2.5, fill="#8a7330", outline="")
        ox, oy = self.vers_droite(self.val)
        dehors = not (X0 + 12 < ox < X1 - 12 and Y0 + 12 < oy < Y1 - 12)
        ox, oy = min(max(ox, X0 + 12), X1 - 12), min(max(oy, Y0 + 12), Y1 - 12)
        p.rond(ox, oy, 11, fill=JAUNE, outline=ROUGE if dehors else "white", width=2)

        if a < self.BRULANT:
            mot, c = "Brûlant !", ROUGE
        elif a < 1.0:
            mot, c = "Chaud", ORANGE
        elif a < 2.0:
            mot, c = "Tiède", JAUNE
        else:
            mot, c = "Froid", BLEU
        p.rect(X0 + 14, Y0 + 14, X0 + 214, Y0 + 58, fill=c, outline="")
        p.texte(X0 + 114, Y0 + 36, mot, 20, True, "#0b0e1f")
        p.texte(X1 - 16, Y0 + 36, compteur(len(self.trouves)), 17, True, TEXTE, anchor="e")
        p.texte(X1 - 16, Y1 - 22, f"Distance au centre : {fr(min(a, 999))}", 15, couleur=GRIS, anchor="e")
        self.cadre(p)


class Miroir(Ecran):
    TITRE = "2. Le miroir"
    NUMERO = 2
    G = (40, 95, 640, 588)
    SMIN, SMAX, TMIN, TMAX = -0.5, 1.5, 0.0, 35.0

    def __init__(self, jeu):
        super().__init__(jeu)
        self.s = complex(0.18, 20.0)
        self.anim = 0.0
        self.tient = False
        self.dire("Ce point violet est un zéro imaginaire (pour l'exemple).",
                  "Pose-le SUR le miroir pour qu'il n'ait plus de jumeau.")

    def vers_px(self, s):
        x0, y0, x1, y1 = self.G
        return (x0 + (s.real - self.SMIN) / (self.SMAX - self.SMIN) * (x1 - x0),
                y1 - (s.imag - self.TMIN) / (self.TMAX - self.TMIN) * (y1 - y0))

    def depuis_px(self, x, y):
        x0, y0, x1, y1 = self.G
        return complex(self.SMIN + (x - x0) / (x1 - x0) * (self.SMAX - self.SMIN),
                       self.TMIN + (y1 - y) / (y1 - y0) * (self.TMAX - self.TMIN))

    def placer(self, s):
        s = complex(min(max(s.real, self.SMIN + 0.02), self.SMAX - 0.02),
                    min(max(s.imag, 1.0), self.TMAX - 1.0))
        if not self.fini and ((self.s.real - 0.5) * (s.real - 0.5) <= 0 or abs(s.real - 0.5) < 0.015):
            s = complex(0.5, s.imag)
            self.fini, self.anim, self.tient = True, 1.2, False
            self.dire("Bravo : sur le miroir, le zéro est son propre reflet.",
                      "Les vrais zéros (étoiles) sont tous collés au miroir.", couleur=VERT)
        self.s = s

    def appui(self, x, y):
        x0, y0, x1, y1 = self.G
        if x0 <= x <= x1 and y0 <= y <= y1:
            self.tient = True
            self.placer(self.depuis_px(x, y))

    def glisse(self, x, y):
        if self.tient:
            self.placer(self.depuis_px(x, y))

    def lache(self, x, y):
        self.tient = False

    def maj(self, dt):
        self.anim = max(0.0, self.anim - dt)
        k = self.jeu.touches
        ds = complex(0.35 * dt * (("Right" in k) - ("Left" in k)), 4.0 * dt * (("Up" in k) - ("Down" in k)))
        if ds:
            self.placer(self.s + ds)

    def dessiner(self, p):
        x0, y0, x1, y1 = self.G
        p.rect(x0, y0, x1, y1, fill=PANNEAU, outline=BORD, width=2)
        a, _ = self.vers_px(complex(0, 0))
        b, _ = self.vers_px(complex(1, 0))
        p.rect(a, y0, b, y1, fill="#1d2450", outline="")
        xm, _ = self.vers_px(complex(0.5, 0))
        p.ligne((xm, y0, xm, y1), fill="#3b2f6e", width=16)
        p.ligne((xm, y0, xm, y1), fill=VIOLET, width=3)
        p.texte(xm, 79, "le miroir (la ligne 1/2)", 16, True, VIOLET)
        for sg, lab in ((0.0, "0"), (0.5, "1/2"), (1.0, "1")):
            x, _ = self.vers_px(complex(sg, 0))
            p.texte(x, y1 + 14, lab, 15, sg == 0.5, VIOLET if sg == 0.5 else GRIS)
        if self.fini:
            for z in ZEROS:
                if z < self.TMAX:
                    p.etoile(*self.vers_px(complex(0.5, z)), 11)
        x, y = self.vers_px(self.s)
        if abs(self.s.real - 0.5) > 1e-9:
            xj, yj = self.vers_px(complex(1 - self.s.real, self.s.imag))
            p.ligne((x, y, xj, yj), fill=VIOLET, width=2, dash=(5, 5))
            p.rond(xj, yj, 13, outline=VIOLET, width=3)
            p.texte(xj, yj - 30, "son jumeau", 15, True, VIOLET)
            p.rond(x, y, 13, fill=VIOLET, outline="white", width=2)
            p.texte(x, y - 30, "zéro imaginaire", 15, True, TEXTE)
        else:
            if self.anim > 0:
                p.rond(x, y, 16 + (1.2 - self.anim) * 45, outline=VERT, width=3)
            p.rond(x, y, 19, outline=VIOLET, width=3)
            p.rond(x, y, 13, fill=VIOLET, outline="white", width=2)
            p.texte(x + 28, y, "son propre reflet", 15, True, TEXTE, anchor="w")

        if not self.fini:
            p.texte(910, 150, "La règle du miroir", 24, True, VIOLET)
            p.texte(910, 200, "(trouvée par Riemann en 1859)", 16, couleur=GRIS)
            p.texte(910, 300, "Si un zéro est à côté du miroir, il a forcément un jumeau, "
                    "pile en face.", 20, largeur=440)
            p.texte(910, 430, "Bouge le point violet : son jumeau le suit.", 20, largeur=440)
        else:
            self.dessiner_jauge(p)
        self.cadre(p)

    def dessiner_jauge(self, p):
        p.texte(910, 100, "Ce qui est prouvé aujourd'hui", 20, True, TEXTE)
        bx0, bx1, by0, by1 = 760, 830, 140, 540
        haut = lambda pc: by1 - pc / 100 * (by1 - by0)
        p.rect(bx0, by0, bx1, by1, fill="#232a5a", outline=BORD, width=2)
        p.rect(bx0, haut(67.2), bx1, by1, fill=VERT, outline="")
        p.ligne((bx0 - 8, haut(41.7), bx1 + 8, haut(41.7)), fill=ORANGE, width=3)
        p.texte(bx1 + 20, haut(100) + 4, "100 % = Riemann (pas prouvé)", 16, True, GRIS, anchor="w")
        p.texte(bx1 + 20, haut(67.2), "2026 : 67 % (avec Claude)", 17, True, VERT, anchor="w")
        p.texte(bx1 + 20, haut(41.7), "avant : 41 %", 17, True, ORANGE, anchor="w")
        p.texte(910, 568, "Les autres zéros ? Personne ne sait encore.", 16, couleur=TEXTE)


class Fleches(Ecran):
    TITRE = "3. Les flèches qui tournent"
    NUMERO = 3
    G = (40, 95, 620, 588)
    ORIG = (243, 341)            # où est le centre (le "0") dans le panneau
    ECH = 76                     # pixels par unité (le plus grand qui ne sort jamais du cadre)
    N = 80                       # nombre de flèches dessinées
    TMAX = 50.0
    COULEURS = [ORANGE, JAUNE, VERT]

    def __init__(self, jeu):
        super().__init__(jeu)
        self.t = 10.0
        self.joue = False
        self.trouves = []
        self.fige = 0.0
        ns = np.arange(1, self.N + 1)
        self.amp = np.where(ns % 2 == 1, 1.0, -1.0) / np.sqrt(ns)
        self.lns = np.log(ns)
        self.calculer()
        self.dire("ESPACE lance le temps : chaque flèche tourne à sa vitesse.",
                  "Rappuie sur ESPACE quand le point jaune touche la croix.")

    def calculer(self):
        somme = np.concatenate([[0j], np.cumsum(self.amp * np.exp(-1j * self.t * self.lns))])
        ox, oy = self.ORIG
        self.chaine = [(ox + v.real * self.ECH, oy - v.imag * self.ECH) for v in somme]
        self.eta = eta1(0.5 + 1j * self.t)

    def touche(self, k):
        if k == "space" and self.fige <= 0:
            if self.joue:
                self.joue = False
                self.verifier(True)
            else:
                self.joue = True

    def relache(self, k):
        if k in ("Left", "Right") and not self.joue and self.fige <= 0:
            self.verifier(False)

    def verifier(self, manuel):
        proche = min(ZEROS, key=lambda g: abs(g - self.t))
        if abs(self.eta) < 0.25 and abs(proche - self.t) < 0.6:
            self.t, self.joue, self.fige = proche, False, 1.4
            self.calculer()
            if proche in self.trouves:
                self.dire("Celui-là, tu l'as déjà !", "Relance le temps (ESPACE) pour trouver le suivant.",
                          couleur=ORANGE)
                return
            self.trouves.append(proche)
            n = len(self.trouves)
            if n >= 3:
                self.fini = True
                self.dire("Bravo ! Toutes les flèches s'annulent pile au centre.",
                          "C'est exactement ça, un zéro de zeta.", couleur=VERT)
            else:
                self.dire(f"Zéro n°{n} : temps = {fr(proche)}, tout s'annule !",
                          "Relance le temps (ESPACE) pour trouver le suivant.", couleur=VERT)
        elif manuel:
            self.dire("Pas encore : le point jaune n'est pas sur la croix.",
                      "Relance (ESPACE) ou ajuste doucement avec ← et →.", couleur=ORANGE)

    def maj(self, dt):
        if self.fige > 0:
            self.fige -= dt
            return
        k = self.jeu.touches
        v = (0.8 if self.joue else 0.0) + 0.5 * (("Right" in k) - ("Left" in k))
        if v:
            self.t = min(max(self.t + v * dt, 0.0), self.TMAX)
            if self.t >= self.TMAX and self.joue:
                self.joue = False
                self.dire("Fin de la piste !", "Reviens en arrière avec la flèche ←.", couleur=ORANGE)
            self.calculer()

    def dessiner(self, p):
        x0, y0, x1, y1 = self.G
        p.rect(x0, y0, x1, y1, fill=PANNEAU, outline=BORD, width=2)
        ox, oy = self.ORIG
        proche = abs(self.eta) < 0.25
        c = VERT if proche else "#cfd6ff"
        if self.fige > 0:
            p.rond(ox, oy, 16 + (1.4 - self.fige) * 60, outline=VERT, width=3)
        p.ligne((ox - 16, oy, ox + 16, oy), fill=c, width=3)
        p.ligne((ox, oy - 16, ox, oy + 16), fill=c, width=3)
        p.texte(ox - 22, oy + 22, "0", 15, True, c)
        pts = self.chaine
        for i in range(self.N, 0, -1):
            (xa, ya), (xb, yb) = pts[i - 1], pts[i]
            if i <= 3:
                p.ligne((xa, ya, xb, yb), fill=self.COULEURS[i - 1], width=5, arrow="last",
                        arrowshape=(14, 18, 6))
            else:
                f = (i - 4) / (self.N - 4)
                couleur = "#%02x%02x%02x" % (round(79 + 100 * f), round(195 - 110 * f), 247)
                p.ligne((xa, ya, xb, yb), fill=couleur, width=2.5 if i < 15 else 1.5)
        places = []                  # chaque numéro va du côté le plus loin des numéros déjà posés
        for i in range(1, 4):
            (xa, ya), (xb, yb) = pts[i - 1], pts[i]
            dx, dy = xb - xa, yb - ya
            n = math.hypot(dx, dy) or 1
            mx, my = (xa + xb) / 2, (ya + yb) / 2
            cotes = [(mx - dy / n * 20, my + dx / n * 20), (mx + dy / n * 20, my - dx / n * 20)]
            x, y = max(cotes, key=lambda c: min((math.hypot(c[0] - q[0], c[1] - q[1]) for q in places),
                                                default=1e9))
            places.append((x, y))
            p.texte(x, y, str(i), 18, True, self.COULEURS[i - 1])
        ex, ey = ox + self.eta.real * self.ECH, oy - self.eta.imag * self.ECH
        p.rond(ex, ey, 10, fill=JAUNE, outline="white", width=2)

        # panneau de droite
        p.texte(910, 112, f"temps = {fr(self.t)}", 28, True, TEXTE)
        tx0, tx1, ty = 720, 1140, 168
        p.ligne((tx0, ty, tx1, ty), fill=GRIS, width=3)
        for g in range(0, 51, 10):
            x = tx0 + g / self.TMAX * (tx1 - tx0)
            p.ligne((x, ty - 6, x, ty + 6), fill=GRIS, width=2)
            p.texte(x, ty + 20, str(g), 13, couleur=GRIS)
        for g in self.trouves:
            p.etoile(tx0 + g / self.TMAX * (tx1 - tx0), ty, 10)
        x = tx0 + self.t / self.TMAX * (tx1 - tx0)
        p.poly((x, ty - 10, x - 9, ty - 26, x + 9, ty - 26), fill=JAUNE, outline="")

        legende = [(ORANGE, "la 1 : ne tourne pas"), (JAUNE, "la 2 : tourne doucement"),
                   (VERT, "la 3 : un peu plus vite"), (BLEU, "les autres : encore plus vite")]
        for i, (couleur, txt) in enumerate(legende):
            y = 236 + i * 42
            p.ligne((712, y, 762, y), fill=couleur, width=5 if i < 3 else 2, arrow="last",
                    arrowshape=(12, 15, 5))
            p.texte(778, y, txt, 17, couleur=TEXTE, anchor="w")
        p.rond(737, 404, 10, fill=JAUNE, outline="white", width=2)
        p.texte(778, 404, "le total de TOUTES les flèches", 17, couleur=TEXTE, anchor="w")
        p.texte(910, 462, compteur(len(self.trouves)), 20, True, TEXTE)
        p.texte(910, 504, "ESPACE = lancer / arrêter      ← → = doucement", 15, couleur=GRIS)
        p.texte(910, 548, "Petit secret : ici zeta a des + et des -.", 14, couleur=GRIS)
        p.texte(910, 570, "Sur la ligne 1/2, elle a les mêmes zéros.", 14, couleur=GRIS)
        self.cadre(p)


class Pi(Ecran):
    TITRE = "4. π sort de nulle part"
    NUMERO = 4
    PI2_6 = math.pi ** 2 / 6

    def __init__(self, jeu):
        super().__init__(jeu)
        self.n = 0
        self.total = 0.0
        self.objectif = 1
        self.tenu = 0.0
        self.reserve = 0.0
        self.dire("ESPACE = ajouter un carré : 1, puis 1/4, puis 1/9...",
                  "Objectif : π ≈ 3,1. Garde ESPACE appuyé pour aller vite !")

    def touche(self, k):
        if k == "space":
            self.ajouter(1)

    def ajouter(self, m):
        for _ in range(m):
            self.n += 1
            self.total += 1.0 / (self.n * self.n)
        estim = math.sqrt(6 * self.total)
        if self.objectif == 1 and estim >= 3.1:
            self.objectif = 2
            self.dire(f"Bravo : π ≈ 3,1 avec seulement {self.n} carrés !",
                      "Objectif 2 : π ≈ 3,14. Garde ESPACE appuyé !", couleur=VERT)
        elif self.objectif == 2 and estim >= 3.14:
            self.objectif = 3
            self.fini = True
            self.dire("π sort tout seul, alors qu'il n'y a aucun cercle !",
                      "C'est zeta de 2 : Euler l'a trouvé en 1734.", couleur=VERT)

    def maj(self, dt):
        if "space" in self.jeu.touches:
            self.tenu = min(self.tenu + dt, 10.0)   # sans limite, 2,2 ** ... déborde après ~5 min
            if self.tenu > 0.35:
                self.reserve += min(3000.0, 4 * 2.2 ** ((self.tenu - 0.35) * 3)) * dt
                m = int(self.reserve)
                self.reserve -= m
                if m:
                    self.ajouter(m)
        else:
            self.tenu, self.reserve = 0.0, 0.0

    def dessiner(self, p):
        p.rect(40, 95, 700, 588, fill=PANNEAU, outline=BORD, width=2)
        p.texte(370, 150, "1 + 1/4 + 1/9 + 1/16 + ...", 30, True, TEXTE)
        p.texte(370, 200, "= la surface de tous les carrés ensemble", 18, couleur=GRIS)
        x, bas = 62, 540
        for i in range(1, min(self.n, 10) + 1):
            c = 190 / i
            p.rect(x, bas - c, x + c, bas, fill=JAUNE if i == self.n else "#3d7fbf", outline="white", width=1)
            if i <= 4:
                p.texte(x + c / 2, bas + 18, "1" if i == 1 else f"1/{i * i}", 15, True, TEXTE)
            x += c + 6
        if self.n > 10:
            p.texte(680, 300, f"+ {self.n - 10} carrés", 18, True, TEXTE, anchor="e")
            p.texte(680, 328, "tout petits", 18, couleur=GRIS, anchor="e")
        if self.n == 0:
            p.texte(370, 380, "Appuie sur ESPACE !", 26, True, JAUNE)

        bx0, bx1, by0, by1 = 760, 830, 120, 560
        haut = lambda v: by1 - v / 1.8 * (by1 - by0)
        p.rect(bx0, by0, bx1, by1, fill="#232a5a", outline=BORD, width=2)
        if self.total > 0:
            p.rect(bx0, haut(self.total), bx1, by1, fill=BLEU, outline="")
        p.ligne((bx0 - 10, haut(self.PI2_6), bx1 + 10, haut(self.PI2_6)), fill=ROUGE, width=3)
        p.texte(bx0 - 14, haut(self.PI2_6), "π²/6", 16, True, ROUGE, anchor="e")
        estim = math.sqrt(6 * self.total)
        p.texte(870, 160, f"Carrés : {self.n}", 21, True, TEXTE, anchor="w")
        p.texte(870, 205, f"Total : {fr(self.total, 4)}", 21, couleur=TEXTE, anchor="w")
        p.texte(870, 290, "π ≈ √(6 × total)", 18, couleur=GRIS, anchor="w")
        p.texte(870, 345, f"= {fr(estim, 4)}", 36, True, JAUNE, anchor="w")
        p.texte(870, 410, "Le vrai π :", 17, couleur=GRIS, anchor="w")
        p.texte(870, 440, "3,14159...", 21, True, TEXTE, anchor="w")
        obj = {1: "Objectif : 3,1", 2: "Objectif : 3,14", 3: "Objectifs réussis !"}[self.objectif]
        p.texte(870, 520, obj, 19, True, VERT if self.objectif == 3 else ORANGE, anchor="w")
        self.cadre(p)


class Fin(Ecran):
    def touche(self, k):
        if k == "Return":
            self.jeu.aller(0)

    def dessiner(self, p):
        p.texte(VW / 2, 90, "Bravo, tu as tout vu !", 38, True, JAUNE)
        lignes = [(BLEU, "1. Les zéros qu'on a trouvés sont tous sur la ligne 1/2."),
                  (VIOLET, "2. Le miroir : un zéro hors de la ligne aurait un jumeau."),
                  (VERT, "3. Un zéro = toutes les flèches qui tournent s'annulent."),
                  (JAUNE, "4. π se cache dans zeta : 1 + 1/4 + 1/9 + ... = π²/6.")]
        for i, (c, txt) in enumerate(lignes):
            p.texte(140, 180 + i * 56, txt, 21, i == -1, c, anchor="w")
        p.rect(140, 420, 1060, 560, fill="#1b2150", outline=BORD, width=2)
        p.texte(VW / 2, 462, "Prouvé en 2026 : au moins 67 % des zéros sont sur la ligne.", 20, True, VERT)
        p.texte(VW / 2, 516, "Les 33 % restants : personne ne sait. Le million attend toujours !", 18,
                couleur=TEXTE)
        self.jeu.bouton(330, 600, 580, 670, "Rejouer", lambda: self.jeu.aller(0), BLEU)
        self.jeu.bouton(620, 600, 870, 670, "Quitter", self.jeu.root.destroy, ROUGE)


# ==================================================================
# 4. LE JEU (fenêtre, souris, clavier, boucle)
# ==================================================================
class Jeu:
    ECRANS = [Menu, Machine, Miroir, Fleches, Pi, Fin]

    def __init__(self):
        try:                                    # texte net sur les écrans agrandis (Windows)
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass
        self.root = tk.Tk()
        self.root.title("La chasse aux zéros de Riemann")
        self.root.configure(bg=FOND)
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.k = min(sw * 0.92 / VW, sh * 0.84 / VH)
        w, h = round(VW * self.k), round(VH * self.k)
        self.root.geometry(f"{w}x{h}+{(sw - w) // 2}+{max(0, (sh - h) // 2 - 30)}")
        self.root.resizable(False, False)
        self.cv = tk.Canvas(self.root, width=w, height=h, bg=FOND, highlightthickness=0)
        self.cv.pack()
        self.stylo = Stylo(self.cv, self.k)
        self.touches = set()
        self.boutons = []
        self.souris = (-1, -1)
        self.rgb_carte = None
        self.cv.bind("<Button-1>", self._appui)
        self.cv.bind("<B1-Motion>", self._glisse)
        self.cv.bind("<ButtonRelease-1>", self._lache)
        self.cv.bind("<Motion>", self._bouge)
        self.root.bind("<KeyPress>", self._touche)
        self.root.bind("<KeyRelease>", self._relache)
        self.root.bind("<FocusOut>", lambda e: self.touches.clear())
        self.aller(0)
        self.dernier = time.perf_counter()
        self.root.after(50, self.root.focus_force)
        self.boucle()

    def aller(self, i):
        self.index = i
        self.ecran = self.ECRANS[i](self)

    def suivant(self):
        self.aller(min(self.index + 1, len(self.ECRANS) - 1))

    def bouton(self, x0, y0, x1, y1, txt, action, couleur=BLEU, taille=21):
        mx, my = self.souris
        dessus = x0 <= mx <= x1 and y0 <= my <= y1
        self.stylo.rect(x0, y0, x1, y1, fill=eclaircir(couleur) if dessus else couleur, outline="")
        self.stylo.texte((x0 + x1) / 2, (y0 + y1) / 2, txt, taille, True, "#0b0e1f")
        self.boutons.append((x0, y0, x1, y1, action))

    def _xy(self, e):
        return e.x / self.k, e.y / self.k

    def _appui(self, e):
        x, y = self._xy(e)
        for x0, y0, x1, y1, action in reversed(self.boutons):
            if x0 <= x <= x1 and y0 <= y <= y1:
                action()
                return
        self.ecran.appui(x, y)

    def _glisse(self, e):
        self.souris = self._xy(e)
        self.ecran.glisse(*self.souris)

    def _lache(self, e):
        self.ecran.lache(*self._xy(e))

    def _bouge(self, e):
        self.souris = self._xy(e)

    def _touche(self, e):
        k = e.keysym
        if k in self.touches:            # répétition automatique du clavier : on ignore
            return
        self.touches.add(k)
        if k == "Escape":
            self.aller(0)
        elif k == "Return" and self.ecran.fini:
            self.suivant()
        else:
            self.ecran.touche(k)

    def _relache(self, e):
        self.touches.discard(e.keysym)
        self.ecran.relache(e.keysym)

    def boucle(self):
        try:
            maintenant = time.perf_counter()
            dt = min(0.1, maintenant - self.dernier)
            self.dernier = maintenant
            self.ecran.maj(dt)
            self.cv.delete("all")
            self.boutons = []
            self.ecran.dessiner(self.stylo)
        finally:                         # une image ratée ne doit jamais figer le jeu
            self.root.after(16, self.boucle)


if __name__ == "__main__":
    Jeu().root.mainloop()
