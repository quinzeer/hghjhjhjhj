# Journal de progression

Entrées datées, la plus récente en haut. Chaque affirmation « fait » est suivie de la commande qui le prouve et de sa sortie.

## 2026-09-28 — Session 1 : lancement de la phase 0

### Fait
- `docs/MISSION.md` enregistré mot pour mot, commit `docs: mission initiale` (c77e887).
  Preuve : `sha256sum docs/MISSION.md` → `45eb93fad125d40b…` (217 lignes).
- Skill `scenariste-youtube` trouvé dans la session et lu (36 640 octets). **Non copié** dans le dépôt : le dépôt est public (NEEDS_HUMAN H1).
- Format des sous-agents vérifié dans la documentation officielle (code.claude.com/docs/en/sub-agents, consultée le 2026-09-28) :
  champs `name`, `description` obligatoires ; `tools`, `model` (`sonnet`, `opus`, `haiku`, `fable`, ID complet ou `inherit`) facultatifs.
  9 fichiers créés ; frontmatter validé par un parseur YAML.
- Écarts relevés dans l'outillage : `claude --help` (v2.1.283) n'affiche pas `--max-turns` ; `--json-schema` existe ; `--bare` n'utilise pas l'auth OAuth. Vérification détaillée confiée à `docs/research/apis.md`.
- `tools/verify_phase0.py` (porte de phase 0, stdlib) + `tools/doctor.py` + 22 tests.
- 9 recherches lancées en parallèle (rôle `researcher`, modèle sonnet) : platform-policies, apis, video-image-models, audio-models, craft, economics, infra, concepts lot A (C01-C06), concepts lot B (C07-C12).
  Les définitions `.claude/agents/` créées pendant la session ne sont pas encore chargées : les recherches tournent sur l'agent générique avec le rôle `researcher` injecté dans la consigne.
- Paramètres du §0 vides → hypothèses prudentes dans `docs/PARAMETERS.md`, actions dans `docs/NEEDS_HUMAN.md` (H1-H12).

### Preuves
```
$ make doctor
  · claude: présent
  · ffmpeg: absent (requis plus tard sur la machine GPU)
  · ffprobe: absent (requis plus tard sur la machine GPU)
  · docker: présent
  · nvidia-smi: absent (requis plus tard sur la machine GPU)
  · CLAUDE_CODE_OAUTH_TOKEN: absent (requis sur la machine d'exécution, phase 2)
doctor : OK

$ make test
22 passed in 0.23s

$ make lint
All checks passed!

$ make verify-phase-0   # attendu en échec tant que les notes et ADR ne sont pas livrés
verify-phase-0 : 2/13 contrôles OK, 11 en échec
```
