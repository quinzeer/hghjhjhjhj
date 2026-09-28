# Audio — TTS, musique, effets sonores, transcription, loudness (état septembre 2026)

> Consulté le : 2026-09-28 · Auteur : researcher · Version : 1 · Portée : modèles à poids ouverts et méthodes procédurales pour la voix (narrateur Qwen3-TTS + Kokoro), la musique, les effets sonores/foley, la transcription de contrôle (WER) et le mastering loudness, exécutables sur 4× RTX 4070 Ti Super 16 Go (CUDA, Ada sm_89), opérateur en France (UE), usage commercial, aucun service externe de génération.

## Synthèse

Qwen3-TTS (Apache-2.0, sorti 2026-01-22, 0.6B/1.7B, 10 langues dont le français, clonage 3 s + design vocal, vLLM jour-0) est déjà nativement un modèle PyTorch/Transformers CUDA [S1][S2][S3] : le « portage CUDA » de la mission n'est pas un portage logiciel mais une reproduction du timbre + un benchmark VRAM/vitesse, non mesurés à ce jour. Kokoro-82M (Apache-2.0) reste un bon secours léger mais n'a qu'une seule voix française [S4][S5]. La majorité des alternatives TTS séduisantes ont des poids non commerciaux (F5-TTS, XTTS-v2/CPML, Fish-Speech/OpenAudio, Spark-TTS, MaskGCT — toutes CC-BY-NC[-SA]) [S17][S19][S20][S26][S27] ou une licence restrictive/territoriale (IndexTTS2 : licence bilibili non standard et pas de français ; Higgs Audio v2 : licence communautaire à seuil d'utilisateurs) [S11][S12][S14]. CosyVoice 2/3 (Apache-2.0, français inclus) et Chatterbox Multilingual (MIT, français inclus) sont de bons secours [S6][S7][S8][S9]. VibeVoice reste dispo (MIT) mais Microsoft a retiré son propre dépôt pour usage détourné — statut fragile [S15][S16]. Côté musique, la plupart des modèles génératifs de qualité ont des poids CC-BY-NC (MusicGen, YuE2, AudioLDM2, Tango) [S32][S39][S46][S47] ; seuls ACE-Step, DiffRhythm, YuE v1 et Magenta RealTime (Apache-2.0/CC-BY-4.0) sont commercialement utilisables [S29][S34][S33][S36]. Aucun modèle génératif de SFX/foley ouvert et commercial-UE n'a été identifié (MMAudio CC-BY-NC, HunyuanVideo-Foley exclut explicitement l'UE, ThinkSound ambigu) [S41][S42][S43][S45] : la voie sûre reste les banques CC0/royalty-free documentées (Freesound filtré CC0, Sonniss GDC) [S48][S49]. Pour la transcription de contrôle, faster-whisper (MIT) et Whisper large-v3 (Apache-2.0) sont sûrs ; NVIDIA Canary-1B-v2 (CC-BY-4.0) donne un WER anglais mesuré de 2,18 % (LibriSpeech clean) avec horodatage mot à mot natif, mais aucun WER français officiel n'a été trouvé [S50][S51][S53]. Aucune source officielle YouTube ou TikTok ne publie −14 LUFS comme cible ; c'est un comportement de normalisation observé et un consensus de praticiens, à distinguer de la cible officielle EBU R128 (−23 LUFS, diffusion broadcast) [S38][S56][S57][S58].

## Constats

