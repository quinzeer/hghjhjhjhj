# Canapoil — dossier e-commerce

Accessoires anti-poils pour foyers avec chat ou chien, vendus en France. Ce dossier a été produit par 9 agents (recherche, stratégie, finance, site, marketing, red team, correction) le 12/10/2026.

## Par où commencer

1. `docs/tableau-de-bord.html` : la synthèse visuelle (paliers, économie unitaire, scénarios, portes de décision).
2. `docs/demarrage-J1-J14.md` : les 14 premiers jours, une action par jour avec son critère de réussite.
3. `docs/revue-red-team.md` : les 39 problèmes trouvés, leur statut, et les points qui attendent une décision.

## Contenu

| Dossier | Contenu |
|---|---|
| `recherche/` | Marché et niches (01), acquisition sans budget (02), droit et opérations France 2026 (03), données brutes Google Trends et relevés de prix, modèles de pages légales |
| `strategie/` | Stratégie complète (04) et `brand.json`, **source unique** de tous les prix, coûts, délais et textes |
| `finance/` | `modele_financier.py` → `modele_financier.xlsx` + `data.json` ; analyse (05) |
| `site/` | Site statique (Cloudflare Pages + Stripe Checkout), générateur, tests Playwright ; voir `site/README.md` |
| `shopify-kit/` | Import CSV, pages, thème, applications, checklist pour la phase de croissance |
| `marketing/` | Plan organique 90 jours, 30 scripts TikTok, créateurs affiliés, e-mails, SEO, lancement, passage au payant |
| `docs/` | Pilotage (`pilotage.xlsx`), gabarits d'étiquettes et de notices, captures du site, revue red team |

## Vérifier que tout fonctionne

```bash
python3 finance/modele_financier.py                     # 801 valeurs recalculées, 0 écart attendu
cd site && python3 outils/generer.py                    # régénère les 25 pages depuis brand.json
NODE_PATH="$(npm root -g)" node outils/verifier_site.js # 417/417 contrôles attendus
NODE_PATH="$(npm root -g)" node outils/tester_fonctions.js # 19/19 tests attendus
```

`python3 site/outils/generer.py --publication` refuse la mise en ligne tant que l'identité légale (`brand.json` → `identite`) n'est pas remplie.
