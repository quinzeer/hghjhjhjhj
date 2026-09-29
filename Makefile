# Studio — commandes de construction. `make help` pour la liste.
PY ?= python3
UV ?= uv

.PHONY: help doctor doctor-execution verify-phase-0 verify-phase-0-online verify-phase-1 e2e-dry test lint fmt check

help: ## Liste des commandes
	@grep -E '^[a-zA-Z0-9_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-18s %s\n", $$1, $$2}'

doctor: ## Santé de l'environnement ; échoue si ANTHROPIC_API_KEY est définie ou si un réglage Claude Code contourne l'abonnement
	@if command -v $(UV) >/dev/null 2>&1; then $(UV) run python tools/doctor.py; else $(PY) tools/doctor.py; fi

doctor-execution: ## Santé de la machine GPU : ffmpeg, Docker, les 4 cartes (STUDIO_GPU_COUNT), CLAUDE_CODE_OAUTH_TOKEN
	@if command -v $(UV) >/dev/null 2>&1; then $(UV) run python tools/doctor.py --role execution; else $(PY) tools/doctor.py --role execution; fi

verify-phase-0: ## Porte de sortie de la phase 0 (code 0 seulement si tous les critères sont remplis)
	@$(PY) tools/verify_phase0.py

verify-phase-0-online: ## Idem + re-mesure des outliers par l'API (YOUTUBE_API_KEY) : obligatoire avant de clore la phase
	@$(PY) tools/verify_phase0.py --online

verify-phase-1: ## Porte de sortie de la phase 1 (lint, tests + couverture du cœur, e2e à blanc x2, ffprobe)
	@$(PY) tools/verify_phase1.py

e2e-dry: ## Parcours à blanc via les mocks : un Short 1080x1920 et un long 1920x1080 dans var/e2e/
	@$(UV) run studio run --channel channel-a --format short --dry-run --out var/e2e
	@$(UV) run studio run --channel channel-a --format long --dry-run --out var/e2e

test: ## Tests (unitaires ; intégration Postgres si STUDIO_TEST_PG_URL est définie)
	@$(UV) run --group dev pytest

lint: ## ruff (lint + format vérifié) + mypy strict sur studio/
	@$(UV) run --group dev ruff check tools tests studio
	@$(UV) run --group dev ruff format --check tools tests studio
	@$(UV) run --group dev mypy

fmt: ## Formate le code
	@$(UV) run --group dev ruff format tools tests studio

check: doctor lint test ## Tout ce qui doit être vert avant une PR