| # | Constat | Sources | Confiance | Conséquence pour le studio |
|---|---|---|---|---|
| 1 | Qwen3-TTS (QwenLM/Qwen3-TTS) est sous licence Apache-2.0, publié le 2026-01-22, tailles 0.6B et 1.7B, 10 langues dont le français, clonage vocal 3 s et design vocal par instruction en langage naturel, latence de streaming « aussi basse que 97 ms », support Transformers natif et vLLM jour-0 (inférence offline). | [S1][S2][S3] | élevée | Le narrateur reste légal et libre de droits en France ; le pipeline « portage CUDA » se réduit à une installation + reproduction du timbre, pas à un développement de backend |
| 2 | Aucune exigence VRAM ni vitesse d'inférence CUDA chiffrée n'est publiée par Qwen (page GitHub/HF lues) ; l'installation utilise `device_map="cuda:0"`, `torch.bfloat16`/`float16`, et FlashAttention 2 en option. | [S1] | élevée | VRAM et vitesse sur RTX 4070 Ti Super : **non mesuré** — à couvrir par `make gpu-smoke` en phase 3 |
| 3 | Kokoro-82M est Apache-2.0, sorti le 2025-01-27 (v1.0), 82M paramètres, 54 voix sur 8 langues, mais une seule voix française listée dans VOICES.md. | [S4][S5] | élevée | Kokoro reste utilisable en secours mais la variété de voix FR est très limitée ; ne pas en faire le narrateur principal |
| 4 | CosyVoice (FunAudioLLM), versions 2.0 (déc. 2024, 0.5B) et Fun-CosyVoice 3.0 (déc. 2025, 0.5B), est Apache-2.0, couvre 9 langues dont le français + 18 dialectes chinois, latence de streaming dès 150 ms. | [S6][S7] | élevée | Bon candidat de secours TTS multilingue commercial |
| 5 | Chatterbox / Chatterbox Multilingual (Resemble AI) est sous licence MIT, couvre 23+ langues dont le français, ~0.5B paramètres (backbone Llama), watermark PerTh intégré par défaut. | [S8][S9][S10] | élevée | Secours solide, watermark = traçabilité utile pour la divulgation IA (§4 mission) |
| 6 | IndexTTS2 est sous une licence propriétaire bilibili non standard (seuils de 100M MAU / 1 Md RMB de revenu annuel avant licence séparée, interdiction d'usage à haut risque, interdiction d'utiliser le modèle pour améliorer un autre modèle IA) ; ses langues documentées sont chinois, anglais, japonais, espagnol, arabe — **pas de français**. | [S11][S12] | élevée | Éliminé : licence non standard et absence de français |
| 7 | Higgs Audio v2 (Boson AI) est sous « BOSON HIGGS AUDIO 2 COMMUNITY LICENSE AGREEMENT », qui autorise l'usage commercial en dessous de 100 000 utilisateurs actifs annuels mais exige une licence étendue au-delà, sans restriction territoriale explicite. Langues documentées : anglais, chinois, allemand, coréen (pas de français confirmé). | [S13][S14] | moyenne | Utilisable pour un studio de petite taille, mais licence à réévaluer si le studio grandit ; français non confirmé → pas prioritaire |
| 8 | Microsoft a retiré le code source du dépôt officiel `microsoft/VibeVoice` après avoir constaté des usages détournés ; les poids (MIT) restent sur Hugging Face et un fork communautaire maintient le code. | [S15][S16] | moyenne | Statut fragile — utilisable techniquement (poids MIT) mais dépôt officiel instable ; à éviter comme dépendance critique |
| 9 | F5-TTS : code MIT, mais poids pré-entraînés sous CC-BY-NC-4.0 (entraînés sur le jeu de données Emilia, non commercial). | [S17][S18] | élevée | Éliminé pour un usage commercial (poids officiels non réutilisables), sauf ré-entraînement complet hors budget |
| 10 | XTTS-v2 (Coqui) est sous Coqui Public Model License (CPML) 1.0.0, qui n'autorise que l'usage non commercial du modèle et de ses sorties ; Coqui Inc. a fermé en janvier 2024, donc aucune licence commerciale n'est plus disponible. | [S19] | élevée | Éliminé pour un usage commercial |
| 11 | Fish-Speech / OpenAudio-S1 : code Apache-2.0, mais poids sous CC-BY-NC-SA-4.0. | [S20][S21] | élevée | Éliminé pour un usage commercial en l'état (poids) |
| 12 | Dia (Nari Labs) est Apache-2.0 ; Orpheus-TTS (Canopy Labs) a un code Apache-2.0 mais des poids publiés sous la licence communautaire Llama 3.2 (usage commercial autorisé sous condition d'attribution « Built with Llama » et de seuil d'utilisateurs). | [S22][S23] | élevée | Dia utilisable commercialement (mais focalisé dialogue EN, français non confirmé) ; Orpheus utilisable sous conditions Llama — à vérifier pour la France/UE (question ouverte) |
| 13 | Zonos (Zyphra) est Apache-2.0 pour le code et les poids (Zonos-v0.1 et ZONOS2). | [S24] | élevée | Candidat commercial viable, mais français non confirmé dans les sources lues |
| 14 | Kyutai TTS (kyutai/tts-1.6b-en_fr) a des poids sous CC-BY-4.0, couvre explicitement anglais et français, ~1.8B paramètres (backbone 1B + depth transformer 600M), délai acoustique/sémantique ≈ 1,28 s. | [S25] | élevée | Bon candidat commercial FR/EN, licence permissive avec attribution |
| 15 | Spark-TTS : code Apache-2.0, mais poids Spark-TTS-0.5B sous CC-BY-NC-SA-4.0 ; MaskGCT (Amphion) : code Amphion MIT, mais poids MaskGCT sous CC-BY-NC-4.0. | [S26][S27] | élevée | Poids éliminés pour usage commercial dans les deux cas |
| 16 | Voxtral (Mistral AI) : le modèle de compréhension vocale (STT) est Apache-2.0 (24B et 3B, sorti 2025-07-15) ; le modèle Voxtral TTS séparé (3B, poids + voix de référence) est sous CC-BY-NC-4.0. | [S28] | élevée | Voxtral STT utilisable commercialement comme alternative de contrôle ASR ; Voxtral TTS éliminé pour usage commercial |
| 17 | ACE-Step (Apache-2.0) : v1-3.5B, puis ACE-Step 1.5 (janvier 2026) et 1.5 XL 4B (avril 2026) ; génération d'un morceau complet en <2 s sur A100 et <10 s sur RTX 3090 selon le dépôt. | [S29][S30] | moyenne (chiffres de vitesse non vérifiés indépendamment) | Candidat musique commercial principal ; vitesse RTX 4070 Ti Super non mesurée à ce jour |
| 18 | Stable Audio Open est sous Stability AI Community License : usage commercial gratuit avec enregistrement obligatoire pour les organisations à moins d'1 M$ de revenu annuel ; au-delà, licence Enterprise payante requise ; génère jusqu'à 47 s d'audio. | [S31] | élevée | Utilisable pour le studio (revenu très en dessous du seuil), avec enregistrement à faire ; adapté aux effets courts plus qu'à la musique longue |
| 19 | MusicGen (Meta/Audiocraft) : code MIT, mais poids sous CC-BY-NC-4.0 (300M/1.5B/3.3B), entraîné sur 20 000 h de musique sous licence (Meta Music Initiative, Shutterstock, Pond5). | [S32] | élevée | Éliminé pour usage commercial (poids officiels) |
| 20 | YuE v1 (Apache-2.0, code et poids, annoncé 2025-01-30) autorise l'usage commercial des sorties ; YuE2 introduit un dual-licensing où le code reste Apache-2.0 mais les poids passent en CC-BY-NC-4.0. | [S33] | élevée | Utiliser uniquement YuE v1 pour un usage commercial ; YuE2 à écarter tant que ses poids restent NC |
| 21 | DiffRhythm et DiffRhythm 2 (ASLP-lab) sont publiés sous licence Apache-2.0 (code et poids). | [S34] | élevée | Candidat musique commercial |
| 22 | SongGeneration / LeVo (Tencent AI Lab) affiche une incohérence de licence : NOASSERTION dans certains éléments du dépôt vs. mention Apache-2.0 ailleurs après un correctif. | [S35] | faible | Statut à clarifier avant tout usage commercial — ne pas retenir comme dépendance principale tant que non confirmé |
| 23 | Magenta RealTime (Google) : code Apache-2.0, poids sous CC-BY-4.0 ; Magenta RealTime 2 (2026-06-04) génère du 48 kHz stéréo avec ~200 ms de latence de contrôle, y compris sur Apple Silicon. Google déclare ne revendiquer aucun droit sur les sorties générées. | [S36][S37] | élevée | Candidat musique commercial temps réel, licence permissive avec attribution |
| 24 | YouTube Audio Library propose deux régimes : licence YouTube standard (pas d'attribution, mais usage limité aux vidéos YouTube selon les CGU consultées) et licence Creative Commons CC-BY (attribution obligatoire, réutilisable ailleurs) ; les pistes de la bibliothèque ne sont pas réclamées par le Content ID. | [S38] | élevée | Compatible avec la règle « licence documentée » pour les pistes CC-BY explicitement attribuées ; les pistes « standard YouTube » sont à réserver à YouTube et ne satisfont pas une réutilisation multi-plateforme (TikTok) |
| 25 | FluidSynth est sous licence LGPL ; les soundfonts génériques type FluidR3_GM sont documentées sous licence Creative Commons par le wiki officiel du projet (les mentions « MIT » trouvées ailleurs ne sont pas confirmées par la source officielle). | [S39] | moyenne | Vérifier la licence exacte de chaque soundfont utilisé avant intégration ; FluidSynth lui-même ne pose pas de problème commercial (LGPL, dynamiquement liée) |
| 26 | pyloudnorm est MIT, implémente ITU-R BS.1770-4. | [S40] | élevée | Outil de vérification indépendant du mastering, sûr en usage commercial |
| 27 | MMAudio : code MIT, mais checkpoints sous CC-BY-NC-4.0. | [S41][S42] | élevée | Éliminé pour usage commercial en l'état (poids) |
| 28 | HunyuanVideo-Foley (Tencent) est sous licence « tencent-hunyuan-community », dont le texte exclut explicitement le territoire de l'Union européenne, du Royaume-Uni et de la Corée du Sud (« THIS LICENSE AGREEMENT DOES NOT APPLY IN THE EUROPEAN UNION... »). | [S43][S44] | élevée | **Éliminatoire** pour un opérateur en France (UE), conformément à la contrainte du studio |
| 29 | ThinkSound (Alibaba/QwenAudio) affiche un fichier LICENSE Apache-2.0 mais son README précise que « l'usage commercial n'est PAS autorisé sans licence explicite des auteurs originaux ». | [S45] | moyenne | Incohérence licence/README → traiter comme non commercial et écarter tant que non clarifié |
| 30 | AudioLDM 2 et Tango/Tango 2 sont tous deux sous licence CC-BY-NC-SA-4.0. | [S46][S47] | élevée | Éliminés pour usage commercial |
| 31 | Sonniss GDC (bundle GameAudioGDC) accorde une licence mondiale, non exclusive, libre de redevance, pour projets personnels et commerciaux, sans attribution requise, incluant explicitement films/vidéos ; interdiction de revendre les sons isolément ou de les utiliser pour entraîner une IA sans autorisation écrite. | [S48] | élevée | Banque sûre et directement utilisable en production, y compris pour entraîner nos propres modèles seulement avec autorisation (à ne pas faire) |
| 32 | Freesound permet de filtrer les résultats par licence CC0 (« Creative Commons 0 »), qui autorise un usage commercial sans attribution ; les sons CC-BY-NC y sont explicitement interdits en usage commercial. | [S49] | élevée | Filtrer systématiquement sur CC0 (ou CC-BY avec attribution tracée) dans le pipeline SFX |
| 33 | faster-whisper (SYSTRAN) est MIT ; Whisper large-v3 (OpenAI) est publié sous Apache-2.0 (page de modèle officielle lue), avec un WER moyen de 7,44 sur l'open-asr-leaderboard, 15,95 sur AMI ; aucun WER français chiffré n'a été trouvé sur la fiche modèle officielle. | [S50][S51] | élevée (licence) / faible (WER FR) | Moteur de contrôle sûr en licence ; WER FR à mesurer nous-mêmes (non mesuré dans les sources officielles trouvées) |
| 34 | WhisperX est sous licence BSD-4-Clause et dépend de pyannote-audio (CC-BY-4.0) pour la VAD/diarisation ; il ajoute l'alignement forcé mot à mot via un modèle phonémique (ex. wav2vec2). | [S52] | élevée | Utilisable commercialement avec attribution de la dépendance pyannote |
| 35 | NVIDIA Canary-1B-v2 est sous CC-BY-4.0, WER 2,18 % sur LibriSpeech clean (EN) et WER moyen 7,15 % sur l'Open ASR Leaderboard, horodatage mot à mot natif pour 25 langues européennes ; aucun WER français isolé n'a été publié dans les sources lues. Parakeet-TDT-0.6B-v3 atteint 7,15 % de WER sur AMI et 10,82 % sur LibriSpeech clean selon NVIDIA. | [S53][S54] | élevée (licence, EN) / faible (FR isolé) | Bon candidat ASR de contrôle, licence permissive ; WER FR à mesurer nous-mêmes |
| 36 | Le filtre `loudnorm` de ffmpeg applique une normalisation de loudness conforme à EBU R128, avec un usage en deux passes documenté (I = loudness intégrée cible, TP = true peak, LRA = plage de loudness). | [S55] | élevée | Outil de mastering par défaut, gratuit et scriptable |
| 37 | La norme officielle EBU R128 (v5.0, novembre 2023) cible une loudness moyenne de programme de **−23 LUFS** pour la diffusion broadcast — ce n'est pas la cible des plateformes de streaming/vidéo. | [S56] | élevée | Ne pas confondre la cible EBU R128 broadcast (−23 LUFS) avec la pratique recommandée pour YouTube/TikTok (−14 LUFS, voir écarts) |
| 38 | Aucune page d'aide officielle Google/YouTube consultée ne publie −14 LUFS comme cible d'upload ; plusieurs sources de praticiens (mastering audio) convergent sur −14 LUFS comme comportement de normalisation observé à la lecture, avec true peak ≤ −1 dBTP. | [S38][S57][S59] | moyenne | Garder −14 LUFS ±1 comme cible de production (large consensus), mais noter que ce n'est pas une exigence officielle publiée |
| 39 | Aucune documentation officielle TikTok (newsroom/developers) trouvée sur une cible de loudness ; le consensus de praticiens converge également vers ≈ −14 LUFS intégré, true peak ≤ −1 dBTP, sans re-rendu du fichier (gain de lecture appliqué). | [S58] | moyenne | Même cible que YouTube en pratique ; confirme que viser −14 LUFS ±1 pour les deux plateformes est une hypothèse raisonnable mais non officiellement documentée |

## 1. TTS — comparatif détaillé

| Modèle | Licence poids | Licence code | Français | Clonage/Design | Taille | VRAM mesurée | Vitesse CUDA mesurée | Streaming | Verdict commercial UE |
|---|---|---|---|---|---|---|---|---|---|
| Qwen3-TTS | Apache-2.0 [S1] | Apache-2.0 [S1] | Oui | Clonage 3 s + design vocal | 0.6B / 1.7B | non mesuré | non mesuré | Oui, ~97 ms | **Retenu (principal)** |
| Kokoro-82M | Apache-2.0 [S4] | Apache-2.0 [S4] | 1 voix seulement [S5] | Non (voix fixes) | 82M | non mesuré (très léger, inférence connue rapide) | non mesuré | Non documenté | **Retenu (secours léger)** |
| CosyVoice 2/3 | Apache-2.0 [S6][S7] | Apache-2.0 | Oui | Clonage zero-shot | 0.5B | non mesuré | non mesuré | Oui, dès 150 ms | Retenu (secours) |
| Chatterbox / Multilingual | MIT [S8] | MIT [S8] | Oui (23+ langues) [S9] | Clonage zero-shot | ~0.5B | non mesuré | non mesuré | Non documenté | Retenu (secours) |
| IndexTTS2 / 2.5 | Licence bilibili custom [S11] | idem | **Non** [S12] | Clonage + contrôle émotionnel fin | n.d. | non mesuré | non mesuré | Non documenté | **Éliminé** (licence + pas de FR) |
| Higgs Audio v2 | Boson Community License (seuil 100k MAU) [S14] | idem | Non confirmé [S13] | Clonage | 3B | non mesuré | non mesuré | Non documenté | Utilisable sous seuil, non prioritaire |
| VibeVoice | MIT [S15][S16] | MIT (dépôt officiel retiré) | Non confirmé | Multi-locuteur longform | 1.5B / 7B | non mesuré | non mesuré | Non documenté | Techniquement possible, statut instable |
| F5-TTS | **CC-BY-NC-4.0** [S18] | MIT [S17] | Non confirmé (Emilia multi-langue) | Clonage | n.d. | non mesuré | non mesuré | Non documenté | **Éliminé** (poids NC) |
| XTTS-v2 | **CPML 1.0.0 (NC)** [S19] | MPL-2.0 | Oui (17 langues) | Clonage 6 s | n.d. | non mesuré | non mesuré | Non documenté | **Éliminé** (NC) |
| Fish-Speech / OpenAudio-S1 | **CC-BY-NC-SA-4.0** [S20] | Apache-2.0 [S21] | Non confirmé | Clonage | n.d. | non mesuré | non mesuré | Non documenté | **Éliminé** (poids NC) |
| Dia | Apache-2.0 [S22] | Apache-2.0 | Non confirmé (dialogue EN) | Dialogue à 2 voix | 1.6B | non mesuré | non mesuré | Non documenté | Utilisable, FR incertain |
| Orpheus-TTS | Llama 3.2 Community License [S23] | Apache-2.0 | Non confirmé | Clonage | 3B (+400M/150M annoncés) | non mesuré | non mesuré | Non documenté | Utilisable sous conditions Llama (UE à vérifier) |
| Zonos / ZONOS2 | Apache-2.0 [S24] | Apache-2.0 | Non confirmé (200k h multilingues) | Clonage expressif | 1.6B / MoE 8B (900M actifs) | non mesuré | non mesuré | Oui (ZONOS2 temps réel) | Utilisable |
| Kyutai TTS | CC-BY-4.0 [S25] | s.d. | **Oui (EN/FR natif)** | Voix du projet Unmute (CC0) | 1.6–1.8B | non mesuré | non mesuré | Oui, délai ≈1,28 s | Retenu (candidat FR/EN solide) |
| Spark-TTS | **CC-BY-NC-SA-4.0** [S26] | Apache-2.0 | Non confirmé | Clonage | 0.5B | non mesuré | non mesuré | Non documenté | **Éliminé** (poids NC) |
| MaskGCT | **CC-BY-NC-4.0** [S27] | MIT (Amphion) | Non confirmé | Zero-shot non-autorégressif | n.d. | non mesuré | non mesuré | Non documenté | **Éliminé** (poids NC) |
| Voxtral TTS (Mistral) | **CC-BY-NC-4.0** [S28] | n.d. | Non confirmé | Voix de référence fournies | 3B | non mesuré | non mesuré | Non documenté | **Éliminé** (poids NC) ; Voxtral STT (Apache-2.0) reste utilisable comme ASR |

## 2. Musique — comparatif et alternative procédurale

| Modèle | Licence poids | Licence code | Commercial UE | Notes |
|---|---|---|---|---|
| ACE-Step (v1, 1.5, 1.5 XL) | Apache-2.0 [S29] | Apache-2.0 | **Oui** | Le plus rapide annoncé (<2 s/morceau A100, <10 s RTX 3090, chiffres du dépôt non vérifiés indépendamment) [S30] |
| YuE v1 | Apache-2.0 [S33] | Apache-2.0 | **Oui** | YuE2 : poids repassés en CC-BY-NC-4.0, ne pas utiliser |
| DiffRhythm / DiffRhythm 2 | Apache-2.0 [S34] | Apache-2.0 | **Oui** | Génération de chanson complète par diffusion latente |
| SongGeneration / LeVo (Tencent) | Statut ambigu (NOASSERTION / Apache-2.0 selon la source) [S35] | idem | **À vérifier** | Ne pas retenir avant clarification écrite de la licence |
| MusicGen (Meta) | **CC-BY-NC-4.0** [S32] | MIT | **Éliminé** | Entraîné sur données sous licence Meta, non réutilisable commercialement en poids officiels |
| Stable Audio Open | Stability AI Community License (gratuit <1 M$ revenu, enregistrement requis) [S31] | idem | Oui sous condition | Limité à 47 s ; plus adapté aux transitions/textures qu'à une bande-son complète |
| Magenta RealTime / RT2 (Google) | CC-BY-4.0 [S36] | Apache-2.0 | **Oui** | Temps réel, ~200 ms de latence de contrôle sur RT2 [S37] |

**Droits sur les sorties et risque Content ID.** Aucune source officielle sur le statut « fausse réclamation Content ID » des sorties de modèles génératifs n'a été trouvée pour ces modèles spécifiquement ; **Inférence** (confiance faible) : un modèle entraîné sur des corpus musicaux à grande échelle peut générer un passage suffisamment proche d'une œuvre préexistante pour déclencher une correspondance Content ID par similarité acoustique, indépendamment de la licence du modèle — risque géré par la revue humaine (porte G2/G3) plutôt que par la licence seule.

**Alternative procédurale (recommandée par défaut).** FluidSynth est LGPL [S39] ; il peut être piloté entièrement en code (génération MIDI programmatique) pour produire une trame musicale à droits garantis, sans dépendre d'un modèle génératif ni de ses biais de licence. La licence exacte de chaque SoundFont utilisée doit être vérifiée individuellement (le wiki officiel FluidSynth documente FluidR3_GM sous licence Creative Commons, pas MIT comme certaines sources tierces l'affirment) [S39].

