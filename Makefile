.PHONY: test examples cinema cinema-open cinema-test cinema-stop cinema-repair ci-cinema-smoke

CINEMA_MODEL ?=
CINEMA_CAPSULE ?= scientific_calc
CINEMA_PATH ?= examples/web_app_calculator/workspace
CINEMA_GOAL ?= wdrożenie kalkulatora naukowego na bazie aktualnego
CINEMA_MODEL_ARG = $(if $(strip $(CINEMA_MODEL)),LLM_MODEL="$(CINEMA_MODEL)",)

test:
	pytest -q

examples:
	python examples/run_examples.py

cinema:
	uv sync --quiet
	@$(CINEMA_MODEL_ARG) uv run nexu capsule iterate $(CINEMA_CAPSULE) --steps 1 --goal "$(CINEMA_GOAL)" --cinema --path $(CINEMA_PATH)

cinema-open:
	@url="$$( uv sync --quiet; $(CINEMA_MODEL_ARG) uv run nexu capsule iterate $(CINEMA_CAPSULE) --steps 1 --goal "$(CINEMA_GOAL)" --cinema --path $(CINEMA_PATH) 2>&1 | tee /tmp/nexu-cinema-open.log | sed -n 's/.*Live HTTP Server started for Cinema Player: //p' | tail -1)"; \
	if [ -z "$$url" ]; then \
		echo "Could not detect Cinema URL. See /tmp/nexu-cinema-open.log"; \
		exit 1; \
	fi; \
	echo "Opening $$url"; \
	( xdg-open "$$url" >/dev/null 2>&1 || sensible-browser "$$url" >/dev/null 2>&1 || firefox "$$url" >/dev/null 2>&1 || google-chrome "$$url" >/dev/null 2>&1 || true )

cinema-test: cinema
	pytest -q

cinema-stop:
	@pkill -f '/cinema/server.py' 2>/dev/null && echo 'Stopped cinema server.py process(es).' || echo 'No cinema server.py processes found.'

cinema-repair:
	@uv run python -c "from pathlib import Path; from nexu.cinema_scripts import repair_cinema_html_files; d=Path('$(CINEMA_PATH)')/'.nexu/capsules/$(CINEMA_CAPSULE)/cinema'; n=repair_cinema_html_files(d); print(f'Repaired {n} HTML file(s) in {d}')"

ci-cinema-smoke:
	@./scripts/ci-cinema-smoke.sh
