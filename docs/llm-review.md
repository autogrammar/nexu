# LLM review and handoff

nexu 0.4 adds a review layer around capsule iterations. The goal is not to let an LLM approve its own work. The goal is to create a structured evidence packet that a human, CI job or optional external reviewer can inspect.

## Offline by default

```bash
nexu capsule review menu-icons
```

This creates:

```text
.nexu/capsules/menu-icons/reviews/review.yaml
.nexu/capsules/menu-icons/reviews/review.md
.nexu/capsules/menu-icons/reviews/review-prompt.md
```

The deterministic decision is based on nexu verification gates:

- `pass` -> `approve`,
- `partial` -> `needs_revision`,
- `fail` -> `reject`.

The review packet includes verification, diff from capsule baseline, source drift, blueprint, prompt export and a strict JSON response schema for optional LLM review.

## Optional LiteLLM/OpenRouter review

Network calls are disabled unless explicitly enabled.

```yaml
llm:
  provider: openrouter
  model: openrouter/deepseek/deepseek-v4-pro
  base_url: https://openrouter.ai/api/v1
  api_key_env: OPENROUTER_API_KEY
  allow_network_calls: true
```

Then run:

```bash
nexu capsule review menu-icons --call-llm
```

The LLM must return JSON matching the review schema. Invalid JSON fails the review call instead of being silently accepted.

## Portable bundle

```bash
nexu capsule bundle menu-icons
```

The bundle ZIP contains capsule context, prompts, evidence, reports, contracts, blueprints and optionally copied source files. This is useful when the reviewing agent cannot access the whole repository.
