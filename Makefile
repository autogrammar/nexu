.PHONY: test examples docs-links quality quality-strict quality-intract quality-redup cinema cinema-open cinema-test cinema-stop cinema-restart cinema-repair ci-cinema-smoke

CINEMA_MODEL ?=
CINEMA_CAPSULE ?= scientific_calc
CINEMA_PATH ?= examples/web_app_calculator/workspace
CINEMA_GOAL ?= wdrożenie kalkulatora naukowego na bazie aktualnego
CINEMA_MODEL_ARG = $(if $(strip $(CINEMA_MODEL)),LLM_MODEL="$(CINEMA_MODEL)",)

test:
	pytest -q

examples:
	python examples/run_examples.py

docs-links:
	python scripts/check-doc-links.py .

quality-intract:
	intract check src --format text
	intract coverage src

quality-redup:
	redup scan src --format toon --min-lines 8

quality: test docs-links quality-intract quality-redup
	ruff check \
		src/nexu/cinema.py \
		src/nexu/cinema_server.py \
		src/nexu/cinema_baseline_contracts.py \
		src/nexu/cinema_goal_contracts.py \
		src/nexu/cinema_html.py \
		src/nexu/cinema_html_validate.py \
		src/nexu/cinema_llm_contracts.py \
		src/nexu/cinema_markpact.py \
		src/nexu/cinema_project_imports.py \
		src/nexu/cinema_projects.py \
		src/nexu/cinema_scripts.py \
		src/nexu/cinema_publish.py \
		src/nexu/cinema_offline_options.py \
		src/nexu/cinema_options_cache.py \
		src/nexu/cinema_ui_patch.py \
		src/nexu/fast_delivery/__init__.py \
		src/nexu/fast_delivery/context.py \
		src/nexu/fast_delivery/options.py \
		src/nexu/fast_delivery/router.py \
		src/nexu/intract.py \
		src/nexu/verify.py \
		src/nexu/intract_adapter.py \
		tests/test_cinema_server.py \
		tests/test_cinema_baseline_contracts.py \
		tests/test_cinema_goal_contracts.py \
		tests/test_cinema_markpact.py \
		tests/test_cinema_project_imports.py \
		tests/test_cinema_projects.py \
		tests/test_cinema_scripts.py \
		tests/test_cinema_publish.py \
		tests/test_cinema_offline_options.py \
		tests/test_cinema_options_cache.py \
		tests/test_cinema_ui_patch.py \
		tests/test_fast_delivery.py

quality-strict:
	pytest -q
	ruff check src tests --statistics
	intract check . --format text
	redup scan src --format toon

cinema:
	uv sync --quiet
	@$(CINEMA_MODEL_ARG) uv run nexu capsule iterate $(CINEMA_CAPSULE) --steps 1 --goal "$(CINEMA_GOAL)" --cinema --path $(CINEMA_PATH)

cinema-open:
	@url="$$( uv sync --quiet; $(CINEMA_MODEL_ARG) uv run nexu capsule iterate $(CINEMA_CAPSULE) --steps 1 --goal "$(CINEMA_GOAL)" --cinema --path $(CINEMA_PATH) 2>&1 | tee /tmp/nexu-cinema-open.log | sed -n 's/.*Live HTTP Server started for Nexu: //p' | tail -1)"; \
	if [ -z "$$url" ]; then \
		echo "Could not detect Nexu URL. See /tmp/nexu-cinema-open.log"; \
		exit 1; \
	fi; \
	echo "Opening $$url"; \
	( xdg-open "$$url" >/dev/null 2>&1 || sensible-browser "$$url" >/dev/null 2>&1 || firefox "$$url" >/dev/null 2>&1 || google-chrome "$$url" >/dev/null 2>&1 || true )

cinema-test: cinema
	pytest -q

cinema-stop:
	@pkill -f '[/]cinema/server.py' >/dev/null 2>&1 || true
	@echo 'Stopped cinema server.py process(es) if any were running.'

cinema-restart:
	@$(MAKE) cinema-stop
	@$(MAKE) cinema

cinema-repair:
	@uv run python -c "from pathlib import Path; from nexu.cinema_scripts import repair_cinema_html_files; d=Path('$(CINEMA_PATH)')/'.nexu/capsules/$(CINEMA_CAPSULE)/cinema'; n=repair_cinema_html_files(d); print(f'Repaired {n} HTML file(s) in {d}')"

ci-cinema-smoke:
	@./scripts/ci-cinema-smoke.sh
