# Paramètres du studio (MISSION §0)

`docs/MISSION.md` §0 est livré avec des champs vides. Ce fichier tient la valeur **en vigueur** de chaque paramètre et son statut. Règle du §0 : champ vide → hypothèse prudente + entrée dans `docs/NEEDS_HUMAN.md`.

- `hypothèse` : choisie par Claude, réversible, à confirmer.
- `confirmé` : validé par l'humain (date + canal).
- `make verify-phase-0` lit ce tableau : `docs/research/channel-concepts.md` reste exigé tant que les deux concepts ne sont pas `confirmé`.

| Paramètre | Valeur en vigueur | Statut | Raison de l'hypothèse | Mis à jour |
|---|---|---|---|---|
| Nom du studio | `studio` (nom de code technique) | hypothèse | Aucun impact d'architecture ; le nom public viendra avec les chaînes | 2026-09-28 |
| Concept chaîne A | à choisir dans `docs/research/channel-concepts.md` | en attente | Le §0 dit « propose » par défaut ; 6 concepts classés livrés en phase 0 | 2026-09-28 |
| Concept chaîne B | à choisir dans `docs/research/channel-concepts.md` | en attente | Idem | 2026-09-28 |
| Langue maître | par chaîne (champ `language` de la configuration de chaîne), aucune langue codée en dur | hypothèse | Choix lié au concept et au RPM (voir `docs/research/economics.md`) ; l'architecture reste multilingue | 2026-09-28 |
| Offre Claude du studio | Max 5x | hypothèse | Offre la plus contrainte : dimensionner sur elle évite de dépendre d'un quota qu'on n'a peut-être pas | 2026-09-28 |
| Plafond par vidéo | voir `docs/COST_MODEL.md` § Plafonds | hypothèse | Dérivé du modèle de coût, pas fixé à l'aveugle | 2026-09-28 |
| Temps humain disponible | 30 min par jour | hypothèse | §11 : ≤ 15 min par vidéo ; 30 min/jour couvre la cadence ci-dessous avec marge | 2026-09-28 |
| Cadence cible par chaîne | 1 long + 3 Shorts par semaine au lancement | hypothèse | Prudente tant que `docs/CAPACITY.md` (phase 3) n'a pas mesuré le débit GPU réel | 2026-09-28 |
| OS de la machine GPU | Ubuntu 24.04 LTS | hypothèse | NVIDIA Container Toolkit natif, sans la couche WSL2 | 2026-09-28 |
| Clés et comptes disponibles | aucun supposé | hypothèse | Tout ce qui manque est listé dans `docs/NEEDS_HUMAN.md` | 2026-09-28 |