**YouTube Audio Library et la règle « licence documentée ».** Les pistes marquées Creative Commons (CC-BY) dans la bibliothèque sont réutilisables hors YouTube avec attribution obligatoire et satisfont la règle de licence documentée du §12 de la mission ; les pistes en « licence YouTube standard » (sans attribution) ne sont, selon les CGU consultées, prévues que pour un usage sur YouTube et ne couvrent donc pas une réutilisation multi-plateforme (TikTok) — à traiter comme non conformes à une bande-son commune multi-chaînes [S38].

## 3. Effets sonores / foley — comparatif

| Modèle/banque | Licence | Commercial UE | Notes |
|---|---|---|---|
| MMAudio | Code MIT, poids **CC-BY-NC-4.0** [S41][S42] | **Éliminé** (poids) | Vidéo→audio synchronisé, qualité saluée mais non réutilisable en poids officiels |
| HunyuanVideo-Foley | « tencent-hunyuan-community », **exclut explicitement l'UE/UK/Corée du Sud** [S43][S44] | **Éliminé (territoire)** | Sortie initiale 2025-08-28 ; à ne jamais déployer en France selon les termes du texte de licence lui-même |
| ThinkSound | LICENSE Apache-2.0 mais README interdit l'usage commercial sans accord explicite [S45] | **Éliminé (incohérence)** | Traiter comme non commercial tant que la contradiction n'est pas levée par les auteurs |
| Stable Audio Open | Stability AI Community License [S31] | Oui sous condition | Utilisable pour des textures/effets courts (≤47 s) |
| AudioLDM 2 | **CC-BY-NC-SA-4.0** [S46] | **Éliminé** | — |
| Tango / Tango 2 | **CC-BY-NC-SA-4.0** [S47] | **Éliminé** | — |

