# -*- coding: utf-8 -*-
"""Vérifie les maths du jeu avec une 2e méthode indépendante (Euler-Maclaurin).
Lancer : python tests/test_maths.py   (depuis le dossier riemann-zero-hunt)"""
import math
import os
import random
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import riemann_jeu as rj

B = [1 / 6, -1 / 30, 1 / 42, -1 / 30, 5 / 66, -691 / 2730, 7 / 6, -3617 / 510, 43867 / 798, -174611 / 330]


def zeta_em(s, N=60, M=10):
    """zeta par Euler-Maclaurin (méthode totalement différente de celle du jeu)."""
    s = complex(s)
    tot = sum(n ** -s for n in range(1, N)) + N ** (1 - s) / (s - 1) + 0.5 * N ** -s
    for k in range(1, M + 1):
        prod = 1
        for j in range(2 * k - 1):
            prod *= s + j
        tot += B[k - 1] / math.factorial(2 * k) * prod * N ** (-s - 2 * k + 1)
    return tot


def ok(cond, msg):
    print(("OK   " if cond else "FAIL ") + msg)
    if not cond:
        ok.echecs += 1


ok.echecs = 0

# 1. zeta du jeu == Euler-Maclaurin sur toute la zone du jeu
random.seed(1)
pire = 0.0
for _ in range(3000):
    s = complex(random.uniform(-1, 2), random.uniform(0.3, 50))
    if abs(s - 1) < 0.05:
        continue
    a, b = rj.zeta1(s), zeta_em(s)
    pire = max(pire, abs(a - b) / max(1.0, abs(b)))
ok(pire < 1e-9, f"zeta jeu vs Euler-Maclaurin, 3000 points, pire écart relatif = {pire:.2e}")

# continuité à la frontière 1/2 (deux formules différentes de chaque côté)
pire = max(abs(rj.zeta1(complex(0.5 - 1e-9, t)) - rj.zeta1(complex(0.5, t))) for t in np.linspace(0.5, 50, 200))
ok(pire < 1e-7, f"pas de saut à la ligne 1/2 : {pire:.2e}")

# 2. valeurs connues
ok(abs(rj.zeta1(2) - math.pi ** 2 / 6) < 1e-12, "zeta(2) = π²/6")
ok(abs(rj.zeta1(0.5) - (-1.4603545088095868)) < 1e-10, "zeta(1/2) = -1,46035...")
ok(abs(rj.zeta1(-1) - (-1 / 12)) < 1e-10, "zeta(-1) = -1/12")
ok(abs(rj.zeta1(complex(0, 0.3)) - zeta_em(complex(0, 0.3))) < 1e-9, "zeta près de 0 (point le plus bas autorisé)")

# 3. la liste des zéros du jeu est juste
for g in rj.ZEROS:
    ok(abs(rj.zeta1(complex(0.5, g))) < 1e-9 and abs(zeta_em(complex(0.5, g))) < 1e-9,
       f"zéro à 1/2 + {g:.4f} i (|zeta| = {abs(rj.zeta1(complex(0.5, g))):.1e})")
    ok(abs(rj.eta1(complex(0.5, g))) < 1e-9, f"   eta aussi nulle là (niveau 3)")

# 4. Newton (niveau 1) retrouve le bon zéro depuis un point "Brûlant"
random.seed(2)
rates = 0
essais = 0
M = rj.Machine
for _ in range(3000):
    s = complex(random.uniform(M.SMIN, M.SMAX), random.uniform(0.3, M.TMAX))
    if abs(rj.zeta1(s)) >= rj.Machine.CAPTURE:
        continue
    essais += 1
    z = rj.newton_zero(s)
    if z is None or abs(z.real - 0.5) > 1e-8 or min(abs(z.imag - g) for g in rj.ZEROS) > 1e-6:
        rates += 1
ok(essais > 0 and rates == 0, f"Newton : {essais} départs 'Brûlant', {rates} ratés")

# zone de capture autour de chaque zéro (est-ce jouable ?)
for g in rj.ZEROS[:5]:
    d = abs((rj.zeta1(complex(0.5, g + 1e-5)) - rj.zeta1(complex(0.5, g - 1e-5))) / 2e-5)
    print(f"     zéro {g:6.2f} : |zeta'| = {d:.2f} -> zone de capture ±{rj.Machine.CAPTURE / d:.2f} en hauteur")

# 5. niveau 3 : la chaîne de flèches reste dans le panneau
x0, y0, x1, y1 = rj.Fleches.G
ox, oy = rj.Fleches.ORIG
ech = rj.Fleches.ECH
ns = np.arange(1, rj.Fleches.N + 1)
amp = np.where(ns % 2 == 1, 1.0, -1.0) / np.sqrt(ns)
xs, ys = [], []
for t in np.linspace(0, 50, 5001):
    S = np.concatenate([[0j], np.cumsum(amp * np.exp(-1j * t * np.log(ns)))])
    e = rj.eta1(0.5 + 1j * t)
    pts = np.concatenate([S, [e]])
    xs += [(ox + pts.real * ech).min(), (ox + pts.real * ech).max()]
    ys += [(oy - pts.imag * ech).min(), (oy - pts.imag * ech).max()]
print(f"     chaîne : x de {min(xs):.0f} à {max(xs):.0f} (panneau {x0}-{x1}), "
      f"y de {min(ys):.0f} à {max(ys):.0f} (panneau {y0}-{y1})")
