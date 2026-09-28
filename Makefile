# Studio — commandes de construction. `make help` pour la liste.
PY ?= python3
UV ?= uv

.PHONY: help doctor verify-phase-0 verify-phase-0-online test lint fmt check

help: ## Liste des commandes
	@grep -E '^[a-zA-Z0-9_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-18s %s\n", $$1, $$2}'

doctor: ## Santé de l'environnement ; échoue si ANTHROPIC_API_KEY est définie
	@$(PY) tools/doctor.py

verify-phase-0: ## Porte de sortie de la phase 0 (code 0 seulement si tous les critères sont remplis)
	@$(PY) tools/verify_phase0.py

verify-phase-0-online: ## Idem + re-mesure des outliers par l'API (YOUTUBE_API_KEY) : obligatoire avant de clore la phase
	@$(PY) tools/verify_phase0.py --online

test: ## Tests unitaires (outillage de vérification en phase 0)
	@$(UV) run --group dev pytest

lint: ## ruff (lint + format vérifié)
	@$(UV) run --group dev ruff check tools tests
	@$(UV) run --group dev ruff format --check tools tests

fmt: ## Formate le code
	@$(UV) run --group dev ruff format tools tests

check: doctor lint test ## Tout ce qui doit être vert avant une PR