**Conclusion SFX :** aucun modèle génératif de foley identifié ne satisfait simultanément « poids ouverts », « commercial » et « pas d'exclusion UE ». La voie recommandée est donc **exclusivement** les banques à licence documentée :
- **Sonniss GDC** : licence mondiale non exclusive, royalty-free, commercial et personnel, sans attribution, usage explicite en « films, vidéos » ; interdiction de revente isolée ou d'entraînement d'IA sans autorisation [S48].
- **Freesound filtré CC0** : filtre `license:"Creative Commons 0"` disponible dans l'UI et l'API, usage commercial sans attribution ; à ne jamais mélanger avec des résultats CC-BY-NC [S49].
- Complément : synthèse procédurale de bruitages en code (bibliothèques DSP/ffmpeg) pour les cas non couverts par les banques.

## 4. Transcription / contrôle — comparatif

| Outil | Licence | WER mesuré (source) | Horodatage mot à mot | Notes |
|---|---|---|---|---|
| faster-whisper | MIT [S50] | non mesuré dans les sources officielles lues | Oui (via Whisper) | Moteur CTranslate2, rapide sur CPU/GPU |
| Whisper large-v3 | Apache-2.0 [S51] | 7,44 (moyenne open-asr-leaderboard), 15,95 (AMI) ; **FR non publié sur la fiche officielle** | Approximatif (segments) | — |
| Whisper large-v3-turbo | Apache-2.0 (variante de large-v3) | non mesuré dans les sources officielles lues | Approximatif | Non confirmé en détail (page non ouverte séparément) |
| WhisperX | BSD-4-Clause (+ dépendance pyannote CC-BY-4.0) [S52] | hérite de Whisper | **Oui, alignement forcé phonémique** | Ajoute la diarisation |
| NVIDIA Canary-1B-v2 | CC-BY-4.0 [S53] | 2,18 % (LibriSpeech clean, EN) ; 7,15 % moyen (Open ASR Leaderboard) ; **FR isolé non publié** | **Oui, natif** | 25 langues européennes |
| NVIDIA Parakeet-TDT-0.6B-v3 | CC-BY-4.0 (famille NeMo) [S54] | 7,15 % (AMI), 10,82 % (LibriSpeech clean) | Oui | Optimisé streaming temps réel |