ok(min(xs) > x0 and max(xs) < x1 and min(ys) > y0 and max(ys) < y1, "les flèches restent dans le panneau")

# fenêtre jouable du niveau 3 : durée où |eta| < 0,25 autour de chaque zéro
for g in rj.ZEROS[:6]:
    ts = np.linspace(g - 0.6, g + 0.6, 2401)
    dedans = [t for t in ts if abs(rj.eta1(0.5 + 1j * t)) < 0.25]
    print(f"     zéro {g:6.2f} : point jaune sur la croix pendant {max(dedans) - min(dedans):.2f} de temps "
          f"(= {(max(dedans) - min(dedans)) / 0.8:.2f} s en lecture)")

# 6. niveau 4 : combien de carrés pour 3,1 et 3,14 ?
tot, n, n31, n314 = 0.0, 0, None, None
while n314 is None:
    n += 1
    tot += 1 / n ** 2
    e = math.sqrt(6 * tot)
    if n31 is None and e >= 3.1:
        n31 = n
    if e >= 3.14:
        n314 = n
print(f"     π ≈ 3,1 après {n31} carrés ; π ≈ 3,14 après {n314} carrés")
ok(n31 < 60 and n314 < 2000, "objectifs du niveau 4 atteignables")

# 7. niveau 1 : le thermomètre ne dit jamais « Brûlant ! » loin d'un vrai zéro
sig = np.linspace(M.SMIN, M.SMAX, 201)
ts = np.linspace(0.3, M.TMAX, 1401)
S = sig[None, :] + 1j * ts[:, None]
Z = np.abs(rj.zeta(S))
dist = np.full(S.shape, 1e9)
for g in rj.ZEROS:
    dist = np.minimum(dist, np.abs(S - (0.5 + 1j * g)))
pieges = (Z < M.BRULANT) & (dist > 0.8)
ok(not pieges.any(), f"aucun faux « Brûlant » loin d'un zéro ({pieges.sum()} points)")


# ... et un joueur qui suit « plus chaud » depuis le départ finit par attraper un vrai zéro
def descente(s, pas=0.02, n=4000):
    h = 1e-5
    for _ in range(n):
        if abs(rj.zeta1(s)) < M.CAPTURE:
            return True
        g = complex(abs(rj.zeta1(s + h)) - abs(rj.zeta1(s - h)),
                    abs(rj.zeta1(s + 1j * h)) - abs(rj.zeta1(s - 1j * h)))
        if abs(g) < 1e-14:
            return False
        s = M.borner(M, s - pas * g / abs(g))
    return False


class FauxJeu:
    touches = set()
    rgb_carte = 0          # évite de lancer le calcul de la carte


ok(descente(M(FauxJeu()).s), "depuis le départ, suivre « plus chaud » mène à un zéro")

# 8. niveau 4 : garder ESPACE appuyé 10 minutes ne plante pas (avant : débordement après ~5 min)
FauxJeu.touches = {"space"}
niv4 = rj.Pi(FauxJeu())
try:
    for _ in range(6000):
        niv4.maj(0.1)
    ok(niv4.fini, f"ESPACE gardé 10 min : pas de plantage ({niv4.n} carrés)")
except Exception as exc:
    ok(False, f"ESPACE gardé 10 min : plantage {exc!r}")

# 9. version web (docs/maths.js) : mêmes résultats que Python
import json
import shutil
import subprocess

if shutil.which("node") is None:
    print("SKIP version web : node n'est pas installé")
else:
    random.seed(3)
    pts = [[random.uniform(-1, 2), random.uniform(0.3, 50)] for _ in range(1500)]
    pts += [[0.5, g] for g in rj.ZEROS] + [[0.62, 14.0], [0.9, 21.3], [1.3, 30.6]]
    web = json.loads(subprocess.run(["node", os.path.join(os.path.dirname(__file__), "test_web.js")],
                                    input=json.dumps(pts), capture_output=True, text=True, check=True).stdout)
    ok(np.max(np.abs(np.array(web["poids"]) - rj._POIDS)) < 1e-13, "web : poids de Borwein identiques")
    pire = max(abs(complex(*z) - rj.zeta1(complex(*p))) / max(1.0, abs(rj.zeta1(complex(*p))))
               for p, z in zip(pts, web["zeta"]))
    ok(pire < 1e-9, f"web : zeta identique à Python ({pire:.1e})")
    pire = max(abs(complex(*e) - rj.eta1(complex(*p))) for p, e in zip(pts, web["eta"]))
    ok(pire < 1e-9, f"web : eta identique à Python ({pire:.1e})")
    for p, z in zip(pts[-3:], web["newton"][-3:]):
        zp = rj.newton_zero(complex(*p))
        ok(z is not None and zp is not None and abs(complex(*z) - zp) < 1e-8,
           f"web : Newton trouve le même zéro depuis {p}")
    ref = rj.carte_couleurs(np.array([0, 0.05, 0.3, 1, 3, 1e9], dtype=complex))
    ok(np.max(np.abs(np.array(web["couleurs"]) - ref.astype(int))) <= 1, "web : mêmes couleurs de carte")

print("\nTOUT EST BON" if ok.echecs == 0 else f"\n{ok.echecs} ÉCHEC(S)")
sys.exit(1 if ok.echecs else 0)
