# Recette du rendu « qui fait vrai »

Le réalisme vient d'une pile de petits signaux. Chacun est cheap ; ensemble ils font la différence entre « démo WebGL » et « plan tourné ».

## Lumière (le plus important)
- **Une lumière principale qui porte des ombres douces** (le kit la crée selon le `look`), plus 1–2 contre-jours colorés qui détachent les objets du fond.
- **IBL** : l'environnement du kit donne des reflets crédibles sur tout ce qui est brillant. Un objet laqué sans reflets paraît faux ; vérifier qu'on voit un reflet de « softbox » sur les billes, écrans, métaux.
- **Ombre de contact** sous chaque objet posé (`K.contactShadow`) : sans elle, les objets flottent.
- **Émissifs + bloom** : fenêtres allumées, LED, écrans → `K.mat.emissive(couleur, 2–5)` ; le bloom ne prend que ce qui dépasse l'exposition.
- Pour un extérieur réaliste, charger une HDRI Poly Haven (CC0) : `K.loadHDRI(...)`.

## Matériaux
- Rien n'est parfaitement lisse ni parfaitement mat : `roughness` entre 0,15 et 0,85, jamais 0 ni 1 (sauf chrome).
- Le **clearcoat** (vernis) sur les objets fabriqués (jouets, billes, voitures, céramique) ; le mat pour le carton, le plâtre, le tissu.
- Varier : deux objets identiques côte à côte → changer légèrement couleur, rugosité ou échelle (`K.rng`).
- Les textures dessinées (`K.canvasTex`) gagnent à recevoir du grain, de l'usure, des bords irréguliers.

## Échelle et physique
- Travailler en **mètres réels** : une tasse fait 0,1 m, une voiture 4,5 m, une maison 8 m. La caméra, la profondeur de champ et la vitesse de chute en dépendent.
- Les objets qui tombent accélèrent (`y = y0 − 4,9·t²`), rebondissent avec amortissement (`K.bounce`), et **s'écrasent légèrement** à l'impact (échelle y 0,9 pendant 0,1 s).
- Rien ne démarre ni ne s'arrête sec : `easeOut` à l'arrivée, `easeInOut` pour les caméras.
- Pour une vraie simulation (billes, dominos, chutes en chaîne), s'inspirer de la physique déterministe du projet « Arène des Nations » (maths maison bit-exactes, pas fixe 480 Hz, enregistrement puis relecture).

## Caméra (langage de tournage)
- **Toujours un léger mouvement** : orbite lente (0,05–0,1 rad/s), travelling avant, grue. Un plan fixe paraît « rendu ».
- **Bougé à l'épaule** discret (`shake` 0,003) et secousse franche sur les impacts (0,02–0,04, décroissance 0,4 s).
- **Profondeur de champ** sur les plans rapprochés (`focus` sur le sujet, `aperture` 0,003–0,006) : c'est le signal « vraie caméra » le plus fort.
- Focales : `fov` 30–40 en portrait (plus serré = plus « cinéma »), 45–50 pour les plans larges.
- Varier les plans toutes les 2–4 s : large → rapproché → détail → large. Transition = `K.mixCam` sur 0,6–1 s, ou coupe franche sur un temps fort.

## Image
- Tone mapping ACES, grain, vignettage, aberration chromatique légère : déjà dans le kit. Flash blanc (`K.grade.uFlash`) de 0,2–0,35 s sur une révélation ; teinte rouge (`uTint`) pour le danger ; bandes cinéma (`uBars = 1`) pour un replay ou un flashback.
- La 3D est rendue à 0,75× puis agrandie : invisible après compression, et presque 2× plus rapide.

## Son (la moitié du réalisme)
- **Chaque mouvement visible a un son** : chute → `land`, choc métal → `clang`, apparition → `pop`/`whoosh`, révélation → `riser` puis `impact`, horloge → `tick`, argent → `coin`.
- Voix au-dessus de tout (le mixeur la place ~8 dB au-dessus du fond) ; musique qui monte avec `energy` et se coupe avant la révélation (`drop`).
- Un temps de silence de 0,4 s avant le payoff est plus fort que n'importe quel effet.

## Contrôle qualité avant rendu complet
1. Planche contact (`--preview 8`) : netteté, cadrage, lisibilité des textes à taille miniature.
2. Deux ou trois images en gros plan (`--at`) sur les moments clés.
3. Après rendu : le journal affiche loudness et crête ; viser −14 LUFS et crête ≤ −1 dBTP.
