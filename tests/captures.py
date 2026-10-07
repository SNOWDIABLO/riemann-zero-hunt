# -*- coding: utf-8 -*-
"""Ouvre le jeu, met chaque niveau dans un état typique, et fait une capture d'écran
dans docs/images/. Sert aussi de test « tout se lance sans planter ».
Windows uniquement (la capture passe par PowerShell).
Lancer : python tests/captures.py   (depuis le dossier riemann-zero-hunt)"""
import os
import subprocess
import sys
import time

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ICI, ".."))
import riemann_jeu as rj  # noqa: E402

IMAGES = os.path.join(ICI, "..", "docs", "images")
os.makedirs(IMAGES, exist_ok=True)

PS = r"""
Add-Type -AssemblyName System.Drawing
Add-Type -TypeDefinition 'using System.Runtime.InteropServices; public class Dpi {{ [DllImport("user32.dll")] public static extern bool SetProcessDPIAware(); }}'
[Dpi]::SetProcessDPIAware() | Out-Null
$b = New-Object System.Drawing.Bitmap {w}, {h}
$g = [System.Drawing.Graphics]::FromImage($b)
$g.CopyFromScreen({x}, {y}, 0, 0, $b.Size)
$b.Save('{chemin}', [System.Drawing.Imaging.ImageFormat]::Png)
"""


def tourner(jeu, n=8):
    for _ in range(n):
        jeu.root.update()
        time.sleep(0.02)


def capture(jeu, nom):
    tourner(jeu)
    r = jeu.root
    chemin = os.path.abspath(os.path.join(IMAGES, nom + ".png"))
    script = PS.format(w=r.winfo_width(), h=r.winfo_height(), x=r.winfo_rootx(), y=r.winfo_rooty(),
                       chemin=chemin)
    subprocess.run(["powershell", "-NoProfile", "-Command", script], check=True)
    print("capture :", chemin)


def main():
    jeu = rj.Jeu()
    jeu.root.attributes("-topmost", True)
    tourner(jeu, 20)
    capture(jeu, "0-menu")

    # Niveau 1 : en pleine recherche, puis carte révélée
    jeu.aller(1)
    e = jeu.ecran
    for i in range(60):                      # un petit trajet pour avoir une traînée à droite
        e.s = complex(1.3 - i * 0.012, 6 + i * 0.12)
        e.maj(0.016)
        tourner(jeu, 1)
    capture(jeu, "1-machine-recherche")
    for z in rj.ZEROS[:3]:
        e.s = complex(0.5, z + 0.1)
        e.sortir = False
        e.maj(0.016)
        e.fige = 0
        e.maj(0.016)
    while jeu.rgb_carte is None:
        tourner(jeu, 5)
    e.s = complex(0.85, 28.0)
    e.sortir = True
    e.maj(0.016)
    assert e.fini and len(e.trouves) == 3, "le niveau 1 devrait être gagné"
    capture(jeu, "1-machine-carte")

    # Niveau 2 : avant / après
    jeu.aller(2)
    capture(jeu, "2-miroir-jumeau")
    e = jeu.ecran
    e.placer(complex(0.62, 20.0))            # traverse le miroir : doit se coller
    assert e.fini and e.s.real == 0.5, "le zéro devrait se coller au miroir"
    e.anim = 0
    capture(jeu, "2-miroir-prouve")

    # Niveau 3 : flèches en mouvement, puis sur un zéro
    jeu.aller(3)
    e = jeu.ecran
    e.t = 12.6
    e.calculer()
    capture(jeu, "3-fleches")
    e.t = rj.ZEROS[0] + 0.02
    e.calculer()
    e.verifier(True)
    assert e.trouves == [rj.ZEROS[0]], "le zéro 1 devrait être validé"
    e.fige = 0
    capture(jeu, "3-fleches-zero")
    e.t = 17.0
    e.calculer()
    e.verifier(True)                          # loin d'un zéro : message « pas encore »
    assert len(e.trouves) == 1

    # Niveau 4 : quelques carrés, puis objectifs atteints
    jeu.aller(4)
    e = jeu.ecran
    for _ in range(6):
        e.touche("space")
    capture(jeu, "4-pi-debut")
    e.ajouter(23 - e.n)
    assert e.objectif == 2, "π ≈ 3,1 devrait être atteint"
    e.ajouter(600 - e.n)
    assert e.fini, "π ≈ 3,14 devrait être atteint"
    capture(jeu, "4-pi-gagne")

    jeu.aller(5)
    capture(jeu, "5-fin")
    jeu.root.destroy()
    print("TOUT S'EST LANCÉ SANS PLANTER")


if __name__ == "__main__":
    main()
