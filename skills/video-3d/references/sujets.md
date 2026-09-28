# Traduire n'importe quel sujet en 3D

## Les six formats (et le modèle de départ)

| Format | Structure | Modèle | Exemples |
|---|---|---|---|
| **Récit** « C'est l'histoire de… » | hook → contexte → complication (« mais ») → retournement → chute | `recit` | fait divers insolite, histoire d'un objet, d'une entreprise, d'un lieu |
| **Explication** | question → idée reçue → mécanisme en 3 étapes → réponse | `recit` (stations = étapes) | science, économie, « comment ça marche » |
| **Comparaison / échelle** | deux ou N éléments, du plus petit au plus grand, chiffre à chaque fois | `comparaison` | tailles, prix, vitesses, salaires, populations |
| **Classement** | du n°N au n°1, le meilleur en dernier | `classement` | top 5, records, pays, inventions |
| **Simulation / jeu** | règle simple → escalade → vainqueur | projet Arène des Nations | courses, éliminations, « et si… » physiques |
| **Portrait** d'objet ou de lieu | objet héros en orbite, annotations qui apparaissent | `recit` avec une seule station | produit, monument, animal |

## Équivalents visuels

| Le sujet parle de… | On montre en 3D |
|---|---|
| une personne réelle | un **objet qui la symbolise** (outil, vêtement, trophée), une **silhouette stylisée** sans visage, son **lieu** en maquette ; jamais son visage |
| un lieu (ville, pays, bâtiment) | **maquette** façon diorama (`InstancedMesh` pour les immeubles), carte extrudée (`ExtrudeGeometry`), drapeau dessiné (`canvasTex`) |
| de l'argent | liasses (boîtes texturées), pièces (cylindres or), lingots (`RoundedBox` + `mat.gold`), montant qui s'incrémente dans `overlay` |
| le temps, une date | calendrier dont les pages tombent, horloge, sablier, frise au sol que la caméra longe |
| une quantité, une statistique | pile d'objets unitaires (`InstancedMesh`), barres 3D, jauge qui se remplit |
| une découverte | objet caché sous un drap/sable qui se révèle, lumière qui s'allume, zoom de carte |
| un danger, une catastrophe | teinte rouge, alarme, objet qui vacille, fissures (géométrie découpée) ; pas de victimes représentées |
| internet, une appli | smartphone 3D (`RoundedBox` + écran `canvasTex` + émissif), notifications qui surgissent |
| un animal | forme stylisée en primitives, ou modèle glTF CC0 (Quaternius, Poly Pizza en vérifiant la licence) |
| l'espace, la nature | `look: "space"` + sphères texturées ; `look: "day"` + sol, arbres en cônes/sphères instanciés |
| une idée abstraite | métaphore d'objet : cadenas (sécurité), pont (lien), engrenages (système), balance (justice) |

## Limites à dire franchement
- Pas d'humains photoréalistes, pas de reconstitution qui pourrait passer pour une vraie vidéo d'un événement réel.
- Pas de logos ni de marques déposées : objets génériques, noms à l'oral si nécessaire.
- Sujets sensibles (santé, finance, droit, drames récents) : faits sourcés, ton sobre, aucune dramatisation des victimes.

## Hooks qui marchent en 3D
- **Résultat d'abord** : on montre la fin (la maison, le trésor, le vainqueur) puis « il y a un an, c'était un trombone ».
- **Écart de taille ou de prix** : deux objets côte à côte, l'un minuscule, l'autre immense, chiffre géant.
- **Objet impossible** : un objet familier dans une situation absurde, dès la première image.
- **Compte à rebours** visible à l'écran.
- La phrase du hook, le texte à l'écran et l'image disent la même chose ; l'action est déjà en mouvement à l'image 1.