**Méthode de calcul du WER pour le seuil ≤ 3 % du §8 (proposition, aucune source ne fixe une méthode unique) :** Inférence (confiance moyenne) : normaliser la casse, la ponctuation et les nombres (conversion chiffres/texte) avant alignement, utiliser l'algorithme standard de distance d'édition au niveau mot (substitutions + insertions + suppressions / nombre de mots de référence), et publier la normalisation exacte utilisée à chaque mesure pour rendre le seuil de 3 % reproductible — aucun standard officiel de normalisation n'a été trouvé dans les sources consultées pour ce projet précis.

## 5. Loudness

| Norme / cible | Valeur | Source | Type | Confiance |
|---|---|---|---|---|
| EBU R128 (diffusion broadcast) | −23 LUFS intégré, tolérance ±0,5 LU (v3.0, 2014) ; v5.0 = nov. 2023 | [S56] | officiel | élevée |
| ITU-R BS.1770 | Algorithme de mesure de loudness sous-jacent à EBU R128 et à la plupart des plateformes | [S56] (référencé), [S40] (implémentation) | officiel/praticien | moyenne |
| YouTube (comportement observé) | ≈ −14 LUFS, gain négatif appliqué si plus fort, pas de gain si plus faible | [S57][S59] | praticien | moyenne |
| YouTube Audio Library | Aucune mention de cible LUFS ; garantie « pas de réclamation Content ID » sur ses propres pistes | [S38] | officiel | élevée (sur ce point précis) |
| TikTok (comportement observé) | ≈ −14 LUFS intégré, true peak ≤ −1 dBTP, gain de lecture appliqué sans réencodage | [S58] | praticien | moyenne |
| Outils | `ffmpeg loudnorm` en deux passes (mesure puis application) ; `pyloudnorm` (MIT, ITU-R BS.1770-4) pour vérification indépendante | [S55][S40] | officiel | élevée |

Aucune page d'aide officielle Google (YouTube) ou documentation développeur/newsroom TikTok publiant une cible LUFS chiffrée n'a été trouvée malgré plusieurs recherches ciblées ; voir « Écarts avec MISSION §4 ».

## 6. Recommandation — chaîne audio cible

**TTS narrateur (voix off).**
- Principal : **Qwen3-TTS** (Apache-2.0, 0.6B/1.7B, transformers + vLLM jour-0, français inclus) [S1][S2][S3], reproduisant le timbre custom déjà créé (aucune personne réelle, conforme §5 mission).
- Secours qualité/diversité : **Chatterbox Multilingual** (MIT, français inclus, watermark intégré) [S8][S9] ou **CosyVoice 2/3** (Apache-2.0, français inclus, streaming natif) [S6][S7].
- Secours léger/rapide : **Kokoro-82M** (Apache-2.0, déjà dans le pipeline `usine-video`) [S4], voix française unique — n'utiliser que pour des rôles secondaires ou des tests rapides.
- Candidat FR/EN natif à évaluer en phase 3 : **Kyutai TTS** (CC-BY-4.0) [S25].
- Éliminés pour licence non commerciale : F5-TTS, XTTS-v2/CPML, Fish-Speech/OpenAudio, Spark-TTS, MaskGCT, Voxtral TTS [S18][S19][S20][S26][S27][S28]. Éliminé pour licence non standard + absence de français : IndexTTS2 [S11][S12].

**Musique.**
- Par défaut : **composition procédurale en code** (génération MIDI programmatique + FluidSynth LGPL + SoundFonts à licence vérifiée individuellement) [S39] — droits garantis à 100 %, coût GPU nul.
- Complément génératif commercial : **ACE-Step** (Apache-2.0) [S29][S30], **DiffRhythm** (Apache-2.0) [S34], **YuE v1** (Apache-2.0) [S33], **Magenta RealTime** (CC-BY-4.0, temps réel) [S36][S37].
- Bibliothèque à licence documentée : pistes **CC-BY** de la YouTube Audio Library, avec attribution tracée [S38] ; ne jamais utiliser les pistes « licence YouTube standard » hors YouTube.
- Éliminés pour licence non commerciale : MusicGen [S32], YuE2 (poids) [S33]. À clarifier avant usage : SongGeneration/LeVo (licence ambiguë) [S35].

**Effets sonores / foley.**
- Principal : banques à licence documentée — **Sonniss GDC** (royalty-free, commercial, sans attribution) [S48] et **Freesound filtré CC0** [S49].
- Aucun modèle génératif de foley n'est retenu : MMAudio (poids CC-BY-NC) [S41][S42], HunyuanVideo-Foley (exclut l'UE) [S43][S44], ThinkSound (incohérence licence/README) [S45], AudioLDM2/Tango (CC-BY-NC-SA) [S46][S47] sont tous éliminés pour la France.
- Stable Audio Open reste une option d'appoint pour des textures courtes (<47 s) sous enregistrement Stability [S31].

