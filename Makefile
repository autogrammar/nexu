.PHONY: test examples cinema cinema-open cinema-test

CINEMA_MODEL ?=
CINEMA_CAPSULE ?= scientific_calc
CINEMA_PATH ?= examples/web_app_calculator/workspace
CINEMA_GOAL ?= wdrożenie kalkulatora naukowego na bazie aktualnego

test:
	pytest -q

examples:
	python examples/run_examples.py

cinema:
	@if [ "$(origin CINEMA_MODEL)" = "command line" ] || [ "$(origin CINEMA_MODEL)" = "environment" ]; then \
		LLM_MODEL="$(CINEMA_MODEL)" uv run nexu capsule iterate $(CINEMA_CAPSULE) --steps 1 --goal "$(CINEMA_GOAL)" --cinema --path $(CINEMA_PATH); \
	else \
		uv run nexu capsule iterate $(CINEMA_CAPSULE) --steps 1 --goal "$(CINEMA_GOAL)" --cinema --path $(CINEMA_PATH); \
	fi

cinema-open:
	@url="$$(LLM_MODEL=$(CINEMA_MODEL) uv run nexu capsule iterate $(CINEMA_CAPSULE) --steps 1 --goal "$(CINEMA_GOAL)" --cinema --path $(CINEMA_PATH) 2>&1 | tee /tmp/nexu-cinema-open.log | sed -n 's/.*Live HTTP Server started for Cinema Player: //p' | tail -1)"; \
	if [ -z "$$url" ]; then \
		echo "Could not detect Cinema URL. See /tmp/nexu-cinema-open.log"; \
		exit 1; \
	fi; \
	echo "Opening $$url"; \
	( xdg-open "$$url" >/dev/null 2>&1 || sensible-browser "$$url" >/dev/null 2>&1 || firefox "$$url" >/dev/null 2>&1 || google-chrome "$$url" >/dev/null 2>&1 || true )

cinema-test: cinema
	pytest -q
