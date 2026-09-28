# Modèles vidéo et image à poids ouverts — inventaire, licences, capacité 16 Go

> Consulté le : 2026-09-28 · Auteur : researcher · Version : 1 · Portée : inventaire exhaustif des modèles vidéo et image à poids ouverts disponibles au 28/09/2026 (T2V, I2V, TI2V, S2V, Animate, upscaling, interpolation, lip-sync, identité), licences exactes et éligibilité France/UE, capacité à tenir dans 4× RTX 4070 Ti Super 16 Go, outillage (ComfyUI, diffusers, accélérateurs), rendu procédural (Blender, three.js/Remotion), marquage C2PA/IPTC, et recommandation pour `make bench-models`.

## Synthèse

- La ligne MISSION §4 « Wan 2.2 / 2.7 (Apache 2.0) » est **inexacte** : seul **Wan 2.2** est Apache 2.0 ; Wan 2.5, 2.6 et 2.7 sont des générations **fermées** (API Bailian uniquement), au moins jusqu'à fin septembre 2026 [S1][S4].
- **HunyuanVideo 1.5 et HunyuanImage 2.1/3.0** confirment l'exclusion territoriale : la licence Tencent Hunyuan Community exclut explicitement l'UE, le Royaume-Uni et la Corée du Sud — vérifié texte de licence à la main [S9][S10][S11]. **Élimination pour un studio opéré en France.**
- **LTX-2 / LTX-2.x** (Lightricks) est bien ouvert avec audio natif, mais sous une licence « communautaire » à seuil de revenu (10 M$ ARR), pas Apache 2.0 comme le laissait entendre la mission [S6][S7].
- Meilleure base vidéo ouverte, sans restriction territoriale ni seuil, pour la production : **Wan 2.2** (T2V/I2V/TI2V/S2V/Animate, Apache 2.0) [S1][S2][S3], et en alternative **CogVideoX1.5** — mais attention, CogVideoX1.5 n'est **pas** Apache 2.0 : licence propriétaire « CogVideoX License » avec enregistrement commercial gratuit et plafond de 1 M visites/mois [S18]. **LongCat-Video** (MIT, Meituan) et **Open-Sora 2** (Apache 2.0) et **Step-Video-T2V** (MIT) et **Kandinsky 5.0** (MIT/Apache) et **MAGI-1** (Apache 2.0) et **Mochi 1** (Apache 2.0) sont des alternatives pleinement permissives [S12][S13][S14][S15][S16][S17].
- Seul **Wan2.2-TI2V-5B** (5B, dense, 720p/24fps/5s) tient nativement dans 24 Go et s'approche de 16 Go avec quantification ; les variantes A14B (14B×2 MoE) exigent l'offload ou le multi-GPU (xDiT/USP) sur 4070 Ti Super [S3][S24][S43].
- Côté image, **FLUX.1 [schnell]**, **Qwen-Image / Qwen-Image-Edit**, **Z-Image (Turbo)**, **Chroma** et le **FLUX.2 [klein] 4B** sont Apache 2.0 pleinement commerciaux [S19][S20][S21][S28][S29]. **FLUX.1 [dev]/[Kontext dev]** et **FLUX.2 [dev] 32B** restent en licence non-commerciale sur le modèle (mais sorties commerciales autorisées) — zone grise à éviter pour un pipeline de revenu [S22][S23]. **SD 3.5** bascule en payant au-delà de 1 M$ de revenu annuel [S25]. **HunyuanImage 2.1/3.0** exclus UE.
- Outils d'identité : **PuLID**, **InstantID** (code) et **IP-Adapter** sont Apache 2.0, mais **InstantID** dépend d'InsightFace/antelopev2 en licence **non-commerciale** — risque à isoler [S30][S31][S32].
- Upscaling/interpolation : **SeedVR2** et **FlashVSR** (Apache 2.0) tiennent en 16 Go via GGUF/FP8 ; **Real-ESRGAN** BSD-3 ; **RIFE** MIT ; **GIMM-VFI** en **S-Lab License 1.0 non-commerciale** — à exclure du pipeline commercial [S33][S34][S35][S36][S37].
- Lip-sync : **LatentSync**, **MuseTalk**, **InfiniteTalk**, **EchoMimic v3** sont tous Apache 2.0/MIT [S38][S39][S40][S41]. Topaz et équivalents propriétaires sont **hors règle** (poids fermés).
- ComfyUI est **GPL-3.0** ; l'exécuter en service privé (sans distribution) ne déclenche pas d'obligation de publication du code, d'après la clause GPLv3 sur la « conveyance » [S42].
- Ada Lovelace (sm_89) supporte nativement le **FP8** (4ᵉ génération Tensor Cores) ; le **FP4** natif (tcgen05/mxf4) n'apparaît dans la documentation PTX que pour les Tensor Cores de 5ᵉ génération (Blackwell) — absence de mention pour sm_89 [S45][S46].
- C2PA (c2pa-python, c2patool) est double licence Apache-2.0/MIT ; l'IPTC `digitalSourceType` prévoit précisément `trainedAlgorithmicMedia` et `compositeSynthetic` pour nos cas [S47][S48][S49]. YouTube lit les métadonnées C2PA et applique un label automatique non modifiable par le créateur [S50].

## Constats