**Transcription / contrôle (voice_director, WER ≤ 3 %).**
- Principal : **faster-whisper** (MIT) avec Whisper large-v3 ou large-v3-turbo [S50][S51].
- Comparaison qualité / horodatage mot à mot natif : **NVIDIA Canary-1B-v2** (CC-BY-4.0) [S53].
- Alignement forcé phrase par phrase pour la régénération ciblée : **WhisperX** (BSD-4-Clause + dépendance pyannote CC-BY-4.0) [S52].
- WER français non publié officiellement pour aucun de ces modèles dans les sources lues → mesure interne obligatoire avant de valider le seuil ≤ 3 % du §8.

**Mastering / loudness.**
- `ffmpeg loudnorm` en deux passes, cible −14 LUFS ±1, true peak ≤ −1 dBTP [S55], vérification indépendante par **pyloudnorm** (MIT, ITU-R BS.1770-4) [S40].
- Cible −14 LUFS non officiellement documentée par YouTube ni TikTok (comportement observé + consensus praticien) [S57][S58][S59] — garder comme cible de production mais tracer la source comme non officielle dans `knowledge/`.

**VRAM et risques — vue d'ensemble.** Aucune valeur VRAM chiffrée officielle n'a été trouvée pour Qwen3-TTS, Kokoro, CosyVoice, Chatterbox, ACE-Step (au-delà de la mention indirecte « tourne sur RTX 3090 »), MMAudio ou les modèles Canary/Parakeet en inférence GPU — toutes les cases « VRAM mesurée » ci-dessus sont **non mesuré** et doivent être remplies par `make bench-models` / `make gpu-smoke` en phase 3, sur les 4× RTX 4070 Ti Super 16 Go. Risque principal identifié : la densité de licences CC-BY-NC dans l'écosystème open-weight audio 2025-2026 est élevée (majorité des modèles musique/SFX/TTS alternatifs rencontrés) — tout nouveau modèle candidat doit être vérifié individuellement sur son fichier LICENSE avant intégration, jamais sur la seule réputation du dépôt.

### Plan de portage MLX → CUDA de Qwen3-TTS

