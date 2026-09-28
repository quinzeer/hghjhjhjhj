# Paramètres du studio (MISSION §0)

`docs/MISSION.md` §0 est livré avec des champs vides. Ce fichier tient la valeur **en vigueur** de chaque paramètre et son statut. Règle du §0 : champ vide → hypothèse prudente + entrée dans `docs/NEEDS_HUMAN.md`.

- `hypothèse` : choisie par Claude, réversible, à confirmer.
- `confirmé` : validé par l'humain (date + canal).
- `délégué (Claude)` : décidé par Claude sur délégation explicite de l'humain (ADR-005), réversible.
- `make verify-phase-0` lit ce tableau : `docs/research/channel-concepts.md` reste exigé tant que les deux concepts ne sont pas `confirmé`.

| Paramètre | Valeur en vigueur | Statut | Raison de l'hypothèse | Mis à jour |
|---|---|---|---|---|
| Nom du studio | `studio` (nom de code technique) | hypothèse | Aucun impact d'architecture ; le nom public viendra avec les chaînes | 2026-09-28 |
| Concept chaîne A | « Civilisations reconstruites » (C02 + C07) | délégué (Claude) | ADR-005 ; à réexaminer après la mesure de demande (H0) | 2026-09-28 |
| Concept chaîne B | « Échelles de l'espace et du temps » (C03 + C09) | délégué (Claude) | ADR-005 ; idem | 2026-09-28 |
| Langue maître | anglais pour A et B ; piste française par `localizer` (phase 4) ; champ `language` par chaîne, rien en dur | délégué (Claude) | ADR-005 : audience et RPM plus élevés | 2026-09-28 |
| Offre Claude du studio | Max 5x | hypothèse | Offre la plus contrainte : dimensionner sur elle évite de dépendre d'un quota qu'on n'a peut-être pas | 2026-09-28 |
| Plafond par vidéo | voir `docs/COST_MODEL.md` § Plafonds | hypothèse | Dérivé du modèle de coût, pas fixé à l'aveugle | 2026-09-28 |
| Temps humain disponible | 30 min par jour | hypothèse | §11 : ≤ 15 min par vidéo ; 30 min/jour couvre la cadence ci-dessous avec marge | 2026-09-28 |
| Cadence cible par chaîne | 1 long + 3 Shorts par semaine au lancement | hypothèse | Prudente tant que `docs/CAPACITY.md` (phase 3) n'a pas mesuré le débit GPU réel | 2026-09-28 |
| OS de la machine GPU | Ubuntu 24.04 LTS natif | hypothèse (contrainte technique) | WSL2 ne permet pas d'épingler un GPU par index (`infra.md` S39) : un worker par carte exige Linux natif (ADR-001, ADR-003) | 2026-09-28 |
| Clés et comptes disponibles | aucun supposé | hypothèse | Tout ce qui manque est listé dans `docs/NEEDS_HUMAN.md` | 2026-09-28 |
