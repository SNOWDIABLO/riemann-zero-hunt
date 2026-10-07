// Aide pour tests/test_maths.py : calcule zeta/eta de la version web (docs/maths.js)
// aux points reçus sur l'entrée standard (JSON [[re, im], ...]) et renvoie les résultats en JSON.
"use strict";
const RZ = require("../docs/maths.js");

let entree = "";
process.stdin.on("data", (morceau) => { entree += morceau; });
process.stdin.on("end", () => {
  const points = JSON.parse(entree);
  const sortie = {
    poids: Array.from(RZ.W),
    zeta: points.map(([re, im]) => RZ.zeta(re, im)),
    eta: points.map(([re, im]) => RZ.eta(re, im)),
    newton: points.map(([re, im]) => RZ.newtonZero(re, im)),
    couleurs: [0, 0.05, 0.3, 1, 3, 1e9].map((m) => RZ.couleur(m)),
  };
  process.stdout.write(JSON.stringify(sortie));
});