1. **Constat de départ.** Le dépôt officiel `QwenLM/Qwen3-TTS` est un modèle PyTorch/Transformers standard avec support CUDA natif (`device_map="cuda:0"`, `bfloat16`/`float16`, FlashAttention 2 optionnelle) et support vLLM jour-0 (inférence offline) [S1]. Le pipeline Mac M1 du studio utilisait vraisemblablement un fork communautaire MLX (ex. type mlx-audio), pas le dépôt officiel : il ne s'agit donc pas d'un portage logiciel (réécriture de kernels MLX→CUDA), mais d'un changement de backend d'exécution vers le chemin officiel du modèle.
2. **Étapes concrètes :**
   a. Installer `qwen-tts` (pip) + `transformers` + `flash-attn` sur la machine GPU Linux/CUDA (Ada sm_89 supporté par les versions récentes de FlashAttention 2, à vérifier en phase 3).
   b. Reproduire le timbre custom du narrateur via les checkpoints officiels **CustomVoice** (clonage 3 s à partir de l'audio déjà produit sur Mac) ou **VoiceDesign 1.7B** (design par instruction), afin d'obtenir un résultat équivalent au fork MLX utilisé jusqu'ici [S2][S3].
   c. Valider par le contrôle Whisper existant (§7 `voice_director`) que le WER et la ressemblance du timbre restent au niveau actuel (92 % mentionné en §5 de la mission).
   d. Benchmarker VRAM et temps réel sur une RTX 4070 Ti Super 16 Go (bf16 d'abord, puis quantification GGUF communautaire si nécessaire — ex. `Serveurperso/Qwen3-TTS-GGUF`, dépôt tiers non officiel à valider avant usage en production) ; objectif : un temps de synthèse très inférieur aux ~1 h 15 observées sur Mac M1 via MLX, ce chiffre n'étant pas représentatif d'un GPU CUDA dédié.
   e. Si la VRAM disponible en parallèle des autres modèles (vidéo, musique) sur les 4 GPU répartis est insuffisante, isoler le TTS sur un GPU dédié dans l'ordonnanceur de file (§6 de la mission).
3. **Non mesuré à ce jour :** VRAM exacte et temps réel de synthèse sur RTX 4070 Ti Super — à produire via `make gpu-smoke` en phase 3 et à consigner dans `docs/CAPACITY.md`.

## Écarts avec MISSION §4

| Affirmation de la mission | Verdict (confirmé / infirmé / nuancé / non vérifiable) | Sources | Correction proposée |
|---|---|---|---|
| « Qwen3-TTS ... tournait sur Mac M1 via MLX (~1 h 15 par voix complète) → portage CUDA attendu » (§5) | Nuancé | [S1][S2][S3] | Le dépôt officiel Qwen3-TTS est déjà un modèle Transformers/vLLM avec support CUDA natif (Apache-2.0) : il n'y a pas de portage logiciel MLX→CUDA à écrire. Reformuler la tâche en « reproduction du timbre custom via les checkpoints officiels CustomVoice/VoiceDesign + benchmark VRAM/vitesse sur RTX 4070 Ti Super », et retirer l'hypothèse d'un effort d'ingénierie de portage bas niveau |
| « Audio : loudness intégrée −14 LUFS ±1 (vérifie les cibles des plateformes) » (§8) | Non vérifiable officiellement / nuancé | [S38][S56][S57][S58][S59] | Aucune page d'aide officielle YouTube ni documentation officielle TikTok consultée ne publie −14 LUFS comme cible d'upload chiffrée ; c'est un comportement de normalisation à la lecture observé par des praticiens, à ne pas confondre avec la cible officielle EBU R128 (−23 LUFS, diffusion broadcast, contexte différent). Conserver −14 LUFS ±1 comme cible de production (consensus large, faible risque), mais documenter dans `knowledge/` que la source est praticien/confiance moyenne, pas une exigence officielle publiée par les plateformes |
| « modèle local de musique ou banque sous licence documentée » (stack par défaut, §6) | Confirmé mais fortement nuancé | [S32][S39][S46][S47][S29][S33][S34][S36] | La majorité des modèles musique/SFX open-weight rencontrés (MusicGen, YuE2, AudioLDM2, Tango, MMAudio) ont des **poids CC-BY-NC**, incompatibles avec l'usage commercial du studio ; ne retenir que ACE-Step, DiffRhythm, YuE v1, Magenta RealTime (Apache-2.0/CC-BY-4.0) côté génératif, et prioriser la composition procédurale (FluidSynth + SoundFonts à licence vérifiée) comme le prévoit déjà le §6 |
| « aucune API ni aucun service externe de génération ... de voix, de musique ou de sons » (§5, règle dure) | Confirmé, renforcé | [S43][S44] | Aucun contournement identifié dans cette recherche ; à l'inverse, HunyuanVideo-Foley illustre un piège proche : un modèle *local à poids ouverts* mais dont la licence exclut explicitement le territoire UE — ajouter une vérification systématique de la clause de territoire, pas seulement « commercial oui/non », dans le futur registre des licences (§6 principe 3) |
| Pipeline `usine-video` : « Kokoro TTS » (§5, contexte existant) | Confirmé mais nuancé | [S4][S5] | Kokoro-82M reste valide (Apache-2.0, léger) mais n'a qu'une seule voix française documentée dans VOICES.md ; le confirmer comme secours/rôles secondaires plutôt que voix principale multi-personnages |

## Questions ouvertes

- VRAM et vitesse réelle de Qwen3-TTS, Kokoro, CosyVoice, Chatterbox, ACE-Step, Canary/Parakeet en inférence sur une RTX 4070 Ti Super 16 Go — aucune source ne les publie ; nécessite `make gpu-smoke` / `make bench-models` en phase 3.
- WER français chiffré et officiel pour Whisper large-v3/turbo, faster-whisper, NVIDIA Canary et Parakeet — non trouvé dans les sources officielles consultées ; nécessite une mesure interne sur corpus FR maison, avec méthode de normalisation à documenter (voir §4 de cette note).
- Statut exact et pérennité de VibeVoice après le retrait du dépôt officiel par Microsoft — à resurveiller avant toute dépendance critique.
- Licence définitive de SongGeneration/LeVo (Tencent) : incohérence NOASSERTION / Apache-2.0 non résolue dans les sources lues.
- Compatibilité de la licence communautaire Llama 3.2 (poids Orpheus-TTS) avec un usage commercial en France/UE spécifiquement — les restrictions connues des licences Llama récentes ont historiquement visé certains modèles multimodaux ; à vérifier pour Orpheus avant adoption.
- Support du français par Dia, Zonos, Spark-TTS et Higgs Audio v2 — non confirmé dans les pages officielles lues (au-delà de la mention générale « multilingue »).
- Existence d'une page d'aide officielle YouTube ou d'une documentation officielle TikTok publiant explicitement une cible LUFS — recherche infructueuse à ce jour malgré plusieurs requêtes ciblées ; à réessayer périodiquement (le §4 de la mission demande une revérification à chaque session).
- Date de sortie précise de Kyutai TTS et ses exigences VRAM en inférence — non trouvées dans les pages consultées.

## Sources

| ID | Titre | URL | Date source | Consulté | Type | Confiance |
|---|---|---|---|---|---|---|
| S1 | GitHub — QwenLM/Qwen3-TTS (README, licence, installation) | https://github.com/QwenLM/Qwen3-TTS | 2026-01-22 | 2026-09-28 | officiel | élevée |
| S2 | Hugging Face — Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice | https://huggingface.co/Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice | s.d. | 2026-09-28 | officiel | élevée |
| S3 | Hugging Face — Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign | https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign | s.d. | 2026-09-28 | officiel | élevée |
| S4 | Hugging Face — hexgrad/Kokoro-82M | https://huggingface.co/hexgrad/Kokoro-82M | 2025-01-27 | 2026-09-28 | officiel | élevée |
| S5 | Hugging Face — hexgrad/Kokoro-82M — VOICES.md | https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md | s.d. | 2026-09-28 | officiel | élevée |
| S6 | GitHub — FunAudioLLM/CosyVoice (README) | https://github.com/FunAudioLLM/CosyVoice | 2025-12 | 2026-09-28 | officiel | élevée |
| S7 | GitHub — FunAudioLLM/CosyVoice — LICENSE | https://github.com/FunAudioLLM/CosyVoice/blob/main/LICENSE | s.d. | 2026-09-28 | officiel | élevée |
| S8 | GitHub — resemble-ai/chatterbox — LICENSE | https://github.com/resemble-ai/chatterbox/blob/master/LICENSE | 2025 | 2026-09-28 | officiel | élevée |
| S9 | Hugging Face — ResembleAI/chatterbox | https://huggingface.co/ResembleAI/chatterbox | s.d. | 2026-09-28 | officiel | élevée |
| S10 | Resemble AI — Chatterbox Multilingual v3 (blog) | https://www.resemble.ai/resources/chatterbox-multilingual-v3-tts-with-embedded-watermarking-for-25-languages | 2026 | 2026-09-28 | presse | moyenne |
| S11 | GitHub — index-tts/index-tts — LICENSE | https://github.com/index-tts/index-tts/blob/main/LICENSE | s.d. | 2026-09-28 | officiel | élevée |
| S12 | GitHub — index-tts/index-tts (README, langues, IndexTTS-2.5) | https://github.com/index-tts/index-tts | 2026-08-10 | 2026-09-28 | officiel | élevée |
| S13 | GitHub — boson-ai/higgs-audio (README) | https://github.com/boson-ai/higgs-audio | s.d. | 2026-09-28 | officiel | élevée |
| S14 | Hugging Face — bosonai/higgs-audio-v2-generation-3B-base — LICENSE | https://huggingface.co/bosonai/higgs-audio-v2-generation-3B-base/blob/main/LICENSE | s.d. | 2026-09-28 | officiel | élevée |
| S15 | Hacker News — Microsoft pulls VibeVoice speech synthesis repo after misuse | https://news.ycombinator.com/item?id=45148114 | 2025 | 2026-09-28 | presse | moyenne |
| S16 | Hugging Face — microsoft/VibeVoice-1.5B — discussion #30 (dépôt GitHub supprimé) | https://huggingface.co/microsoft/VibeVoice-1.5B/discussions/30 | s.d. | 2026-09-28 | praticien | moyenne |
| S17 | GitHub — SWivid/F5-TTS — LICENSE | https://github.com/SWivid/F5-TTS/blob/main/LICENSE | s.d. | 2026-09-28 | officiel | élevée |
| S18 | Hugging Face — SWivid/F5-TTS — README.md | https://huggingface.co/SWivid/F5-TTS/blob/main/README.md | s.d. | 2026-09-28 | officiel | élevée |
| S19 | Hugging Face — coqui/XTTS-v2 — LICENSE.txt (CPML 1.0.0) | https://huggingface.co/coqui/XTTS-v2/blob/main/LICENSE.txt | s.d. | 2026-09-28 | officiel | élevée |
| S20 | Hugging Face — fishaudio/openaudio-s1-mini — discussion #7 (licence CC-BY-NC-SA-4.0) | https://huggingface.co/fishaudio/openaudio-s1-mini/discussions/7 | s.d. | 2026-09-28 | praticien | moyenne |
| S21 | GitHub — fishaudio/fish-speech (README, licence code) | https://github.com/fishaudio/fish-speech | s.d. | 2026-09-28 | officiel | élevée |
| S22 | GitHub — nari-labs/dia — LICENSE | https://github.com/nari-labs/dia/blob/main/LICENSE | s.d. | 2026-09-28 | officiel | élevée |
| S23 | GitHub — canopyai/Orpheus-TTS — LICENSE | https://github.com/canopyai/Orpheus-TTS/blob/main/LICENSE | 2025-03 | 2026-09-28 | officiel | élevée |
| S24 | GitHub — Zyphra/Zonos — LICENSE | https://github.com/Zyphra/Zonos/blob/main/LICENSE | s.d. | 2026-09-28 | officiel | élevée |
| S25 | Hugging Face — kyutai/tts-1.6b-en_fr | https://huggingface.co/kyutai/tts-1.6b-en_fr | s.d. | 2026-09-28 | officiel | élevée |
| S26 | Hugging Face — SparkAudio/Spark-TTS-0.5B | https://huggingface.co/SparkAudio/Spark-TTS-0.5B | s.d. | 2026-09-28 | officiel | élevée |
| S27 | Hugging Face — amphion/MaskGCT | https://huggingface.co/amphion/MaskGCT | s.d. | 2026-09-28 | officiel | élevée |
| S28 | Mistral AI — Voxtral (annonce officielle) | https://mistral.ai/news/voxtral/ | 2025-07-15 | 2026-09-28 | officiel | élevée |
| S29 | GitHub — ace-step/ACE-Step — LICENSE | https://github.com/ace-step/ACE-Step/blob/main/LICENSE | s.d. | 2026-09-28 | officiel | élevée |
| S30 | DEV Community — ACE-Step 1.5: The Complete 2026 Guide | https://dev.to/czmilo/ace-step-15-the-complete-2026-guide-to-open-source-ai-music-generation-522e | 2026 | 2026-09-28 | praticien | moyenne |
| S31 | Hugging Face — stabilityai/stable-audio-open-1.0 — LICENSE.md | https://huggingface.co/stabilityai/stable-audio-open-1.0/blob/main/LICENSE.md | s.d. | 2026-09-28 | officiel | élevée |
| S32 | Hugging Face — facebook/musicgen-large | https://huggingface.co/facebook/musicgen-large | 2023-06-08 | 2026-09-28 | officiel | élevée |
| S33 | GitHub — multimodal-art-projection/YuE — LICENSE | https://github.com/multimodal-art-projection/YuE/blob/main/LICENSE | 2025-01-30 | 2026-09-28 | officiel | élevée |
| S34 | GitHub — ASLP-lab/DiffRhythm (README, licence) | https://github.com/ASLP-lab/DiffRhythm | s.d. | 2026-09-28 | officiel | élevée |
| S35 | GitHub — tencent-ailab/SongGeneration (README) | https://github.com/tencent-ailab/SongGeneration | 2026-03-01 | 2026-09-28 | officiel | moyenne |
| S36 | Hugging Face — google/magenta-realtime | https://huggingface.co/google/magenta-realtime | s.d. | 2026-09-28 | officiel | élevée |
| S37 | Google Magenta — Magenta RealTime (page officielle) | https://magenta.withgoogle.com/magenta-realtime | 2026-06-04 | 2026-09-28 | officiel | élevée |
| S38 | YouTube Help — À propos de la bibliothèque audio | https://support.google.com/youtube/answer/3376882 | s.d. | 2026-09-28 | officiel | élevée |
| S39 | GitHub — FluidSynth/fluidsynth wiki — LicensingFAQ | https://github.com/FluidSynth/fluidsynth/wiki/LicensingFAQ | s.d. | 2026-09-28 | officiel | moyenne |
| S40 | GitHub — csteinmetz1/pyloudnorm | https://github.com/csteinmetz1/pyloudnorm | s.d. | 2026-09-28 | officiel | élevée |
| S41 | GitHub — hkchengrex/MMAudio (README, licence) | https://github.com/hkchengrex/MMAudio | s.d. | 2026-09-28 | officiel | élevée |
| S42 | Hugging Face — hkchengrex/MMAudio — README.md | https://huggingface.co/hkchengrex/MMAudio/blob/main/README.md | s.d. | 2026-09-28 | officiel | élevée |
| S43 | Hugging Face — tencent/HunyuanVideo-Foley — LICENSE | https://huggingface.co/tencent/HunyuanVideo-Foley/blob/main/LICENSE | s.d. | 2026-09-28 | officiel | élevée |
| S44 | Hugging Face — tencent/HunyuanVideo-Foley (fiche modèle) | https://huggingface.co/tencent/HunyuanVideo-Foley | 2025-08-28 | 2026-09-28 | officiel | élevée |
| S45 | GitHub — QwenAudio/ThinkSound (README, licence) | https://github.com/QwenAudio/ThinkSound | s.d. | 2026-09-28 | officiel | moyenne |
| S46 | GitHub — haoheliu/AudioLDM2 — LICENSE | https://github.com/haoheliu/AudioLDM2/blob/main/LICENSE | s.d. | 2026-09-28 | officiel | élevée |
| S47 | Hugging Face — declare-lab/tango | https://huggingface.co/declare-lab/tango | s.d. | 2026-09-28 | officiel | élevée |
| S48 | Sonniss — The License (#GameAudioGDC Bundle) | https://sonniss.com/gdc-bundle-license/ | s.d. | 2026-09-28 | officiel | élevée |
| S49 | Freesound — Help / FAQ | https://freesound.org/help/faq/ | s.d. | 2026-09-28 | officiel | élevée |
| S50 | GitHub — SYSTRAN/faster-whisper | https://github.com/SYSTRAN/faster-whisper | s.d. | 2026-09-28 | officiel | élevée |
| S51 | Hugging Face — openai/whisper-large-v3 | https://huggingface.co/openai/whisper-large-v3 | 2022-12-06 | 2026-09-28 | officiel | élevée |
| S52 | GitHub — m-bain/whisperX | https://github.com/m-bain/whisperX | s.d. | 2026-09-28 | officiel | élevée |
| S53 | Hugging Face — nvidia/canary-1b-v2 | https://huggingface.co/nvidia/canary-1b-v2 | 2025-08-14 | 2026-09-28 | officiel | élevée |
| S54 | NVIDIA — Nemotron Speech (perspectives.nvidia.com, FAQ modèles ASR) | https://perspectives.nvidia.com/nemotron-speech/task/faq/what-are-the-most-production-ready-open-speech-recognition-models-for-european-l/ | 2026 | 2026-09-28 | officiel | élevée |
| S55 | FFmpeg — Documentation des filtres audio (loudnorm) | https://ffmpeg.org/ffmpeg-filters.html#loudnorm | s.d. | 2026-09-28 | officiel | élevée |
| S56 | EBU Technology & Innovation — R 128 (publication officielle) | https://tech.ebu.ch/publications/r128 | 2023-11 | 2026-09-28 | officiel | élevée |
| S57 | AudioForgePro — YouTube LUFS Normalization Guide | https://audioforgepro.com/blog/youtube-lufs-normalization-guide | 2026 | 2026-09-28 | praticien | moyenne |
| S58 | Mixing and Mastering AI — TikTok and Reels Loudness: The −14 LUFS Target Explained | https://mixingandmastering.ai/blog/lufs-for-tiktok-and-reels | 2026 | 2026-09-28 | praticien | moyenne |
| S59 | Critical Listening Lab — YouTube Loudness Normalization | https://www.criticallisteninglab.com/en/learn/loudness/youtube | s.d. | 2026-09-28 | praticien | moyenne |