| # | Constat | Sources | Confiance | Conséquence pour le studio |
|---|---|---|---|---|
| 1 | Wan 2.2 (T2V-A14B, I2V-A14B, TI2V-5B, S2V-14B, Animate-14B) est publié sous Apache 2.0, sans seuil ni restriction territoriale. | [S1][S2][S3] | élevée | Modèle vidéo pivot du studio, éligible France/UE sans réserve. |
| 2 | Wan 2.5, 2.6, 2.7 et 3.0 (génération 2026) sont fermés : accès uniquement via l'API cloud Bailian d'Alibaba, pas de poids publiés. | [S4] | moyenne (source praticien/SEO, recoupée par l'absence de dépôt GitHub officiel et par le classement Artificial Analysis qui ne montre aucun « Wan 2.5/2.6/2.7 open weights ») | La ligne MISSION §4 « Wan 2.2/2.7 Apache 2.0 » est fausse pour 2.7 ; le studio doit rester sur Wan 2.2 tant qu'aucun poids Wan ≥2.5 n'est publié. |
| 3 | HunyuanVideo-1.5 et HunyuanImage-2.1/3.0 utilisent le « Tencent Hunyuan Community License Agreement », qui exclut explicitement « the European Union, United Kingdom and South Korea » de son territoire. | [S9][S10][S11] | élevée (texte de licence lu intégralement) | Élimination ferme pour un studio opéré en France : ni HunyuanVideo-1.5 ni HunyuanImage 2.1/3.0 ne sont utilisables, même via FramePack qui les réutilise comme base (voir #12). |
| 4 | LTX-2 (Lightricks, 19B = 14B vidéo + 5B audio, audio natif synchronisé) est ouvert sous une « LTX-2.x Community License Agreement » (révision du 11/08/2026) : gratuit pour la recherche/usage non-commercial et pour toute entité de moins de 10 M$ de revenu annuel ; licence commerciale payante au-delà. Aucune restriction territoriale identifiée dans le texte. | [S6][S7][S8] | élevée (texte de licence lu) | Utilisable en France tant que le studio reste sous 10 M$ ARR (cas actuel) ; à réévaluer si le studio grossit. Pas Apache 2.0 contrairement à la formulation de la mission. |
| 5 | CogVideoX1.5-5B n'est pas Apache 2.0 : licence propriétaire « The CogVideoX License » (zhipuai/Z.ai), avec enregistrement commercial gratuit obligatoire et plafond de 1 million de visites/mois ; juridiction Chine. | [S18] | élevée (texte de licence lu) | À utiliser seulement après enregistrement sur open.bigmodel.cn ; documenter la démarche dans NEEDS_HUMAN si retenu. Alternative sans démarche : Wan 2.2, Open-Sora 2, LongCat-Video. |
| 6 | Mochi 1 (Genmo, 10B, AsymmDiT) est Apache 2.0 mais son implémentation de référence recommande ≥1 GPU H100 ; la doc communautaire mentionne une exécution possible sous 20-22 Go VRAM en bfloat16/optimisé, au-delà de 16 Go. | [S16][S17] | moyenne | Ne tient pas dans 16 Go sans compromis importants ; candidat secondaire seulement si quantification 8-bit/GGUF confirmée en banc local. |
| 7 | MAGI-1 (Sand.ai) est Apache 2.0 ; le modèle complet est 24B (multi-GPU professionnel), mais une variante Distill 4.5B / Distill+Quant existe pour GPU unique. | [S15] | moyenne | Utiliser la variante 4.5B Distill+Quant pour tenir en 16 Go ; le 24B nécessite un parallélisme multi-GPU explicite. |
| 8 | FLUX.1 [schnell] est Apache 2.0 (poids et usage commercial libres) ; FLUX.1 [dev] et FLUX.1 Kontext [dev] sont sous « FLUX.1 [dev] Non-Commercial License » : le modèle ne peut pas être utilisé pour une « activité génératrice de revenu », mais la licence autorise explicitement l'usage commercial des **sorties** (§2d : « You may use Output for any purpose (including for commercial purposes) »). | [S19][S22][S23] | élevée (texte de licence lu) | Zone grise juridique : générer les visuels d'une vidéo monétisée avec [dev] pourrait être lu comme une « activité génératrice de revenu » via le modèle lui-même. Recommandation : réserver [dev]/Kontext[dev] aux tests non-commerciaux, utiliser [schnell] ou Qwen-Image/Z-Image/Chroma (tous Apache 2.0) comme chemin de production par défaut. |
| 9 | FLUX.2 : seul le variant [klein] 4B est Apache 2.0 ; [klein] 9B et [dev] 32B restent sous licence non-commerciale (paiement requis pour déploiement commercial du modèle). | [S28][S29] | élevée | Même logique que #8 : [klein]-4B seul est un chemin de production sans ambiguïté. |
| 10 | Qwen-Image et Qwen-Image-Edit sont Apache 2.0, vérifié directement sur le tag de licence HuggingFace (`license: apache-2.0`), malgré des blogs SEO de tiers évoquant une « Qwen-Image-2.1 » à licence restrictive non confirmée officiellement. | [S20][S21] | élevée (tag officiel vérifié) | Qwen-Image-Edit = candidat solide pour édition d'image/cohérence de personnage, sans restriction commerciale. |
| 11 | Stable Diffusion 3.5 (Large/Medium) est sous Stability AI Community License : gratuit jusqu'à 1 000 000 USD de revenu annuel cumulé (toutes sources), licence Enterprise payante au-delà. | [S25] | élevée (texte de licence lu) | Utilisable tant que le studio reste sous le seuil ; à surveiller si plusieurs chaînes générent des revenus cumulés. |
| 12 | FramePack (lllyasviel) est lui-même Apache 2.0, mais son modèle I2V par défaut (`FramePackI2V_HY`) est un fine-tune de HunyuanVideo 13B, dont la licence Tencent exclut l'UE (constat #3). | [S13][S9] | moyenne (le lien de dépendance est documenté par la communauté, la licence de base est confirmée) | FramePack tel quel n'est pas utilisable en l'état pour la France ; nécessiterait un ré-entraînement sur une base non-Hunyuan (non fait à ce jour). À exclure de la shortlist. |
| 13 | SeedVR2 (ByteDance-Seed) est Apache 2.0 et tient en 8-16 Go via GGUF Q4_K_M + BlockSwap + tiling VAE. | [S33] | moyenne (communauté ComfyUI, pas de mesure indépendante) | Candidat upscaler par défaut ; à confirmer par `make gpu-smoke`. |
| 14 | FlashVSR (OpenImagingLab, CVPR 2026) est publié en Apache et vise le temps réel (« streaming VSR ») ; poids ouverts depuis octobre 2025. | [S34] | moyenne | Second candidat upscaler, un cran plus récent que SeedVR2, à comparer en banc. |
| 15 | RIFE (Practical-RIFE) est MIT mais le jeu de données d'entraînement porte potentiellement des restrictions non-commerciales séparées des poids eux-mêmes ; à ne pas réentraîner sans vérifier. | [S35] | moyenne | Utilisable pour l'inférence (interpolation) sans réserve ; ne pas redistribuer/réentraîner sur le dataset d'origine sans vérification. |
| 16 | GIMM-VFI est sous « S-Lab License 1.0 », explicitement limitée à l'usage non-commercial (« please contact the contributor(s) » pour tout usage commercial). | [S36] | élevée (texte de licence lu) | **Éliminé** pour la production commerciale du studio. Utiliser RIFE ou FILM à la place. |
| 17 | InstantID : code Apache 2.0, mais dépend d'InsightFace `antelopev2`, dont la licence est réservée à la recherche non-commerciale d'après les mainteneurs eux-mêmes. | [S31] | élevée | InstantID (tel quel) n'est pas exploitable commercialement sans remplacer le détecteur de visage InsightFace par une alternative libre — à traiter comme un risque bloquant si retenu, sinon préférer PuLID (sans cette dépendance). |
| 18 | IP-Adapter (base) est Apache 2.0 ; la variante FaceID (basée aussi sur InsightFace) porte une licence non-commerciale séparée. | [S32] | moyenne | Utiliser IP-Adapter standard (image prompt) sans la variante FaceID pour rester en zone commerciale sûre. |
| 19 | musubi-tuner (kohya-ss) est Apache 2.0 et couvre l'entraînement LoRA pour Wan 2.1/2.2, HunyuanVideo, FramePack, FLUX Kontext/2, Qwen-Image, Z-Image. ai-toolkit (ostris) est MIT, mais tout entraînement sur base FLUX.1-dev hérite de la licence non-commerciale de cette base. | [S43][S44] | élevée | Utiliser musubi-tuner ou ai-toolkit sur bases Apache 2.0 (Wan 2.2, Qwen-Image, Z-Image) pour les LoRA de personnage, en évitant FLUX.1-dev comme base d'entraînement en pipeline commercial. |
| 20 | ComfyUI est sous GPL-3.0 ; la clause de « conveyance » de la GPLv3 précise que la simple interaction réseau sans transfert de copie n'est pas une distribution déclenchant l'obligation de partage du code source. | [S42] | élevée (texte de licence + clause citée) | Faire tourner ComfyUI comme service interne du studio (sans redistribuer le binaire/le code modifié à des tiers) n'oblige pas à republier le code ; en cas de distribution du worker packagé, republier les modifications sous GPLv3. |
| 21 | SageAttention (Apache 2.0) annonce un support explicite Ampere/Ada/Hopper, incluant nommément la RTX 4090 (Ada/sm_89), avec un gain de 2 à 5× sur l'attention vs FlashAttention selon le GPU. | [S45] | élevée (page officielle) | Compatible avec les 4× RTX 4070 Ti Super (même architecture Ada que la 4090) ; à activer dans le pipeline d'inférence. |
| 22 | La documentation PTX ISA de NVIDIA rattache les instructions FP4 natives (formats e2m1/e4m3 en mode `tcgen05`/`mxf4`) aux Tensor Cores de 5ᵉ génération, sans mention pour sm_89 (Ada) dans les sections consultées ; le FP8 est en revanche disponible dès les Tensor Cores de 4ᵉ génération d'Ada. | [S46] | moyenne (absence de mention ≠ preuve d'exclusion formelle, mais cohérent avec la doc architecture NVIDIA qui présente FP4 comme une nouveauté Blackwell) | Sur les 4070 Ti Super, utiliser FP8 (natif) et GGUF/quantification logicielle pour l'équivalent FP4 ; ne pas attendre d'accélération matérielle FP4 native. |
| 23 | Blender est en GPL (v2+ pour le code source, v3+ pour les binaires) ; la FAQ officielle précise que les rendus (images/vidéos) produits avec Blender restent l'entière propriété de l'utilisateur, usage commercial inclus. | [S51] | élevée (page officielle) | Aucune contrainte de licence sur les rendus Blender du studio (Cycles/EEVEE, scènes procédurales). |
| 24 | Poly Haven et ambientCG publient leurs assets (HDRI, textures, modèles) sous CC0 1.0 Universal, sans obligation d'attribution, usage commercial explicitement autorisé. | [S52][S53] | élevée (pages officielles) | Bibliothèque d'assets par défaut pour les scènes Blender procédurales du studio. |
| 25 | c2pa-python et c2patool (Content Authenticity Initiative / C2PA) sont publiés en double licence Apache-2.0/MIT. | [S47][S48] | élevée (dépôts officiels) | Utilisables sans restriction pour signer les manifestes C2PA des vidéos produites. |
| 26 | L'IPTC prévoit dans son vocabulaire `digitalSourceType` les valeurs `trainedAlgorithmicMedia` (média créé par un modèle d'IA entraîné) et `compositeSynthetic` (composite dont au moins un élément est de l'IA générative), ainsi que `compositeWithTrainedAlgorithmicMedia` pour les retouches génératives. | [S49] | élevée (registre officiel IPTC) | Mapper chaque type de plan du studio (100 % généré / composite Blender+IA/retouché) sur la valeur `digitalSourceType` correspondante avant export. |
| 27 | YouTube indique appliquer automatiquement un label IA lorsqu'une vidéo contient des métadonnées C2PA, en plus de sa détection interne ; ce label n'est pas modifiable par le créateur une fois posé automatiquement. | [S50] | élevée (page d'aide officielle) | Le marquage C2PA du studio doit être exact dès l'export (le studio ne pourra pas corriger après coup un label erroné déclenché par ses propres métadonnées). |
| 28 | Remotion est gratuit pour un usage individuel ou une entité à but lucratif de ≤3 employés ; au-delà, une « Company License » payante est requise (seuil par effectif, pas par revenu). | [S54] | élevée (texte de licence lu) | À surveiller si le studio embauche ; actuellement sous le seuil (opérateur solo). |
| 29 | Artificial Analysis Video Arena (leaderboard public) classe, parmi les modèles à poids ouverts, LTX-2/2.3/2.5 (Lightricks) et MiniMax H3 en tête des catégories Texte→Vidéo et Image→Vidéo avec audio ; Wan et HunyuanVideo n'apparaissent pas dans les extraits consultés du classement « open weights » à la date du contrôle. | [S55][S56] | moyenne (page dynamique, classement daté du jour de consultation, MiniMax H3 : statut « poids ouverts » à reconfirmer séparément) | Le classement qualité doit être revérifié en phase 3 avant le choix final ; ne pas se fier uniquement à ce classement pour Wan 2.2 qui reste la base la plus documentée et sans restriction. |
| 30 | lightx2v publie des LoRA/modèles de distillation par étapes pour Wan (StepDistill/CfgDistill), réduisant 40-50 pas à 4 pas sans CFG, avec un gain annoncé de l'ordre de 20-24× en nombre de pas ; un exemple communautaire cite une génération en ~35 s sur RTX 4090 (4 pas, LCM, cfg 1, shift 8) pour un clip Wan I2V. | [S57][S58] | moyenne (chiffres communautaires, non mesurés par nos soins) | LoRA de distillation à intégrer au pipeline de brouillon rapide ; temps exact à mesurer sur 4070 Ti Super via `make gpu-smoke`, « non mesuré » sur notre hardware pour l'instant. |
| 31 | Wan2.1/2.2 supporte le parallélisme multi-GPU via FSDP + xDiT USP (Ulysses + Ring Attention), invocable par `torchrun --nproc_per_node=N --ulysses_size N`, sans exigence de NVLink documentée (le papier xDiT recommande USP y compris sur liaisons moins rapides que le NVLink). | [S59][S60][S61] | moyenne (documentation du dépôt + papier académique, pas de mesure PCIe-only propre à la 4070 Ti Super) | Chemin multi-GPU par défaut pour Wan sur les 4× RTX 4070 Ti Super (PCIe, pas de NVLink) ; à valider par un banc réel avant la phase 3. |
| 32 | Aucune source consultée ne fournit de temps de génération ou de VRAM mesurés sur RTX 4070 Ti Super spécifiquement pour un modèle vidéo ou image quelconque ; les chiffres disponibles portent sur RTX 4090 (24 Go), H100/H800, ou sont des estimations communautaires. | [S24][S25][S57] | élevée (absence confirmée dans toutes les recherches menées) | Conformément à la règle « aucun chiffre inventé » : tout chiffre VRAM/secondes pour la 4070 Ti Super doit être noté « non mesuré » ici et produit par `make gpu-smoke` / `make bench-models` sur la machine réelle. |

## 1. Modèles vidéo à poids ouverts (inventaire détaillé)

| Modèle | Licence (fichier) | Territoire/seuil | Paramètres | Résolution/fps/durée natives | VRAM ≤16 Go ? | Temps mesuré (source tierce) | LoRA distillation | ComfyUI/diffusers | Multi-GPU |
|---|---|---|---|---|---|---|---|---|---|
| **Wan2.2 T2V-A14B** | Apache 2.0 [S2] | aucun | 14B×2 (MoE) | 480p/720p, 5 s | non natif (24 Go+ ; offload/GGUF requis, non mesuré sur 16 Go) | non mesuré | lightx2v StepDistill (4 pas) [S57] | diffusers + ComfyUI natif [S1] | xDiT/USP (torchrun) [S59] |
| **Wan2.2 I2V-A14B** | Apache 2.0 [S2] | aucun | 14B×2 (MoE) | 480p/720p, 5 s | non natif, non mesuré | non mesuré | lightx2v StepDistill [S58] (~35 s/clip sur RTX 4090, 4 pas, source communautaire) | diffusers + ComfyUI [S1] | xDiT/USP |
| **Wan2.2 TI2V-5B** | Apache 2.0 [S3] | aucun | 5B dense | 720p/24fps, 5 s | proche (24 Go cité comme minimum pour RTX 4090 [S24] ; quantification GGUF/FP8 nécessaire pour 16 Go, non mesuré) | « <9 min » pour un clip 5 s/720p sur RTX 4090, source praticien non officielle [S24] | oui (famille lightx2v Distill) [S58] | diffusers + ComfyUI [S1] | oui (moins critique, modèle dense) |
| **Wan2.2 S2V-14B** (son→vidéo) | Apache 2.0 [S1] | aucun | 14B | cinématique audio-pilotée, specs détaillées non mesurées | non mesuré | non mesuré | non identifié spécifiquement | diffusers + Space HF [S1] | xDiT/USP probable (même base Wan) |
| **Wan2.2 Animate-14B** | Apache 2.0 [S1] | aucun | 14B | animation/replacement de personnage | non mesuré | non mesuré | non identifié | HF + ComfyUI communautaire | xDiT/USP probable |
| **Wan 2.5 / 2.6 / 2.7 / 3.0** | **fermé** — pas de poids publiés | API Bailian uniquement | inconnu | inconnu | n/a | n/a | n/a | n/a | n/a |
| **LTX-2 (19B = 14B vidéo + 5B audio)** | « LTX-2.x Community License Agreement » [S7] | gratuit <10 M$ ARR, payant au-delà ; pas de restriction territoriale identifiée | 19B | annoncé « 4K natif, jusqu'à 50 fps, audio synchronisé », durée annoncée incohérente selon la source (10 s vs 20 s, non confirmée par la fiche officielle) [S5][S6] | non (19B, nécessite offload/quantification, non mesuré) | non mesuré | LoRA de fine-tuning documentées par Lightricks [S5] | diffusers + ComfyUI (dépôt officiel actif) [S6] | non documenté dans les sources consultées |
| **HunyuanVideo-1.5** | Tencent Hunyuan Community License — **exclut UE/UK/Corée du Sud** [S9] | 100 M MAU pour licence commerciale séparée | 8.3B | 480p/720p natif, upscale 1080p via SR, 24fps, 121 frames (~5 s) | **oui, 14 Go annoncés avec offload** [S10] | « 75 s sur une RTX 4090 » cité par un comparatif tiers, non officiel [S56] | non identifié | diffusers + ComfyUI | non documenté |
| **HunyuanVideo (I2V, 1.0)** | même licence Tencent Hunyuan, même exclusion territoriale [S9] | idem | 13B | 720p, ~5s | non natif sans offload | non mesuré | base de FramePack (voir constat 12) | diffusers + ComfyUI | non documenté |
| **SkyReels V2** | « Skywork Community License » (licence « other » HF, commercial autorisé après lecture des conditions ; seuil/territoire exact non confirmé, PDF non lu intégralement) [S26] | non vérifié (voir Questions ouvertes) | 1.3B à 14B, variante Diffusion Forcing (vidéo infinie) | 540p/720p | 1.3B tient probablement en 16 Go (non mesuré) ; 14B non | non mesuré | non identifié | diffusers + ComfyUI | non documenté |
| **SkyReels V3** | même famille de licence Skywork [S27] | idem, non vérifié | 14B (R2V, V2V) | non mesuré | non | non mesuré | non identifié | HF disponible | non documenté |
| **CogVideoX1.5-5B** | **« The CogVideoX License »**, pas Apache 2.0 : enregistrement commercial gratuit obligatoire, plafond 1 M visites/mois, droit chinois [S18] | enregistrement requis, plafond de trafic | 5B | 5-10 s, 720p+ | oui avec quantification INT8/offload (4-5 Go annoncés en config minimale, dégradée) [S18] | non mesuré sur notre config | LightX2V cite CogVideoX comme cible SageAttention (12 min vs 25 min sur H20, hors 4070) [S45] | diffusers + ComfyUI | non documenté |
| **Mochi 1 (Genmo)** | Apache 2.0 [S17] | aucun | 10B (AsymmDiT) | 480p, jusqu'à 84 frames/30fps en usage documenté | non natif (≥60 Go recommandé officiellement, 20-22 Go en config optimisée communautaire, au-delà de 16 Go) [S16][S17] | non mesuré | non identifié | ComfyUI communautaire | non documenté |
| **MAGI-1 (Sand.ai)** | Apache 2.0 [S15] | aucun | 24B (base) / 4.5B Distill+Quant | autoregressif par segments | 4.5B Distill+Quant : probable oui (non mesuré) ; 24B : non, multi-GPU requis | non mesuré | distillation intégrée (Distill+Quant officiel) | HF disponible | oui, multi-GPU nécessaire pour le 24B |
| **Kandinsky 5.0** | MIT (dépôt GitHub) / Apache 2.0 (fiches HF selon variantes) [S14] | aucun | 2B (T2V Lite) à plus grand | non mesuré précisément | 2B Lite : probable oui (non mesuré) | non mesuré | non identifié | GitHub + HF | non documenté |
| **LongCat-Video (Meituan)** | MIT [S12] | aucun | 13.6B (DiT) | non mesuré | non natif à 16 Go (13.6B, non mesuré) | non mesuré | non identifié | GitHub officiel | non documenté |
| **Step-Video-T2V (StepFun)** | MIT [S13] | aucun | 30B | jusqu'à 204 frames | non (30B) | non mesuré | non identifié | GitHub officiel | non documenté (taille suggère multi-GPU nécessaire) |
| **Open-Sora 2.0 (HPC-AI Tech)** | Apache 2.0 [S62] | aucun | 11B | comparable à HunyuanVideo/Step-Video en qualité annoncée | non mesuré, probablement proche du seuil 16 Go avec offload | non mesuré | checkpoints d'entraînement complets ouverts (reproductible pour ~200 k$) | GitHub + HF | non documenté |
| **FramePack (lllyasviel)** | Apache 2.0 (code) **mais base HunyuanVideo 13B exclue UE** [S13][S9] | **exclu UE via sa base** | 13B (base HunyuanVideo) | génération longue par « packing » de frames, VRAM gérée dynamiquement | conçu pour VRAM contrainte (annoncé jusqu'à laptop GPU) mais base non utilisable en France | non mesuré | non identifié | GitHub officiel, intégré diffusers | non |

## 2. Modèles image à poids ouverts

| Modèle | Licence (fichier) | Sorties commerciales ? | Paramètres | VRAM | Vitesse | Qualité |
|---|---|---|---|---|---|---|
| **FLUX.1 [schnell]** | Apache 2.0 [S19] | oui, sans réserve | 12B | tient en 16 Go avec FP8/GGUF (communauté, non mesuré ici) | très rapide (1-4 pas, modèle distillé) | référence qualité/vitesse open |
| **FLUX.1 [dev]** | FLUX.1 [dev] Non-Commercial License [S22] | sorties oui, **modèle non-commercial** (zone grise si le pipeline est lui-même générateur de revenu) | 12B | ~16 Go en FP8 (communauté) | plus lent que schnell (20-50 pas) | qualité supérieure à schnell |
| **FLUX.1 Kontext [dev]** | même famille non-commerciale [S22] | idem zone grise | 12B | non mesuré | non mesuré | édition d'image guidée par instruction |
| **FLUX.2 [klein] 4B** | Apache 2.0 [S28] | oui, sans réserve | 4B | tient largement en 16 Go | rapide (< 1 s visé sur datacenter GPU, non mesuré sur 4070 Ti Super) | bon compromis vitesse/qualité |
| **FLUX.2 [klein] 9B / [dev] 32B** | FLUX Non-Commercial (déploiement commercial payant) [S29] | sorties oui, modèle non-commercial pour déploiement | 9B/32B | 32B hors 16 Go sans offload lourd | non mesuré | flagship qualité (32B) |
| **Qwen-Image (20B)** | Apache 2.0 [S20] | oui | 20B (MMDiT) | FP8/GGUF dans 16 Go possible (communauté) ; BF16 complet nécessite ~80 Go | non mesuré sur 4070 Ti Super | rendu de texte fort |
| **Qwen-Image-Edit** | Apache 2.0, vérifié tag officiel [S21] | oui | 20B | idem Qwen-Image, GGUF/FP8 8-16 Go documentés communautairement | non mesuré | édition d'image basée instruction, cohérence d'identité |
| **HiDream-I1** | MIT [S66] | oui | 17B (Full) | Full >40 Go ; variante FP8 communautaire ~18 Go (légèrement > 16 Go) ; Dev/Fast plus légers | non mesuré | annoncé comme dépassant DALL-E 3/Midjourney par l'éditeur (à vérifier indépendamment) |
| **Stable Diffusion 3.5 (Large/Medium)** | Stability AI Community License, gratuit <1 M$ revenu annuel [S25] | oui sous le seuil | 8B (Large) / 2B (Medium) | Medium tient en 16 Go ; Large plus tendu (non mesuré) | non mesuré | référence historique, désormais dépassée par Z-Image/Qwen-Image sur les classements publics |
| **Z-Image / Z-Image Turbo (Tongyi-MAI/Alibaba)** | Apache 2.0 [S63] | oui, sans réserve | 6B | annoncé « tient sur GPU consommateur 16 Go » par l'éditeur/presse spécialisée [S63] | Turbo : <1 s sur GPU datacenter (annoncé), non mesuré sur 4070 Ti Super | **#1 classement Artificial Analysis Image Arena (poids ouverts)** au 08/12/2025, devant FLUX.2[dev], HunyuanImage 3.0, Qwen-Image [S63] |
| **HunyuanImage 2.1 / 3.0** | Tencent Hunyuan Community License — **exclut UE/UK/Corée du Sud**, daté 08/09/2025 pour 2.1 [S9][S10][S11] | non pour la France | 2.1 : non précisé ; 3.0 : natif multimodal large | n/a pour notre usage | n/a | **éliminé pour le studio (France)** |
| **Chroma (lodestones)** | Apache 2.0 (dérivé de FLUX.1-schnell) [S65] | oui | 8.9B | non mesuré, base proche de schnell | non mesuré | modèle communautaire non censuré, pas de filtrage éditorial — vérifier l'adéquation avec les garde-fous MISSION §12 avant usage |

## 3. Cohérence d'identité — LoRA de personnage, PuLID, InstantID, IP-Adapter, édition d'image

| Outil | Licence | Faisabilité 16 Go | Remarque |
|---|---|---|---|
| **musubi-tuner (kohya-ss)** | Apache 2.0 [S43] | conçu pour GPU contraint ; supporte Wan 2.1/2.2, HunyuanVideo, FramePack, FLUX Kontext/2, Qwen-Image, Z-Image | Outil d'entraînement LoRA recommandé, base légale propre si entraîné sur Wan 2.2/Qwen-Image/Z-Image |
| **ai-toolkit (ostris)** | MIT [S44] | LowVRAM mode pour 16 Go, 8 Go minimum documenté | Entraînement actuel majoritairement testé sur FLUX.1-dev → **hérite alors de la licence non-commerciale de FLUX.1-dev** ; entraîner plutôt sur une base Apache 2.0 pour un LoRA de personnage exploitable commercialement |
| **PuLID** | Apache 2.0 [S30] | variante PuLID-FLUX tourne sur 16 Go d'après le dépôt officiel | Pas de dépendance InsightFace non-commerciale identifiée dans les sources consultées — candidat le plus sûr pour la cohérence de personnage |
| **InstantID** | Code Apache 2.0, **mais dépendance InsightFace antelopev2 en licence recherche non-commerciale** [S31] | non mesuré | **Risque licence** : à éviter en pipeline commercial tant que le détecteur de visage n'est pas remplacé |
| **IP-Adapter (standard)** | Apache 2.0 [S32] | léger, tient en 16 Go | Variante FaceID (InsightFace) exclue pour la même raison qu'InstantID |
| **Qwen-Image-Edit / FLUX.1 Kontext [dev]** | Apache 2.0 / non-commercial (cf. tableau §2) | GGUF/FP8 dans 16 Go pour Qwen-Image-Edit | Qwen-Image-Edit = chemin d'édition d'image sans ambiguïté de licence ; Kontext[dev] porte la même zone grise que FLUX.1-dev |

## 4. Upscaling vidéo, interpolation, lip-sync/avatar

| Outil | Fonction | Licence | VRAM | Vitesse | Remarque |
|---|---|---|---|---|---|
| **SeedVR2 (ByteDance-Seed)** | Upscaling vidéo par diffusion | Apache 2.0 [S33] | 8-16 Go documentés (GGUF Q4_K_M + BlockSwap + tiling) | non mesuré | Candidat par défaut |
| **FlashVSR (OpenImagingLab, CVPR 2026)** | Upscaling vidéo temps réel (1 pas, attention parcimonieuse) | Apache [S34] | non mesuré | visée « temps réel » par les auteurs | Second candidat, plus récent |
| **Real-ESRGAN** | Upscaling image/vidéo classique (GAN) | BSD-3-Clause, vérifié texte [S35] | léger, tient largement en 16 Go | rapide (non-diffusion) | Fallback robuste, qualité inférieure aux modèles de diffusion récents |
| **RIFE (Practical-RIFE)** | Interpolation de frames | MIT [S36], réserve sur le dataset d'entraînement | très léger | temps réel documenté par la communauté | Candidat interpolateur par défaut |
| **GIMM-VFI** | Interpolation de frames continue | **S-Lab License 1.0 — non-commercial**, vérifié texte [S37] | non mesuré | non mesuré | **Éliminé** pour usage commercial |
| **FILM (Google Research)** | Interpolation « Frame Interpolation for Large Motion » | non vérifié dans cette note (à contrôler avant usage) | — | — | **Non vérifié — question ouverte** |
| **LatentSync (ByteDance)** | Lip-sync latent diffusion | Apache 2.0, vérifié texte [S38] | non mesuré | non mesuré | Candidat lip-sync par défaut |
| **MuseTalk (TMElyralab)** | Lip-sync temps réel | MIT, vérifié texte [S39] | léger, 30fps+ annoncé sur V100 par l'éditeur | non mesuré sur 4070 Ti Super | Candidat pour avatars parlants légers |
| **InfiniteTalk (MeiGen-AI)** | Talking video longueur illimitée, basé Wan2.1 | Apache 2.0, vérifié tag HF [S40] | hérite des contraintes Wan (14 Go+) | non mesuré | Bonne intégration avec la base Wan du studio |
| **Wan2.2-S2V-14B** | Son→vidéo cinématique natif | Apache 2.0 [S1] | non mesuré | non mesuré | Alternative native à un pipeline lip-sync séparé |
| **EchoMimic v3 (Ant Group)** | Animation humaine multi-tâches, 1.3B | Apache 2.0, vérifié tag HF [S41] | léger (1.3B) — bon candidat 16 Go | non mesuré | Le plus petit des modèles lip-sync/avatar recensés |
| **Topaz Video AI et équivalents propriétaires** | Upscaling/interpolation commercial | **Poids fermés, logiciel propriétaire** | n/a | n/a | **Hors règle du studio** (§5 MISSION : aucune API/service externe, poids non ouverts) — à exclure explicitement de toute liste d'outils |

## 5. Outillage

| Outil | Licence | Implication |
|---|---|---|
| **ComfyUI** | GPL-3.0, vérifié texte [S42] | Exécution en service interne (sans distribution) : pas d'obligation de publication du code, d'après la clause de « conveyance » de la GPLv3. Publication/distribution d'une image Docker à des tiers → republier les modifications. |
| **diffusers (Hugging Face)** | Apache 2.0 (notoire, non re-vérifié dans cette session — confiance moyenne) | Bibliothèque d'inférence de référence pour la majorité des modèles listés ; mode headless natif (scripts Python), pas de risque de licence pour un usage interne. |
| **SageAttention** | Apache 2.0 [S45] | Supporte explicitement Ada/sm_89 (RTX 40 series nommée) ; gain 2-5× sur l'attention vs FlashAttention selon GPU testé (RTX4090, H100, H20, A100, RTX3090, RTX5090 cités ; **4070 Ti Super non mesurée directement**). |
| **TeaCache** | non vérifié dans cette session (budget de recherche épuisé) | **Question ouverte** — à vérifier avant intégration : cache de timesteps pour accélérer l'inférence diffusion, compatible a priori Wan/HunyuanVideo/FLUX d'après la littérature générale, non confirmé ici par une source ouverte. |
| **torch.compile** | PyTorch (BSD), notoire | Accélère l'inférence par compilation de graphe ; combinable avec FP8 sur Ada. Non re-vérifié spécifiquement dans cette session. |
| **FP8 sur Ada (sm_89)** | — | Supporté nativement (4ᵉ génération Tensor Cores) [S45][S46]. |
| **FP4 sur Ada (sm_89)** | — | **Non supporté nativement** d'après la documentation PTX ISA consultée, qui rattache FP4 (tcgen05/mxf4) aux Tensor Cores de 5ᵉ génération (Blackwell) [S46] ; confiance moyenne (absence de mention plutôt qu'exclusion explicite formelle). Sur 4070 Ti Super, viser FP8 natif + quantification logicielle (GGUF Q4/Q8) plutôt que du FP4 matériel. |

## 6. Rendu procédural

| Outil | Licence | Statut des rendus | Notes |
|---|---|---|---|
| **Blender** | GPL v2+ (code), v3+ (binaires) [S51] | Rendus = propriété exclusive de l'utilisateur, usage commercial explicitement autorisé par la FAQ officielle | Aucune contrainte pour le studio |
| **Cycles (OptiX sur RTX)** | inclus dans Blender (GPL) | idem | Accélération matérielle RT/OptiX disponible sur les 4× RTX 4070 Ti Super |
| **EEVEE** | inclus dans Blender (GPL) | idem | Rendu temps réel, alternative rapide à Cycles pour les brouillons |
| **Poly Haven** | CC0 1.0 Universal [S52] | Domaine public de fait, usage commercial libre, pas d'attribution requise | HDRI, textures, modèles 3D |
| **ambientCG** | CC0 1.0 Universal, vérifié texte [S53] | idem | Matériaux/textures complémentaires |
| **three.js** | MIT, vérifié texte [S64] | Librement réutilisable, y compris commercialement | Pour la 2,5D / caméra virtuelle si le studio explore une piste web/WebGL |
| **Remotion** | Licence propriétaire à seuil d'effectif : gratuit ≤3 employés (for-profit), payant au-delà [S54] | Rendus autorisés commercialement sous le seuil | Seuil par **effectif**, pas par revenu — distinct de FLUX/SD3.5 ; à resurveiller si le studio embauche |

## 7. Marquage C2PA / IPTC

| Élément | Détail | Source |
|---|---|---|
| **c2pa-python** | Bindings Python pour c2pa-rs, lecture/écriture/signature de manifestes C2PA, double licence Apache-2.0/MIT | [S47] |
| **c2patool** | CLI équivalente, double licence Apache-2.0/MIT | [S48] |
| **IPTC digitalSourceType** | Vocabulaire contrôlé incluant `trainedAlgorithmicMedia` (média produit par un modèle d'IA entraîné), `compositeSynthetic` (composite avec au moins un élément d'IA générative), `compositeWithTrainedAlgorithmicMedia` (retouche générative), `algorithmicMedia`, `digitalCapture`, `humanEdits`, etc. | [S49] |
| **Lecture YouTube** | YouTube applique un label IA automatique quand des métadonnées C2PA sont détectées (en plus de la détection interne) ; label non ajustable par le créateur dans ce cas | [S50] |
| **Lecture TikTok** | Non re-vérifié dans cette session (budget de recherche épuisé) — la mission mentionne une détection C2PA automatique avec label non retirable ; **à confirmer par une source officielle TikTok en phase 0 complémentaire ou phase 5** | Question ouverte |

## Écarts avec MISSION §4

| Affirmation de la mission | Verdict | Sources | Correction proposée |
|---|---|---|---|
| « Candidats à poids ouverts en septembre 2026 : Wan 2.2 / 2.7 (Apache 2.0) » | **infirmé pour 2.7** | [S1][S4] | Remplacer par « Wan 2.2 (Apache 2.0) ; Wan 2.5/2.6/2.7/3.0 sont fermés (API Bailian uniquement) au 28/09/2026 ». Revérifier périodiquement si Alibaba republie des poids ≥2.5. |
| « LTX-2.x (audio natif, licence à vérifier) » | **confirmé et précisé** | [S6][S7] | LTX-2/2.x a bien un audio natif synchronisé (19B = 14B vidéo + 5B audio). Licence = « LTX-2.x Community License Agreement », gratuite jusqu'à 10 M$ ARR, payante au-delà, sans restriction territoriale identifiée. Pas Apache 2.0. |
| « HunyuanVideo 1.5 (licence historiquement exclue de l'UE → à vérifier avant tout usage) » | **confirmé** | [S9][S10] | L'exclusion UE/UK/Corée du Sud persiste sur HunyuanVideo-1.5 (et s'étend à HunyuanImage 2.1/3.0). **Éliminer HunyuanVideo/HunyuanImage et leurs dérivés directs (dont FramePack tel quel) du studio.** |
| « Le local reste en dessous de Kling / Veo en photoréalisme constant et prend 4 à 15 min par clip » | **non vérifiable précisément sur notre hardware** | [S24][S58] | Les seuls temps mesurés trouvés (RTX 4090, sources praticiennes) donnent ~9 min pour Wan2.2 TI2V-5B (5 s/720p) et ~35 s avec LoRA de distillation 4 pas (I2V) — cohérent avec la fourchette de la mission pour le mode « qualité », mais largement en dessous avec distillation. **Aucun chiffre mesuré sur RTX 4070 Ti Super** : à confirmer par `make gpu-smoke`/`make bench-models`, ne pas figer la fourchette 4-15 min comme acquise. |
| Implicite : modèles listés comme candidats directs sans réserve de licence | **nuancé** | [S18][S22][S23][S29][S37] | Plusieurs candidats évidents portent des restrictions non triviales : CogVideoX1.5 (licence propriétaire à enregistrement), FLUX.1-dev/Kontext-dev/FLUX.2-dev (modèle non-commercial, sorties commerciales OK), GIMM-VFI (non-commercial strict), InstantID/IP-Adapter-FaceID (dépendance InsightFace non-commerciale). Le routeur multi-modèles doit encoder ces restrictions par modèle, pas seulement « licence commerciale oui/non » binaire. |

## Questions ouvertes

- Seuil exact et éventuelle restriction territoriale du « Skywork Community License » (SkyReels V2/V3) : le PDF officiel n'a pas pu être lu intégralement par les outils de cette session ; à relire directement (télécharger et parser le PDF) avant d'intégrer SkyReels à la production.
- TeaCache : compatibilité et gains exacts avec Wan 2.2 / HunyuanVideo / FLUX non vérifiés dans cette session (budget de recherche épuisé) — à rechercher avant intégration au pipeline d'accélération.
- FILM (Google Research, interpolation de frames) : licence non vérifiée dans cette session — à contrôler avant tout usage commercial.
- Lecture C2PA par TikTok (label automatique non retirable) : affirmation de la mission non re-vérifiée par une source officielle TikTok dans cette session ; seule la page YouTube a été confirmée directement.
- Aucun chiffre de VRAM ni de temps de génération n'a pu être mesuré sur la machine réelle (4× RTX 4070 Ti Super, PCIe sans NVLink) : tous les chiffres cités dans cette note proviennent de RTX 4090/H100/H20/A100 ou de communautés tierces. **Le premier `make gpu-smoke` doit produire ces mesures avant toute décision d'architecture définitive.**
- Statut « poids ouverts » exact de MiniMax H3 (cité en tête du classement Artificial Analysis) non confirmé par une fiche de licence officielle dans cette session — à vérifier avant de l'ajouter à la shortlist, malgré son bon classement.
- Diffusers (licence, versions supportées par modèle) et torch.compile n'ont pas été re-vérifiés spécifiquement dans cette session (faits notoires mais non re-sourcés ici avec la même rigueur que le reste) ; TeaCache non trouvé du tout.

## 8. Recommandation — shortlist `make bench-models`

**Shortlist minimale proposée (respecte ≥2 vidéo, ≥1 image, 1 upscaler, 1 interpolateur) :**

1. **Wan2.2 TI2V-5B** (vidéo, T2V+I2V unifié, Apache 2.0, sans restriction) — base de référence, seul modèle dense proche de 16 Go.
2. **Wan2.2 I2V-A14B + LoRA de distillation lightx2v** (vidéo, Apache 2.0) — chemin qualité supérieure avec multi-GPU (xDiT/USP) ou offload, et chemin brouillon rapide via distillation.
3. **LTX-2 (fast/base)** (vidéo avec audio natif, licence à seuil 10 M$ ARR — compatible tant que le studio reste petit) — seul candidat avec son natif synchronisé, à comparer en qualité/vitesse face à Wan.
4. **Z-Image Turbo** (image, Apache 2.0, #1 classement Artificial Analysis Image Arena poids ouverts) — chemin image principal.
5. **Qwen-Image-Edit** (image, Apache 2.0) — édition/cohérence d'identité sans ambiguïté de licence.
6. **SeedVR2** (upscaler, Apache 2.0, tient en 16 Go via GGUF).
7. **RIFE (Practical-RIFE)** (interpolateur, MIT, très léger).

**Modèles écartés de la shortlist (et pourquoi) :**
- **HunyuanVideo-1.5 / HunyuanImage 2.1-3.0 / FramePack (base HunyuanVideo)** : licence excluant l'UE — non exploitables légalement en France [S9][S10][S11].
- **FLUX.1 [dev] / Kontext [dev] / FLUX.2 [dev] 32B** : licence non-commerciale sur le modèle, zone grise pour un pipeline générateur de revenu — réservés aux tests, pas au chemin de production par défaut [S22][S23][S29].
- **CogVideoX1.5** : licence propriétaire à enregistrement + plafond de trafic — utilisable seulement après démarche administrative documentée dans NEEDS_HUMAN ; pas retenu par défaut [S18].
- **GIMM-VFI** : licence S-Lab explicitement non-commerciale — exclu, RIFE couvre le même besoin [S37].
- **InstantID / IP-Adapter-FaceID** : dépendance InsightFace non-commerciale — exclus au profit de PuLID [S31][S32].
- **Wan 2.5/2.6/2.7/3.0, Mochi 1 (VRAM), Step-Video-T2V (30B), MAGI-1 24B** : indisponibles en poids ouverts, ou hors budget 16 Go sans multi-GPU non encore validé.
- **Topaz et upscalers/interpolateurs propriétaires** : poids fermés, hors règle du studio par construction (MISSION §5).

### Matrice famille de plan → technique recommandée

| Famille de plan (MISSION §6) | Technique recommandée | Justification |
|---|---|---|
| Reconstitution historique, échelle impossible, science visualisée sans humain en gros plan | **Blender procédural (Cycles/EEVEE) + assets CC0 Poly Haven/ambientCG** | Aucune contrainte de licence, qualité photoréaliste contrôlable, coût GPU prévisible [S51][S52][S53] |
| Plan avec mouvement vivant indispensable (personnage, action) | **Wan2.2 I2V-A14B ou TI2V-5B**, brouillon via LoRA lightx2v puis final sans distillation | Seul chemin vidéo pleinement ouvert et documenté, multi-GPU disponible via xDiT/USP [S1][S57][S59] |
| Plan avec son/musique synchronisée à l'image (ambiance, dialogue court) | **LTX-2** (audio natif) ou Wan2.2-S2V-14B | Évite un pipeline TTS+vidéo séparé pour les plans où le son doit coller au mouvement [S6][S1] |
| Image fixe animée en 2,5D (parallaxe, caméra virtuelle) | **Z-Image Turbo ou Qwen-Image** (image) + **Remotion/three.js** (mouvement de caméra) | Coût GPU minimal, licence propre sous le seuil d'effectif Remotion [S63][S54][S64] |
| Visage humain en gros plan (à éviter par défaut, MISSION §6) | Si indispensable : **PuLID** (cohérence) + **LatentSync/EchoMimic v3** (lip-sync) sur base Wan2.2, jamais InstantID/FaceID | Seuls outils de cohérence faciale sans dépendance non-commerciale identifiée [S30][S38][S41] |
| Upscale final avant export | **SeedVR2** (ou FlashVSR en comparaison) | Apache 2.0, tient en 16 Go via GGUF [S33][S34] |
| Fluidification / conversion de cadence | **RIFE** | MIT, très léger, temps réel documenté [S36] |
| Marquage de divulgation à l'export | **c2pa-python/c2patool** + `digitalSourceType` adapté (`trainedAlgorithmicMedia` pour un plan 100 % généré, `compositeSynthetic` pour un composite Blender+IA) | Double licence Apache/MIT, vocabulaire IPTC officiel couvrant exactement nos cas [S47][S48][S49] |

## Sources

| ID | Titre | URL | Date source | Consulté | Type | Confiance |
|---|---|---|---|---|---|---|
| S1 | Wan2.2 — dépôt officiel (README, S2V, Animate) | https://github.com/Wan-Video/Wan2.2 | 2025-07-28 | 2026-09-28 | officiel | élevée |
| S2 | Wan2.2 — LICENSE.txt (Apache 2.0) | https://github.com/Wan-Video/Wan2.2/blob/main/LICENSE.txt | 2025-07-28 | 2026-09-28 | officiel | élevée |
| S3 | Wan-AI/Wan2.2-TI2V-5B — fiche modèle HuggingFace | https://huggingface.co/Wan-AI/Wan2.2-TI2V-5B | 2025-07-28 | 2026-09-28 | officiel | élevée |
| S4 | Is Wan 2.7 Open Source? — analyse licence Wan 2.5/2.6/2.7/3.0 | https://wan27.org/blog/wan-2-7-open-source-guide | 2026-08 | 2026-09-28 | praticien | moyenne |
| S5 | LTX-2 — communiqué GlobeNewswire (Lightricks) | https://www.globenewswire.com/news-release/2026/01/06/3213304/0/en/Lightricks-Open-Sources-LTX-2-the-First-Production-Ready-Audio-and-Video-Generation-Model-With-Truly-Open-Weights.html | 2026-01-06 | 2026-09-28 | presse | moyenne |
| S6 | Lightricks/LTX-2 — dépôt officiel GitHub | https://github.com/Lightricks/LTX-2 | 2026-01 | 2026-09-28 | officiel | élevée |
| S7 | LTX-2 — LICENSE-2_x (LTX-2.x Community License Agreement) | https://github.com/Lightricks/LTX-2/blob/main/LICENSE-2_x | 2026-08-11 | 2026-09-28 | officiel | élevée |
| S8 | Lightricks/LTX-2 — fiche modèle HuggingFace | https://huggingface.co/Lightricks/LTX-2 | 2026-01 | 2026-09-28 | officiel | élevée |
| S9 | HunyuanVideo-1.5 — LICENSE (Tencent Hunyuan Community License) | https://github.com/Tencent-Hunyuan/HunyuanVideo-1.5/blob/main/LICENSE | 2025-11 | 2026-09-28 | officiel | élevée |
| S10 | tencent/HunyuanVideo-1.5 — fiche modèle HuggingFace | https://huggingface.co/tencent/HunyuanVideo-1.5 | 2025-11 | 2026-09-28 | officiel | élevée |
| S11 | HunyuanImage-2.1 — LICENSE (texte intégral, date de release 08/09/2025) | https://raw.githubusercontent.com/Tencent-Hunyuan/HunyuanImage-2.1/main/LICENSE | 2025-09-08 | 2026-09-28 | officiel | élevée |
| S12 | LongCat-Video — LICENSE (MIT) | https://raw.githubusercontent.com/meituan-longcat/LongCat-Video/main/LICENSE | 2025 | 2026-09-28 | officiel | élevée |
| S13 | Step-Video-T2V — LICENSE (MIT) | https://raw.githubusercontent.com/stepfun-ai/Step-Video-T2V/main/LICENSE | 2025-02-17 | 2026-09-28 | officiel | élevée |
| S62 | Open-Sora — LICENSE (Apache 2.0) | https://raw.githubusercontent.com/hpcaitech/Open-Sora/main/LICENSE | 2025-03-12 | 2026-09-28 | officiel | élevée |
| S14 | kandinskylab/kandinsky-5 — LICENSE (MIT) | https://raw.githubusercontent.com/kandinskylab/kandinsky-5/main/LICENSE | 2025-09-29 | 2026-09-28 | officiel | élevée |
| S15 | sand-ai/MAGI-1 — fiche modèle HuggingFace (apache-2.0, YAML frontmatter) | https://huggingface.co/sand-ai/MAGI-1/raw/main/README.md | 2025-05 | 2026-09-28 | officiel | élevée |
| S16 | genmo/mochi-1-preview — fiche modèle HuggingFace | https://huggingface.co/genmo/mochi-1-preview | 2024-10 | 2026-09-28 | officiel | élevée |
| S17 | genmoai/mochi — README GitHub (licence Apache 2.0) | https://raw.githubusercontent.com/genmoai/mochi/main/README.md | 2024-10 | 2026-09-28 | officiel | élevée |
| S18 | zai-org/CogVideoX1.5-5B — LICENSE (« The CogVideoX License », texte intégral) | https://huggingface.co/zai-org/CogVideoX1.5-5B/raw/main/LICENSE | 2024-11 | 2026-09-28 | officiel | élevée |
| S19 | black-forest-labs/flux — LICENSE-FLUX1-schnell (Apache 2.0) | https://github.com/black-forest-labs/flux/blob/main/model_licenses/LICENSE-FLUX1-schnell | 2024-08 | 2026-09-28 | officiel | élevée |
| S20 | QwenLM/Qwen-Image — LICENSE (Apache 2.0) | https://github.com/QwenLM/Qwen-Image/blob/main/LICENSE | 2025-08 | 2026-09-28 | officiel | élevée |
| S63 | Tongyi-MAI/Z-Image — dépôt GitHub + classement Artificial Analysis | https://github.com/Tongyi-MAI/Z-Image | 2026-01-27 | 2026-09-28 | officiel | élevée |
| S21 | Qwen/Qwen-Image-Edit — licence vérifiée via API HuggingFace (apache-2.0) | https://huggingface.co/Qwen/Qwen-Image-Edit | 2025-08 | 2026-09-28 | officiel | élevée |
| S22 | black-forest-labs/flux — LICENSE-FLUX1-dev (texte intégral, clause Output §2d) | https://github.com/black-forest-labs/flux/blob/main/model_licenses/LICENSE-FLUX1-dev | 2024-08 | 2026-09-28 | officiel | élevée |
| S23 | black-forest-labs/FLUX.1-Kontext-dev — fiche modèle HuggingFace | https://huggingface.co/black-forest-labs/FLUX.1-Kontext-dev | 2025-06 | 2026-09-28 | officiel | élevée |
| S24 | Wan 2.1/2.2 VRAM Requirements — comparatif praticien (temps RTX 4090) | https://willitrunai.com/blog/wan-2-2-vram-requirements | 2026 | 2026-09-28 | praticien | moyenne |
| S25 | stabilityai/stable-diffusion-3.5-large — LICENSE.md (seuil 1 M$ revenu, texte cité) | https://huggingface.co/stabilityai/stable-diffusion-3.5-large/blob/main/LICENSE.md | 2024-10 | 2026-09-28 | officiel | élevée |
| S26 | Skywork/SkyReels-V2-T2V-14B-540P — LICENSE (fiche « other », Skywork Community License) | https://huggingface.co/Skywork/SkyReels-V2-T2V-14B-540P/raw/main/LICENSE | 2025-04-21 | 2026-09-28 | officiel | moyenne |
| S27 | Skywork/SkyReels-V3-R2V-14B — fiche modèle HuggingFace (licence « other ») | https://huggingface.co/Skywork/SkyReels-V3-R2V-14B | 2026-01-29 | 2026-09-28 | officiel | moyenne |
| S28 | FLUX.2 [klein] — annonce officielle Black Forest Labs | https://bfl.ai/blog/flux2-klein-towards-interactive-visual-intelligence | 2026-01-15 | 2026-09-28 | officiel | élevée |
| S29 | Black Forest Labs — page de licensing (klein 4B Apache 2.0, klein 9B/dev 32B non-commercial) | https://bfl.ai/licensing | 2026 | 2026-09-28 | officiel | moyenne |
| S65 | lodestones/Chroma — README HuggingFace (Apache 2.0, dérivé FLUX.1-schnell) | https://huggingface.co/lodestones/Chroma/blob/main/README.md | 2025 | 2026-09-28 | officiel | moyenne |
| S30 | ToTheBeginning/PuLID — LICENSE (Apache 2.0) | https://github.com/ToTheBeginning/PuLID/blob/main/LICENSE | 2024-04 | 2026-09-28 | officiel | élevée |
| S66 | HiDream-ai/HiDream-I1 — dépôt GitHub (licence MIT) | https://github.com/HiDream-ai/HiDream-I1 | 2025-04-07 | 2026-09-28 | officiel | moyenne |
| S31 | instantX-research/InstantID — discussion HuggingFace sur la dépendance InsightFace non-commerciale | https://huggingface.co/InstantX/InstantID/discussions/2 | 2024 | 2026-09-28 | officiel | élevée |
| S32 | tencent-ailab/IP-Adapter — LICENSE (Apache 2.0) + issue sur FaceID | https://github.com/tencent-ailab/IP-Adapter/blob/main/LICENSE | 2023-09 | 2026-09-28 | officiel | élevée |
| S33 | ByteDance-Seed/SeedVR — dépôt officiel GitHub (SeedVR2, Apache 2.0) | https://github.com/ByteDance-Seed/SeedVR | 2025 | 2026-09-28 | officiel | moyenne |
| S34 | FlashVSR — dépôt GitHub (CVPR 2026, licence Apache) | https://github.com/azhai219/FlashVSR | 2025-10 | 2026-09-28 | officiel | moyenne |
| S35 | xinntao/Real-ESRGAN — LICENSE (BSD 3-Clause, texte cité) | https://github.com/xinntao/Real-ESRGAN/blob/master/LICENSE | 2021 | 2026-09-28 | officiel | élevée |
| S36 | hzwer/Practical-RIFE — licence MIT et réserve sur le dataset | https://github.com/hzwer/Practical-RIFE | 2022 | 2026-09-28 | officiel | moyenne |
| S37 | GSeanCDAT/GIMM-VFI — LICENSE (S-Lab License 1.0, non-commercial, texte cité) | https://github.com/GSeanCDAT/GIMM-VFI/blob/main/LICENSE | 2024-11-18 | 2026-09-28 | officiel | élevée |
| S38 | bytedance/LatentSync — LICENSE (Apache 2.0, texte cité) | https://raw.githubusercontent.com/bytedance/LatentSync/main/LICENSE | 2024-12 | 2026-09-28 | officiel | élevée |
| S39 | TMElyralab/MuseTalk — LICENSE (MIT, texte cité) | https://raw.githubusercontent.com/TMElyralab/MuseTalk/main/LICENSE | 2024 | 2026-09-28 | officiel | élevée |
| S40 | MeiGen-AI/InfiniteTalk — licence vérifiée via API HuggingFace (apache-2.0) | https://huggingface.co/MeiGen-AI/InfiniteTalk | 2025-08-20 | 2026-09-28 | officiel | élevée |
| S41 | antgroup/echomimic_v3 — licence vérifiée via API HuggingFace (apache-2.0) | https://huggingface.co/BadToBest/EchoMimicV3 | 2026 | 2026-09-28 | officiel | élevée |
| S42 | comfyanonymous/ComfyUI — LICENSE (GPL-3.0, clause « conveyance » citée) | https://github.com/comfyanonymous/ComfyUI/blob/master/LICENSE | s.d. | 2026-09-28 | officiel | élevée |
| S43 | kohya-ss/musubi-tuner — dépôt GitHub (Apache 2.0) | https://github.com/kohya-ss/musubi-tuner | 2026 | 2026-09-28 | officiel | élevée |
| S44 | ostris/ai-toolkit — dépôt GitHub (MIT, réserve FLUX.1-dev) | https://github.com/ostris/ai-toolkit | 2026 | 2026-09-28 | officiel | moyenne |
| S45 | thu-ml/SageAttention — dépôt GitHub (support Ada/sm_89, licence Apache 2.0, gains 2-5×) | https://github.com/thu-ml/SageAttention | 2026 | 2026-09-28 | officiel | élevée |
| S46 | NVIDIA PTX ISA 9.4 — documentation officielle (FP4 tcgen05/mxf4 = 5ᵉ gén. Tensor Cores) | https://docs.nvidia.com/cuda/parallel-thread-execution/index.html | 2026 | 2026-09-28 | officiel | moyenne |
| S47 | contentauth/c2pa-python — dépôt GitHub (double licence Apache-2.0/MIT) | https://github.com/contentauth/c2pa-python | 2026 | 2026-09-28 | officiel | élevée |
| S48 | contentauth/c2patool — dépôt GitHub (double licence Apache-2.0/MIT) | https://github.com/contentauth/c2patool | 2026 | 2026-09-28 | officiel | élevée |
| S49 | IPTC — registre officiel digitalSourceType (cv.iptc.org) | https://cv.iptc.org/newscodes/digitalsourcetype/ | 2026 | 2026-09-28 | officiel | élevée |
| S50 | YouTube Aide — divulgation de contenu IA réaliste, détection C2PA | https://support.google.com/youtube/answer/14328491 | 2026 | 2026-09-28 | officiel | élevée |
| S51 | Blender.org — page officielle de licence (GPL, statut des rendus) | https://www.blender.org/about/license/ | s.d. | 2026-09-28 | officiel | élevée |
| S52 | Poly Haven — page de licence (CC0) | https://polyhaven.com/license | s.d. | 2026-09-28 | officiel | élevée |
| S53 | ambientCG — page de licence (CC0, texte cité) | https://docs.ambientcg.com/license | s.d. | 2026-09-28 | officiel | élevée |
| S54 | Remotion — LICENSE.md (seuil de 3 employés) | https://github.com/remotion-dev/remotion/blob/main/LICENSE.md | 2026 | 2026-09-28 | officiel | élevée |
| S55 | Artificial Analysis — Leaderboard Text-to-Video (poids ouverts) | https://artificialanalysis.ai/video/leaderboard/text-to-video | 2026-09 | 2026-09-28 | données | moyenne |
| S56 | Artificial Analysis — Leaderboard Image-to-Video (poids ouverts) | https://artificialanalysis.ai/video/leaderboard/image-to-video | 2026-09 | 2026-09-28 | données | moyenne |
| S57 | lightx2v — documentation « Step Distillation » (readthedocs) | https://lightx2v-en.readthedocs.io/en/latest/method_tutorials/step_distill.html | 2026 | 2026-09-28 | officiel | moyenne |
| S58 | lightx2v/Wan2.2-Distill-Models — fiche HuggingFace (gain de vitesse communautaire ~35s/clip RTX4090) | https://huggingface.co/lightx2v/Wan2.2-Distill-Models | 2026 | 2026-09-28 | officiel | moyenne |
| S59 | Wan-AI/Wan2.1-T2V-14B — fiche modèle HuggingFace (commande xDiT USP/torchrun) | https://huggingface.co/Wan-AI/Wan2.1-T2V-14B | 2025-02 | 2026-09-28 | officiel | moyenne |
| S60 | xDiT — article académique (arXiv 2411.01738), moteur d'inférence parallèle pour DiT | https://arxiv.org/pdf/2411.01738 | 2024-11 | 2026-09-28 | publication | moyenne |
| S61 | Wan-Video/Wan2.1 — dépôt officiel GitHub (FSDP + xDiT USP) | https://github.com/Wan-Video/Wan2.1 | 2025-02 | 2026-09-28 | officiel | moyenne |
| S64 | mrdoob/three.js — LICENSE (MIT, texte cité) | https://github.com/mrdoob/three.js/blob/dev/LICENSE | 2026 | 2026-09-28 | officiel | élevée |
