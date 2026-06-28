#!/home/tom/github/semcod/nexu/.venv/bin/python3
import http.server
import socketserver
import sys
import os
import re
import json
import csv
import base64
import mimetypes
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from datetime import datetime
from threading import Lock

# Force correct MIME types and UTF-8 charsets for clean encoding
mimetypes.add_type("text/html; charset=utf-8", ".html")
mimetypes.add_type("application/javascript; charset=utf-8", ".js")
mimetypes.add_type("text/css; charset=utf-8", ".css")

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
BIND_HOST = os.environ.get("CINEMA_BIND_HOST", "127.0.0.1")
DIRECTORY = Path(__file__).parent.absolute()
LOG_CSV = DIRECTORY / "log.csv"
POLICY_SNAPSHOT_PATH = DIRECTORY / "intract_policy.json"
POLICY_LEDGER_PATH = DIRECTORY / "intract_policy_ledger.json"
LLM_TRACE_DIR = DIRECTORY / "llm_traces"
LLM_TRACE_INDEX = LLM_TRACE_DIR / "index.json"
LLM_TRACE_LOCK = Lock()

WORKSPACE_PATH = '/home/tom/github/semcod/nexu/examples/web_app_calculator'
ROOT_PATH = Path(WORKSPACE_PATH).absolute()
CAPSULE_NAME = 'web_app_calculator'
SYS_EXE = '/home/tom/github/semcod/nexu/.venv/bin/python3'
ALLOW_NETWORK_CALLS = False
API_KEY_ENV = 'OPENROUTER_API_KEY'
DEFAULT_MODEL = 'openrouter/deepseek/deepseek-v4-pro'
MAX_TOKENS = int(os.environ.get("CINEMA_MAX_TOKENS", 20480))
OPTION_GENERATION_MODE = os.environ.get(
    "CINEMA_OPTION_GENERATION_MODE",
    'batch',
).strip().lower()
FAST_SCOPE_OPTIONS = True
_fast_scope_env = os.environ.get("CINEMA_FAST_SCOPE_OPTIONS", "").strip().lower()
if _fast_scope_env:
    FAST_SCOPE_OPTIONS = _fast_scope_env not in {"0", "false", "no", "off"}
LLM_PATCH_OPTIONS = True
_llm_patch_env = os.environ.get("CINEMA_LLM_PATCH_OPTIONS", "").strip().lower()
if _llm_patch_env:
    LLM_PATCH_OPTIONS = _llm_patch_env not in {"0", "false", "no", "off"}
OPTIONS_CACHE = True
_options_cache_env = os.environ.get("CINEMA_OPTIONS_CACHE", "").strip().lower()
if _options_cache_env:
    OPTIONS_CACHE = _options_cache_env not in {"0", "false", "no", "off"}
OPTIONS_CACHE_DIR = DIRECTORY / "cache" / "options"
FORCE_LLM = False
_force_llm_env = os.environ.get("CINEMA_FORCE_LLM", "").strip().lower()
if _force_llm_env:
    FORCE_LLM = _force_llm_env in {"1", "true", "yes", "on"}
DEFAULT_MARKPACT_CONTEXT_CHARS = 4000
DEFAULT_MARKPACT_CONTEXT_MODE = 'summary'
DEFAULT_HTML_CONTEXT_CHARS = 8000
DEFAULT_LLM_TRACE_KEEP = 80


def _load_cinema_ui_profile() -> dict:
    """Active example project kind drives LLM/offline semantics."""
    active: dict = {}
    try:
        import nexu_hooks

        raw = nexu_hooks.active_project()
        if isinstance(raw, dict):
            active = raw
    except Exception:
        active = {}
    try:
        from nexu.cinema_scope import load_cinema_ui_profile

        return load_cinema_ui_profile(active, DIRECTORY)
    except Exception:
        kind = str(active.get("kind") or "").lower()
        title = str(active.get("title") or active.get("id") or "").strip()
        return {"kind": kind, "title": title, "ui_type": "web", "active": active}


def _goal_entry_kwargs(data: dict) -> dict:
    """Optional scope fields from cinema_player goal form."""
    out: dict = {}
    for key in (
        "focus_scope",
        "focus_scope_label",
        "current_state",
        "expected_version",
        "project_context",
    ):
        val = str(data.get(key, "") or "").strip()
        if val:
            out[key] = val
    return out


def _llm_prompt_intro(profile: dict) -> str:
    ui_type = profile.get("ui_type") or "web"
    title = profile.get("title") or "the active project"
    if profile.get("llm_context_mode") == "patch":
        return (
            f"You are patching an imported web page for {title}. "
            "Below is compact visual CSS and an HTML structure outline — not the full live page."
        )
    if ui_type == "dashboard":
        return (
            f"You are evolving a web dashboard/analytics UI for {title}. "
            "Below is the current HTML."
        )
    if ui_type == "calculator":
        return "You are evolving a calculator web UI. Below is the current HTML."
    return f"You are evolving a web application UI for {title}. Below is the current HTML."


def _llm_prompt_rules(profile: dict) -> str:
    ui_type = profile.get("ui_type") or "web"
    shared = [
        "1. Return ONLY the complete evolved HTML document, nothing else.",
        "2. Keep a valid HTML5 shell: <!DOCTYPE html>, <html>, <head> with all CSS in "
        "<style> tags inside head, and <body> with the preserved app structure.",
        "3. Preserve elements marked KEEP - do not change their function.",
    ]
    if ui_type == "calculator":
        return "\n".join(
            shared
            + [
                "4. For DELETE elements: remove ONLY those buttons from the HTML — do not remove anything else.",
                "5. Do NOT simplify the calculator or drop scientific buttons unless they are in the DELETE list.",
                "6. Improve visual design only when explicitly asked in hints; otherwise preserve layout.",
                "7. Keep the same CSS class names (.btn, .btn-sci, .btn-sci-excess, .btn-op, .screen) so buttons work.",
                "8. Do NOT include any <script> tags — runtime is injected by Nexu after generation.",
                "9. Each option variant must be visually and functionally distinct.",
                "10. Use id=screen for the display and class=btn / btn-sci / btn-op on buttons.",
                "11. Domain-specific controls from the current HTML or KEEP list are mandatory "
                "unless they appear under DELETE.",
                "12. Respect Intract baseline contracts (calc.app.kind, display, keypad) — goal contracts "
                "only ADD traits; never remove baseline structure unless DELETE list says so.",
                "13. The element #screen is an output display only: put only a number, formula, "
                "or current expression there. Do not put the app title, goal, variant name, "
                "or text like 'Chemical & scientific keypad evolution' inside #screen; place "
                "that title above or below the display.",
                "14. For #orientation scope: preserve every button id/class and calculator DOM; "
                "change only layout CSS (grid/flex direction, panel order, aspect ratio).",
            ]
        )
    base = "\n".join(
        shared
        + [
            "4. For DELETE elements: remove ONLY those marked panels/cards/controls — do not strip unrelated layout.",
            "5. Do NOT replace the current application type with a different application type unless the goal explicitly asks.",
            "6. Improve visual design only when explicitly asked in hints; otherwise preserve layout.",
            "7. Keep data-nexu-target, id=btn-*, and existing CSS class names on selectable widgets.",
            "8. Do NOT include any <script> tags — runtime is injected by Nexu after generation.",
            "9. Each option variant must be visually and functionally distinct (overview → workflow → expanded).",
            "10. Preserve existing shell/card/control patterns unless the selected scope requires changing them.",
            "11. Align labels and visible data with the project goal and current project metadata.",
            "12. Respect Intract baseline contracts — goal extensions only ADD traits; never regress unless DELETE says so.",
        ]
    )
    if profile.get("llm_context_mode") == "patch":
        from nexu.cinema_http_preprocess import http_patch_llm_rules

        return base + "\n" + http_patch_llm_rules()
    return base


def _llm_communication_contract_block(
    *,
    ui_type: str,
    focus_scope: str,
    variant_label: str,
    keep_els: list,
    delete_els: list,
    project_goal: str = "",
    current_state: str = "",
    expected_version: str = "",
    element_hints: list | None = None,
) -> str:
    try:
        from nexu.cinema_llm_contracts import build_llm_contract_block

        return build_llm_contract_block(
            ui_type=ui_type,
            focus_scope=focus_scope,
            variant_label=variant_label,
            keep_els=keep_els,
            delete_els=delete_els,
            project_goal=project_goal,
            current_state=current_state,
            expected_version=expected_version,
            element_hints=element_hints,
        )
    except Exception:
        return (
            "- @intract.v1 id:llm.cinema.html scope:llm_call "
            "intent:generate:complete_html priority:1 domain:llm.ui "
            "input:current_html,goal,ui_constraints output:complete_html "
            "effect:read,generate forbid:script_tags,secret_leak "
            "require:complete_html_document validate:html_document,no_script_tags"
        )


ENV_PATH_CANDIDATES = [
    ROOT_PATH / ".env",
    ROOT_PATH.parent / ".env",
    ROOT_PATH.parent.parent / ".env",
    ROOT_PATH.parent.parent.parent / ".env",
    DIRECTORY / ".env",
]


_MODEL_ENV_KEYS = frozenset({"LLM_MODEL", "NEXU_MODEL", "nexu_MODEL"})


def _load_env_file(path: Path, override_keys=None) -> None:
    override_keys = override_keys or frozenset()
    if not path.exists():
        return
    try:
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and (key not in os.environ or key in override_keys):
                os.environ[key] = value
    except Exception:
        return


def _load_all_env() -> None:
    for index, env_path in enumerate(ENV_PATH_CANDIDATES):
        _load_env_file(env_path, _MODEL_ENV_KEYS if index else frozenset())


def _resolve_model() -> str:
    _load_all_env()
    return (
        os.environ.get("LLM_MODEL")
        or os.environ.get("NEXU_MODEL")
        or os.environ.get("nexu_MODEL")
        or DEFAULT_MODEL
    )


def _llm_network_allowed() -> bool:
    """Read llm.allow_network_calls from workspace nexu.yaml (not startup snapshot)."""
    try:
        from nexu.cinema_llm import _cached_config

        return bool(_cached_config(ROOT_PATH).llm.allow_network_calls)
    except Exception:
        return ALLOW_NETWORK_CALLS


def _litellm_available() -> bool:
    try:
        from nexu.cinema_llm import _litellm_completion

        _litellm_completion()
        return True
    except Exception:
        return False


def _llm_status_payload() -> dict:
    _ensure_api_key_env()
    try:
        from nexu.cinema_llm import _cached_config

        config = _cached_config(ROOT_PATH)
        llm = config.llm
        provider = str(llm.provider)
        model = _resolve_model() or str(llm.model)
        api_key_env = str(llm.api_key_env)
        allow_network = bool(llm.allow_network_calls)
        base_url = str(llm.base_url)
        temperature = float(llm.temperature)
        timeout = int(llm.timeout)
    except Exception:
        provider = "openrouter"
        model = _resolve_model()
        api_key_env = API_KEY_ENV
        allow_network = bool(ALLOW_NETWORK_CALLS)
        base_url = ""
        temperature = 0.0
        timeout = 0
    return {
        "provider": provider,
        "model": model,
        "api_key_env": api_key_env,
        "api_key_present": bool(os.environ.get(api_key_env, "")),
        "allow_network_calls": allow_network,
        "litellm_available": _litellm_available(),
        "base_url": base_url,
        "temperature": temperature,
        "timeout": timeout,
        "cinema": {
            "markpact_context_chars": int(
                os.environ.get("CINEMA_MARKPACT_CONTEXT_CHARS", str(DEFAULT_MARKPACT_CONTEXT_CHARS))
            ),
            "markpact_context_mode": os.environ.get(
                "CINEMA_MARKPACT_CONTEXT_MODE",
                DEFAULT_MARKPACT_CONTEXT_MODE,
            ),
            "html_context_chars": int(
                os.environ.get("CINEMA_HTML_CONTEXT_CHARS", str(DEFAULT_HTML_CONTEXT_CHARS))
            ),
            "max_tokens": MAX_TOKENS,
            "option_generation_mode": OPTION_GENERATION_MODE,
            "fast_scope_options": FAST_SCOPE_OPTIONS,
            "llm_patch_options": LLM_PATCH_OPTIONS,
            "force_llm": FORCE_LLM,
            "options_cache": OPTIONS_CACHE,
            "llm_trace_keep": int(
                os.environ.get("CINEMA_LLM_TRACE_KEEP", str(DEFAULT_LLM_TRACE_KEEP))
            ),
        },
    }


def _trace_slug(value: str) -> str:
    from nexu.cinema_traces import trace_slug

    return trace_slug(value)


def _read_trace_index() -> list[dict]:
    from nexu.cinema_traces import read_trace_index

    return read_trace_index(LLM_TRACE_INDEX)


def _write_llm_trace(
    *,
    label: str,
    prompt: str,
    output: str = "",
    error: str = "",
    model: str = "",
    duration_ms: int = 0,
) -> None:
    from nexu.cinema_traces import write_llm_trace

    redact_values: tuple[str, ...] = ()
    key = os.environ.get(API_KEY_ENV, "")
    if key:
        redact_values = (key,)
    write_llm_trace(
        LLM_TRACE_DIR,
        LLM_TRACE_INDEX,
        LLM_TRACE_LOCK,
        label=label,
        prompt=prompt,
        output=output,
        error=error,
        model=model or _resolve_model(),
        duration_ms=duration_ms,
        keep=int(os.environ.get("CINEMA_LLM_TRACE_KEEP", str(DEFAULT_LLM_TRACE_KEEP))),
        redact_values=redact_values,
    )


def _list_llm_traces(project_id: str = "") -> dict:
    from nexu.cinema_traces import list_llm_traces

    payload = list_llm_traces(LLM_TRACE_DIR)
    project_id = str(project_id or "").strip()
    if not project_id:
        return payload
    try:
        import nexu_hooks
    except ImportError:
        return payload
    filtered = nexu_hooks.imported_llm_log(project_id)
    if filtered.get("error"):
        return payload
    return {"traces": filtered.get("traces") or [], "project_id": project_id}


def _path_segments(path: str) -> list[str]:
    from urllib.parse import unquote, urlparse

    return [
        unquote(segment)
        for segment in urlparse(path).path.strip("/").split("/")
        if segment
    ]


def _parse_imported_project_route(path: str) -> tuple[str, str] | None:
    parts = _path_segments(path)
    if len(parts) >= 4 and parts[0] == "projects" and parts[1] == "imported":
        action = parts[3]
        if action in ("markpact", "llm-log"):
            return parts[2], action
    return None


def _delete_imported_project(project_id: str) -> dict:
    try:
        import nexu_hooks
    except ImportError:
        return {"error": "nexu_hooks.py missing; regenerate cinema (make cinema)"}
    return nexu_hooks.delete_imported(project_id)


def _delete_project(project_id: str) -> dict:
    try:
        import nexu_hooks
    except ImportError:
        return {"error": "nexu_hooks.py missing; regenerate cinema (make cinema)"}
    return nexu_hooks.delete_workspace_project(project_id)


def _imported_markpact(project_id: str) -> dict:
    try:
        import nexu_hooks
    except ImportError:
        return {"error": "nexu_hooks.py missing; regenerate cinema (make cinema)"}
    return nexu_hooks.imported_markpact(project_id)


def _imported_llm_log(project_id: str) -> dict:
    try:
        import nexu_hooks
    except ImportError:
        return {"error": "nexu_hooks.py missing; regenerate cinema (make cinema)"}
    return nexu_hooks.imported_llm_log(project_id)


def _read_llm_trace(trace_id: str) -> dict:
    from nexu.cinema_traces import read_llm_trace

    return read_llm_trace(LLM_TRACE_DIR, trace_id)


def _ensure_api_key_env() -> None:
    if os.environ.get(API_KEY_ENV):
        return
    _load_all_env()
    if os.environ.get(API_KEY_ENV):
        return


def _strip_markdown_fences(text: str) -> str:
    raw = text.strip()
    if raw.startswith("```"):
        lines = raw.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        return chr(10).join(lines).strip()
    return raw


def _extract_html_document(text: str) -> str:
    cleaned = _strip_markdown_fences(text)
    match = re.search(r"<!DOCTYPE\s+html[\s\S]*?</html>", cleaned, flags=re.I)
    if match:
        return match.group(0).strip()
    match = re.search(r"<html[\s\S]*?</html>", cleaned, flags=re.I)
    if match:
        return "<!DOCTYPE html>\n" + match.group(0).strip()
    return cleaned


def _compact_html_for_llm(html: str) -> str:
    limit = int(os.environ.get("CINEMA_HTML_CONTEXT_CHARS", str(DEFAULT_HTML_CONTEXT_CHARS)))
    from nexu.fast_delivery import compact_html_for_llm

    return compact_html_for_llm(html, limit=limit)


def _effective_markpact_mode(focus_scope: str, project_kind: str) -> str:
    default = os.environ.get(
        "CINEMA_MARKPACT_CONTEXT_MODE",
        DEFAULT_MARKPACT_CONTEXT_MODE,
    ).strip().lower()
    env_off = os.environ.get("CINEMA_MARKPACT_OFF_FOR_SCOPE", "").strip().lower()
    from nexu.fast_delivery import effective_markpact_mode

    return effective_markpact_mode(
        focus_scope,
        project_kind,
        default_mode=default,
        env_off=env_off,
    )


def _compact_markpact_for_llm(markdown: str, *, mode: str | None = None) -> str:
    effective_mode = (
        str(mode or "").strip().lower()
        or os.environ.get(
            "CINEMA_MARKPACT_CONTEXT_MODE",
            DEFAULT_MARKPACT_CONTEXT_MODE,
        ).strip().lower()
    )
    limit = int(os.environ.get("CINEMA_MARKPACT_CONTEXT_CHARS", str(DEFAULT_MARKPACT_CONTEXT_CHARS)))
    from nexu.fast_delivery import compact_markpact_for_llm

    return compact_markpact_for_llm(markdown, mode=effective_mode, limit=limit)


def _try_read_options_cache(
    *,
    stage_html: str,
    ledger: object,
    focus_scope: str,
    goal: str,
    keep_els: list[str],
    delete_els: list[str],
) -> tuple[list[str], str] | None:
    from nexu.fast_delivery import read_cached_options

    return read_cached_options(
        cinema_dir=DIRECTORY,
        cache_dir=OPTIONS_CACHE_DIR,
        enabled=OPTIONS_CACHE,
        stage_html=stage_html,
        ledger=ledger,
        focus_scope=focus_scope,
        goal=goal,
        keep_els=keep_els,
        delete_els=delete_els,
        ui_type=_load_cinema_ui_profile().get("ui_type") or "web",
    )


def _store_options_cache(
    *,
    stage_html: str,
    ledger: object,
    focus_scope: str,
    goal: str,
    keep_els: list[str],
    delete_els: list[str],
    files: dict[str, str],
    labels: list[str],
    source: str,
) -> None:
    from nexu.fast_delivery import store_options_cache

    store_options_cache(
        cache_dir=OPTIONS_CACHE_DIR,
        enabled=OPTIONS_CACHE,
        stage_html=stage_html,
        ledger=ledger,
        focus_scope=focus_scope,
        goal=goal,
        keep_els=keep_els,
        delete_els=delete_els,
        files=files,
        labels=labels,
        source=source,
    )


def _extract_llm_content(response: object) -> str | None:
    choices = getattr(response, "choices", None)
    if not choices:
        return None
    message = getattr(choices[0], "message", None)
    if message is None:
        return None
    content = getattr(message, "content", None)
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
            elif isinstance(item, str):
                parts.append(item)
        return "".join(parts)
    if content is None:
        return None
    return str(content)


def _compact_llm_error(err_text: str) -> str:
    try:
        from nexu.cinema_llm import compact_llm_error

        return compact_llm_error(err_text)
    except Exception:
        compact = " ".join(str(err_text).split())
        return compact[:260]


def _load_policy_payload(*, stage: int = 0, focus_scope: str = "") -> dict:
    snapshot = {}
    if POLICY_SNAPSHOT_PATH.exists():
        snapshot = json.loads(POLICY_SNAPSHOT_PATH.read_text(encoding="utf-8"))
    ledger = []
    if POLICY_LEDGER_PATH.exists():
        ledger = json.loads(POLICY_LEDGER_PATH.read_text(encoding="utf-8"))
    if not isinstance(ledger, list):
        ledger = []
    effective_ui = _effective_ui_constraints_from_ledger(
        ledger, stage=stage, focus_scope=focus_scope
    )
    return {"snapshot": snapshot, "ledger": ledger, "effective_ui": effective_ui}


def _apply_entry_constraints(entry: dict, state: dict):
    for el in entry.get("keep") or []:
        key = str(el).strip()
        if key:
            state[key] = "keep"
    for el in entry.get("delete") or []:
        key = str(el).strip()
        if key:
            state[key] = "delete"


def _effective_ui_constraints_from_ledger(
    ledger: list, stage: int = 0, focus_scope: str = ""
) -> dict:
    try:
        import nexu_hooks
        return nexu_hooks.effective_ui_constraints(stage, focus_scope=focus_scope)
    except Exception:
        pass
    try:
        from nexu.cinema_policy import effective_ui_constraints_from_ledger

        return effective_ui_constraints_from_ledger(
            ledger, stage=stage, focus_scope=focus_scope or None
        )
    except Exception:
        pass
    state = {}
    if not isinstance(ledger, list):
        return {"keep": [], "delete": [], "by_element": {}}
    for entry in ledger:
        if not isinstance(entry, dict):
            continue
        if entry.get("stage") is not None and int(entry.get("stage", 0)) != stage:
            continue
        _apply_entry_constraints(entry, state)
    keep = sorted(k for k, v in state.items() if v == "keep")
    delete = sorted(k for k, v in state.items() if v == "delete")
    return {"keep": keep, "delete": delete, "by_element": state}


def _update_constraints(state: dict, elements: list | None, value: str):
    for el in elements or []:
        key = str(el).strip()
        if key:
            state[key] = value


def _merge_ui_constraints(ledger_keep, ledger_delete, session_keep, session_delete):
    state = {}
    _update_constraints(state, ledger_keep, "keep")
    _update_constraints(state, ledger_delete, "delete")
    _update_constraints(state, session_keep, "keep")
    _update_constraints(state, session_delete, "delete")
    keep = sorted(k for k, v in state.items() if v == "keep")
    delete = sorted(k for k, v in state.items() if v == "delete")
    return keep, delete


def _ensure_intract_on_path() -> bool:
    import sys

    curr = ROOT_PATH.resolve()
    for _ in range(6):
        for candidate in (curr / "intract" / "src", curr.parent / "intract" / "src"):
            if candidate.exists():
                path = str(candidate)
                if path not in sys.path:
                    sys.path.insert(0, path)
                return True
        curr = curr.parent
    return False


def _propose_cinema_contracts(stage: int, keep_els: list, delete_els: list) -> list:
    active = _active_project().get("project") or {}
    active_project_id = str(active.get("id") or "").strip()
    active_kind = str(active.get("kind") or "").strip().lower()
    domain = "calculator" if active_kind == "calculator" else "web"
    contract_scope = "ui"
    contract_subject = active_project_id or CAPSULE_NAME
    if _ensure_intract_on_path() and not active_project_id:
        try:
            from intract.proposals import propose_ui_delta_contract_dicts

            return propose_ui_delta_contract_dicts(
                stage=stage,
                keep=keep_els,
                delete=delete_els,
                capsule=CAPSULE_NAME,
                domain=domain,
            )
        except Exception:
            pass

    proposals = []
    for element_id in delete_els:
        contract_id = f"cinema.{contract_subject}.S{stage}.{contract_scope}.remove.{element_id}"
        proposals.append({
            "id": contract_id,
            "kind": "delete",
            "element": element_id,
            "line": (
                f"@intract.v1 id:{contract_id} scope:{contract_scope} "
                f"intent:ui:{contract_scope}:remove:{element_id} "
                f"priority:3 domain:{domain} effect:ui_change forbid:destructive_write,secret_leak "
                f"require:human_review validate:no_forbidden_effect "
                f'project:{contract_subject} meaning:"Cinema S{stage} removed #{element_id} in #{contract_scope}"'
            ),
        })
    for element_id in keep_els:
        contract_id = f"cinema.{contract_subject}.S{stage}.{contract_scope}.keep.{element_id}"
        proposals.append({
            "id": contract_id,
            "kind": "keep",
            "element": element_id,
            "line": (
                f"@intract.v1 id:{contract_id} scope:{contract_scope} "
                f"intent:ui:{contract_scope}:keep:{element_id} "
                f"priority:3 domain:{domain} effect:read forbid:destructive_write,secret_leak "
                f"require:human_review validate:no_forbidden_effect "
                f'project:{contract_subject} meaning:"Cinema S{stage} preserved #{element_id} in #{contract_scope}"'
            ),
        })
    return proposals


def _proposal_kind_and_element(proposal: dict) -> tuple[str, str]:
    kind = str(proposal.get("kind") or "")
    element = str(proposal.get("element") or "")
    if kind and element:
        return kind, element

    intent = str(proposal.get("intent") or "")
    if ":remove:" in intent:
        maybe = intent.rsplit(":", 1)[-1]
        if maybe:
            return "delete", maybe
    if ":keep:" in intent:
        maybe = intent.rsplit(":", 1)[-1]
        if maybe:
            return "keep", maybe
    return (kind or "change"), (element or "unknown")


def _proposal_delta_text(stage: int, proposal: dict) -> str:
    kind, element = _proposal_kind_and_element(proposal)
    action = "remove" if kind == "delete" else ("keep" if kind == "keep" else kind)
    base_id = str(proposal.get("based_on") or f"cinema.{CAPSULE_NAME}.S{stage}.ui.template")
    supersedes = proposal.get("supersedes")
    text = f"Δ {action} #{element} based_on={base_id}"
    if supersedes:
        text += f" supersedes={supersedes}"
    return text


def _normalize_proposals_for_ledger(stage: int, proposals: list) -> list:
    normalized = []
    for proposal in proposals:
        if not isinstance(proposal, dict):
            continue
        kind, element = _proposal_kind_and_element(proposal)
        item = dict(proposal)
        item.setdefault("kind", kind)
        item.setdefault("element", element)
        item.setdefault("based_on", f"cinema.{CAPSULE_NAME}.S{stage}.ui.template")
        item.setdefault("delta_text", _proposal_delta_text(stage, item))
        normalized.append(item)
    return normalized


def _append_policy_entry_legacy(stage: int, keep_els: list, delete_els: list, status: str, model: str) -> dict:
    proposals = _normalize_proposals_for_ledger(
        stage,
        _propose_cinema_contracts(stage, keep_els, delete_els),
    )
    entry = {
        "timestamp": datetime.now().isoformat(),
        "capsule": CAPSULE_NAME,
        "workspace": str(ROOT_PATH),
        "stage": stage,
        "status": status,
        "model": model,
        "keep": keep_els,
        "delete": delete_els,
        "proposed_contracts": proposals,
    }
    ledger = []
    if POLICY_LEDGER_PATH.exists():
        ledger = json.loads(POLICY_LEDGER_PATH.read_text(encoding="utf-8"))
    if not isinstance(ledger, list):
        ledger = []
    ledger.append(entry)
    POLICY_LEDGER_PATH.write_text(
        json.dumps(ledger, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return entry


def _nexu_hooks_apply(*, dry_run: bool = False, target: str = "both") -> dict:
    try:
        import nexu_hooks
    except ImportError:
        return {"error": "nexu_hooks.py missing; regenerate cinema (make cinema)"}
    return nexu_hooks.apply_manifest_from_ledger(dry_run=dry_run, target=target)


def _nexu_hooks_verify() -> dict:
    try:
        import nexu_hooks
    except ImportError:
        return {"error": "nexu_hooks.py missing; regenerate cinema (make cinema)"}
    return nexu_hooks.verify_capsule()


def _propose_llm_for_stage(stage: int, goal: str) -> dict:
    try:
        import nexu_hooks
    except ImportError:
        return {"error": "nexu_hooks.py missing; regenerate cinema (make cinema)"}
    return nexu_hooks.propose_llm(stage, goal, _resolve_model())


def _validate_intract_artifact(artifact: str, proposals: list, filename: str):
    try:
        import nexu_hooks
    except ImportError:
        return None
    return nexu_hooks.validate_artifact(artifact, proposals, filename)


def _append_policy_entry(
    stage: int,
    keep_els: list,
    delete_els: list,
    status: str,
    model: str,
    *,
    focus_scope: str = "",
) -> dict:
    try:
        import nexu_hooks
    except ImportError:
        return _append_policy_entry_legacy(stage, keep_els, delete_els, status, model)
    return nexu_hooks.append_policy_entry(
        stage, keep_els, delete_els, status, model, focus_scope=focus_scope
    )


def _save_history_checkpoint(**kwargs) -> dict | None:
    try:
        import nexu_hooks
    except ImportError:
        return None
    try:
        return nexu_hooks.save_history(**kwargs)
    except Exception:
        return None


def _list_history() -> dict:
    try:
        import nexu_hooks
    except ImportError:
        return {"checkpoints": [], "ledger_archive": []}
    payload = nexu_hooks.list_history()
    if isinstance(payload, dict):
        return payload
    return {"checkpoints": payload if isinstance(payload, list) else [], "ledger_archive": []}


def _restore_history(checkpoint_id: str, *, apply_manifest: bool = True, target: str = "both") -> dict:
    try:
        import nexu_hooks
    except ImportError:
        return {"error": "nexu_hooks.py missing; regenerate cinema (make cinema)"}
    return nexu_hooks.restore_history(
        checkpoint_id, apply_manifest=apply_manifest, target=target
    )


def _sync_option_previews(stage: int, delete_els: list | None = None) -> dict:
    try:
        import nexu_hooks
    except ImportError:
        return {}
    return nexu_hooks.sync_option_previews(stage, delete_els)


def _patch_option_previews(
    stage: int = 0,
    session_keep: list | None = None,
    session_delete: list | None = None,
    focus_scope: str = "",
) -> dict:
    try:
        import nexu_hooks
    except ImportError:
        return {}
    return nexu_hooks.patch_option_previews(
        stage,
        session_keep=session_keep,
        session_delete=session_delete,
        focus_scope=focus_scope,
    )


def _projects_catalog() -> dict:
    try:
        import nexu_hooks
    except ImportError:
        return {"projects": [], "filters": {}}
    return nexu_hooks.projects_catalog()


def _active_project() -> dict:
    try:
        import nexu_hooks
    except ImportError:
        return {"active": None}
    active = nexu_hooks.active_project()
    return {"active": active}


def _activate_project(project_id: str) -> dict:
    try:
        import nexu_hooks
    except ImportError:
        return {"error": "nexu_hooks.py missing; regenerate cinema (make cinema)"}
    return nexu_hooks.activate_project(project_id)


def _import_project(data: dict) -> dict:
    try:
        import nexu_hooks
    except ImportError:
        return {"error": "nexu_hooks.py missing; regenerate cinema (make cinema)"}
    kind = str(data.get("kind") or "").strip()
    if kind == "git":
        return nexu_hooks.import_project_from_git(
            str(data.get("git_url") or data.get("url") or ""),
            str(data.get("branch") or ""),
            allow_network=bool(ALLOW_NETWORK_CALLS),
        )
    if kind == "http":
        return nexu_hooks.import_project_from_http(
            str(data.get("url") or ""),
            allow_network=bool(ALLOW_NETWORK_CALLS),
        )
    if kind == "zip":
        return nexu_hooks.import_project_from_zip(
            str(data.get("filename") or "project.zip"),
            str(data.get("content_base64") or ""),
        )
    if kind == "markpact":
        return nexu_hooks.import_project_from_markpact(
            str(data.get("filename") or "project.md"),
            str(data.get("content_base64") or ""),
        )
    return {"error": "unsupported import kind"}


def _import_project_zip(content: bytes, filename: str) -> dict:
    try:
        import nexu_hooks
    except ImportError:
        return {"error": "nexu_hooks.py missing; regenerate cinema (make cinema)"}
    return nexu_hooks.import_project_from_zip(
        filename or "project.zip",
        content_bytes=content,
    )


def _import_project_git(data: dict) -> dict:
    try:
        import nexu_hooks
    except ImportError:
        return {"error": "nexu_hooks.py missing; regenerate cinema (make cinema)"}
    return nexu_hooks.import_project_from_git(
        str(data.get("url") or data.get("git_url") or ""),
        str(data.get("branch") or ""),
        allow_network=bool(ALLOW_NETWORK_CALLS),
    )


def _import_project_http(data: dict) -> dict:
    try:
        import nexu_hooks
    except ImportError:
        return {"error": "nexu_hooks.py missing; regenerate cinema (make cinema)"}
    return nexu_hooks.import_project_from_http(
        str(data.get("url") or ""),
        allow_network=bool(ALLOW_NETWORK_CALLS),
    )


def _import_project_markpact(content: bytes, filename: str) -> dict:
    try:
        import nexu_hooks
    except ImportError:
        return {"error": "nexu_hooks.py missing; regenerate cinema (make cinema)"}
    return nexu_hooks.import_project_from_markpact(
        filename or "project.md",
        content_bytes=content,
    )



def _parse_multipart_upload(
    post_data: bytes,
    content_type: str,
    *,
    field_names: tuple[str, ...],
    default_filename: str,
    empty_error: str,
    missing_error: str,
) -> tuple[str, bytes] | dict:
    from email.parser import BytesParser
    from email.policy import default

    if "multipart/form-data" not in (content_type or "").lower():
        return {"error": "expected multipart/form-data"}
    crlf = bytes([13, 10])
    raw = (
        b"MIME-Version: 1.0" + crlf
        + b"Content-Type: "
        + content_type.encode("utf-8", "surrogateescape")
        + crlf + crlf
        + post_data
    )
    msg = BytesParser(policy=default).parsebytes(raw)
    for part in msg.walk():
        if part.get_content_maintype() == "multipart":
            continue
        disposition = part.get("Content-Disposition", "")
        if not disposition:
            continue
        name = part.get_param("name", header="content-disposition")
        if name not in field_names:
            continue
        filename = part.get_filename() or default_filename
        payload = part.get_payload(decode=True)
        if payload is None:
            text = part.get_payload()
            payload = text.encode("utf-8") if isinstance(text, str) else b""
        if not payload:
            return {"error": empty_error}
        return str(filename), payload
    return {"error": missing_error}


def _parse_multipart_zip(post_data: bytes, content_type: str) -> tuple[str, bytes] | dict:
    return _parse_multipart_upload(
        post_data,
        content_type,
        field_names=("file", "zip"),
        default_filename="project.zip",
        empty_error="empty zip upload",
        missing_error="missing zip file field (file or zip)",
    )


def _parse_multipart_markpact(post_data: bytes, content_type: str) -> tuple[str, bytes] | dict:
    return _parse_multipart_upload(
        post_data,
        content_type,
        field_names=("file", "markpact"),
        default_filename="project.md",
        empty_error="empty markpact upload",
        missing_error="missing markpact file field (file or markpact)",
    )


def _export_markpact_markdown(*, stage: int = 0, user_goal: str = "") -> dict:
    try:
        import nexu_hooks
    except ImportError:
        return {"error": "nexu_hooks.py missing; regenerate cinema (make cinema)"}
    return nexu_hooks.export_markpact_readme(stage, user_goal)


def _services_catalog() -> dict:
    try:
        import nexu_hooks
    except ImportError:
        return {"services": [], "count": 0}
    return nexu_hooks.services_catalog()


def _publish_service(*, stage: int, project_id: str, project_title: str, user_goal: str) -> dict:
    try:
        import nexu_hooks
    except ImportError:
        return {"error": "nexu_hooks.py missing; regenerate cinema (make cinema)"}
    return nexu_hooks.publish_service(
        stage=stage,
        project_id=project_id,
        project_title=project_title,
        user_goal=user_goal,
    )


def _start_service(service_id: str) -> dict:
    try:
        import nexu_hooks
    except ImportError:
        return {"error": "nexu_hooks.py missing; regenerate cinema (make cinema)"}
    return nexu_hooks.start_service(service_id)


def _stop_service(service_id: str) -> dict:
    try:
        import nexu_hooks
    except ImportError:
        return {"error": "nexu_hooks.py missing; regenerate cinema (make cinema)"}
    return nexu_hooks.stop_service(service_id)


def _delete_service(service_id: str) -> dict:
    try:
        import nexu_hooks
    except ImportError:
        return {"error": "nexu_hooks.py missing; regenerate cinema (make cinema)"}
    return nexu_hooks.delete_service(service_id)


class _IterateHandler:
    """Helper class to handle the /iterate endpoint logic, reducing cyclomatic complexity."""
    
    def __init__(self, request_handler, post_data: bytes):
        self.handler = request_handler
        self.post_data = post_data
        self.data = None
        self.spatial_feedback = ''
        self.current_stage = 0
        self.annotations = []
        self.selected_fragments = []
        self.user_goal = ''
        self.focus_scope = ''
        self.focus_scope_label = ''
        self.focus_scope_display = ''
        self.current_state = ''
        self.expected_version = ''
        self.normalized_element_hints = []
        self.normalized_hints = []
        self.goal_block = ''
        self.scope_block = ''
        self.element_hints_block = ''
        self.current_html = ''
        self.current_html_for_prompt = ''
        self.force_refresh = False
        self.pending_goal = False
        self.requested_mode = ''
        self.session_keep = []
        self.session_delete = []
        self.policy_payload = {}
        self.goal_contract_lines = []
        self.ui_profile = {}
        self.project_kind = ''
        self.ledger_ui = {}
        self.ledger_keep = []
        self.ledger_delete = []
        self.keep_els = []
        self.delete_els = []
        self.hard_delete_els = []
        self.visual_redesign_scopes = {"colors", "shapes", "display", "orientation"}
        self.active_scope_name = ''
        self.marked_llm_context = None
        self.apply_active = False
        self.apply_options = False
        self.model = ''
        self.evolved_html = None
        self.llm_error = None
        self.options_written = []
        self.spatial_removed = []
        self.iteration_mode = 'none'
        self.status_msg = ''
    
    def handle(self):
        """Main entry point for handling the /iterate request."""
        try:
            self._parse_request_data()
            self._restore_http_import_stages_if_needed()
            self._read_current_stage_html()
            self._build_llm_context()
            self._determine_iteration_mode()
            self._execute_iteration()
            self._log_iteration()
            self._sync_options()
            self._append_policy_entry()
            self._validate_intract_artifact()
            self._save_history_checkpoint()
            self._send_response()
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.handler.send_response(500)
            self.handler.send_header('Access-Control-Allow-Origin', '*')
            self.handler.end_headers()
            self.handler.wfile.write(str(e).encode('utf-8'))
    
    def _parse_request_data(self):
        """Parse and normalize request data."""
        self.data = json.loads(self.post_data.decode('utf-8', errors='replace'))
        self.spatial_feedback = self.data.get('prompt', '')
        self.current_stage = int(self.data.get('current_stage', 0))
        self.annotations = self.data.get('annotations', [])
        if not isinstance(self.annotations, list):
            self.annotations = []
        self.selected_fragments = self.data.get('selected_fragments') or []
        if not isinstance(self.selected_fragments, list):
            self.selected_fragments = []
        self.user_goal = str(self.data.get('user_goal', '') or '').strip()
        self.focus_scope = str(self.data.get('focus_scope', '') or '').strip()
        self.focus_scope_label = str(self.data.get('focus_scope_label', '') or '').strip()
        self.focus_scope_display = self.focus_scope_label or (f"#{self.focus_scope}" if self.focus_scope else "")
        self.current_state = str(self.data.get('current_state', '') or '').strip()
        self.expected_version = str(self.data.get('expected_version', '') or '').strip()
        element_hints_raw = self.data.get('element_hints', [])
        if not isinstance(element_hints_raw, list):
            element_hints_raw = []
        self.normalized_element_hints = [
            str(item).strip() for item in element_hints_raw if str(item).strip()
        ]
        user_hints = self.data.get('user_hints', [])
        if not isinstance(user_hints, list):
            user_hints = []
        legacy_hints = [str(item).strip() for item in user_hints if str(item).strip()]
        if not self.user_goal and legacy_hints:
            self.user_goal = legacy_hints[0]
        if not self.normalized_element_hints and len(legacy_hints) > 1:
            self.normalized_element_hints = legacy_hints[1:]
        elif not self.normalized_element_hints and legacy_hints and legacy_hints[0] != self.user_goal:
            self.normalized_element_hints = legacy_hints
        self.normalized_hints = []
        if self.user_goal:
            self.normalized_hints.append(self.user_goal)
        self.normalized_hints.extend(self.normalized_element_hints)
        if self.focus_scope_display:
            self.normalized_hints.append(f"Focus scope {self.focus_scope_display}")
        self.goal_block = self.user_goal if self.user_goal else "none provided"
        self.scope_block = (
            f"{self.focus_scope_display}"
            + (f"\nCurrent slice: {self.current_state}" if self.current_state else "")
            + (f"\nExpected version/actions: {self.expected_version}" if self.expected_version else "")
            if self.focus_scope_display
            else "none selected"
        )
        self.element_hints_block = (
            "\n".join(f"- {hint}" for hint in self.normalized_element_hints)
            if self.normalized_element_hints
            else "none provided"
        )
    
    def _restore_http_import_stages_if_needed(self):
        """Restore HTTP import stages if needed for imported projects."""
        try:
            import nexu_hooks
            from nexu.cinema_project_imports import restore_http_import_stages_if_needed
            active = nexu_hooks.active_project() or {}
            project_id = str(active.get("id") or "")
            if project_id.startswith("http-"):
                meta_path = DIRECTORY / "imported_projects" / project_id / "project.json"
                if meta_path.is_file():
                    import_meta = json.loads(meta_path.read_text(encoding="utf-8"))
                    restore_http_import_stages_if_needed(DIRECTORY, import_meta)
        except Exception:
            pass
    
    def _read_current_stage_html(self):
        """Read the current stage HTML file."""
        stage_file = DIRECTORY / f'stage{self.current_stage}.html'
        self.current_html = stage_file.read_text(encoding='utf-8') if stage_file.exists() else '<p>No stage found</p>'
        self.current_html_for_prompt = _compact_html_for_llm(self.current_html)
        self.force_refresh = bool(
            self.data.get('force_refresh')
            or self.data.get('refresh_options')
            or str(self.data.get('cache', '') or '').strip().lower() == 'refresh'
        )
    
    def _build_llm_context(self):
        """Build LLM context from annotations and hints."""
        self.pending_goal = bool(self.data.get('pending_goal', False))
        self.requested_mode = str(self.data.get('iteration_mode', '') or '').strip()
        self.session_keep = [
            str(a.get('id') or '').strip()
            for a in self.annotations
            if isinstance(a, dict) and a.get('type') == 'KEEP' and str(a.get('id') or '').strip()
        ]
        self.session_delete = [
            str(a.get('id') or '').strip()
            for a in self.annotations
            if isinstance(a, dict) and a.get('type') == 'DELETE' and str(a.get('id') or '').strip()
        ]
        if self.session_delete or self.session_keep:
            self.pending_goal = False
        self.policy_payload = _load_policy_payload(
            stage=self.current_stage, focus_scope=self.focus_scope
        )
        self.goal_contract_lines = []
        self.ui_profile = _load_cinema_ui_profile()
        self.project_kind = str(self.ui_profile.get("kind") or "").lower()
        try:
            import nexu_hooks
            if self.user_goal:
                nexu_hooks.append_goal_policy_entry(
                    self.current_stage,
                    self.user_goal,
                    **_goal_entry_kwargs(self.data),
                )
            self.goal_contract_lines = list(nexu_hooks.goal_contract_lines() or [])
        except Exception:
            self.goal_contract_lines = []
        self.ledger_ui = self.policy_payload.get("effective_ui") or {}
        self.ledger_keep = list(self.ledger_ui.get("keep") or [])
        self.ledger_delete = list(self.ledger_ui.get("delete") or [])
        self.keep_els, self.delete_els = _merge_ui_constraints(
            self.ledger_keep, self.ledger_delete, self.session_keep, self.session_delete
        )
        self.active_scope_name = (self.focus_scope or "").strip().lower()
        self.hard_delete_els = [] if self.active_scope_name in self.visual_redesign_scopes else self.delete_els
        self.marked_llm_context = None
        if self.session_keep or self.session_delete or self.keep_els or self.delete_els:
            try:
                from repatch import resolve_marked_llm_context
                self.marked_llm_context = resolve_marked_llm_context(
                    self.current_html,
                    keep_els=self.keep_els,
                    delete_els=self.delete_els,
                    focus_scope=self.focus_scope or "",
                    project_kind=self.project_kind,
                    ui_profile=self.ui_profile,
                    client_fragments=self.selected_fragments,
                )
            except Exception:
                self.marked_llm_context = None
        if self.marked_llm_context:
            self.current_html_for_prompt = self.marked_llm_context
        else:
            try:
                from nexu.cinema_scope import scoped_html_fragment
                scoped = scoped_html_fragment(self.current_html, self.focus_scope, self.project_kind)
                if scoped:
                    self.current_html_for_prompt = _compact_html_for_llm(scoped)
            except Exception:
                pass
            if self.ui_profile.get("llm_context_mode") == "patch" and (
                self.ui_profile.get("html_outline") or self.ui_profile.get("visual_css")
            ):
                try:
                    from nexu.cinema_http_preprocess import build_http_llm_context
                    patch_ctx = build_http_llm_context(self.ui_profile)
                    if patch_ctx:
                        self.current_html_for_prompt = patch_ctx
                except Exception:
                    pass
    
    def _determine_iteration_mode(self):
        """Determine whether to apply active workspace or generate options."""
        if self.requested_mode == 'goal_options':
            self.apply_active = False
            self.apply_options = bool(
                self.user_goal
                or self.normalized_element_hints
                or self.session_keep
                or self.session_delete
                or self.ledger_keep
                or self.ledger_delete
                or self.pending_goal
                or self.focus_scope
            )
        elif self.requested_mode == 'active_workspace':
            self.apply_active = bool(self.session_delete or self.session_keep or self.delete_els or self.keep_els)
            self.apply_options = False
        elif (self.pending_goal or self.user_goal or self.normalized_element_hints) and not (self.session_delete or self.session_keep):
            self.apply_active = False
            self.apply_options = True
        elif self.session_delete or self.session_keep:
            self.apply_active = True
            self.apply_options = False
        else:
            self.apply_active = False
            self.apply_options = False
    
    def _execute_iteration(self):
        """Execute the iteration based on the determined mode."""
        self.model = _resolve_model()
        self.evolved_html = None
        self.llm_error = None
        self.options_written = []
        self.spatial_removed = []
        self.iteration_mode = "none"
        
        if not self.apply_active and not self.apply_options:
            self.status_msg = 'llm_skipped: no spatial feedback or goal provided'
        elif self.apply_options:
            self._execute_options_mode()
        else:
            self._execute_active_workspace_mode()
    
    def _execute_options_mode(self):
        """Execute options-only iteration mode."""
        self.iteration_mode = "options_only"
        hints_text = "; ".join(self.normalized_hints)
        goal_focus = (" Primary project goal: " + self.user_goal + ".") if self.user_goal else ""
        if self.focus_scope_display:
            goal_focus += (
                " Focus this variant on " + self.focus_scope_display
                + " only; keep other evolution axes stable unless required by the goal."
            )
        if self.normalized_element_hints:
            goal_focus += " Element hints: " + "; ".join(self.normalized_element_hints) + "."
        option_variants = self._llm_option_variants(
            self.focus_scope,
            goal_focus,
            str(self.ui_profile.get("ui_type") or "web"),
        )
        label_by_file = {
            filename: label for filename, label, _note in option_variants
        }
        
        ledger_raw = []
        if POLICY_LEDGER_PATH.exists():
            try:
                ledger_raw = json.loads(
                    POLICY_LEDGER_PATH.read_text(encoding="utf-8")
                )
            except Exception:
                ledger_raw = []
        
        cache_hit = None
        if not self.force_refresh:
            cache_hit = _try_read_options_cache(
                stage_html=self.current_html,
                ledger=ledger_raw,
                focus_scope=self.focus_scope or "functions",
                goal=self.user_goal,
                keep_els=self.keep_els,
                delete_els=self.delete_els,
            )
        if cache_hit:
            self.options_written, cache_key = cache_hit
            self.status_msg = 'proposed_options_cached'
            self.llm_error = None
            _write_llm_trace(
                label=f"Options cache hit ({self.focus_scope or 'functions'})",
                prompt=(
                    "Served alt_a/b/c from local options cache; no LLM call.\n\n"
                    f"cache_key: {cache_key}\n"
                    f"scope: #{self.focus_scope or 'functions'}\n"
                    f"goal: {self.user_goal or '(none)'}"
                ),
                output="\n".join(self.options_written),
                model="options-cache",
                duration_ms=0,
            )
        else:
            self._execute_options_llm(option_variants, label_by_file, ledger_raw)
    
    def _execute_options_llm(self, option_variants, label_by_file, ledger_raw):
        """Execute LLM-based options generation."""
        active_scope_for_route = (self.focus_scope or "").strip().lower()
        project_kind_for_route = str(self.ui_profile.get("kind") or "").lower()
        prefer_local_scope = False
        try:
            from nexu.cinema_scope import (
                DASHBOARD_KINDS,
                IMPORTED_KINDS,
                can_use_offline_fast_iterate,
            )
            prefer_local_scope = can_use_offline_fast_iterate(
                active_scope_for_route,
                project_kind_for_route,
                DIRECTORY,
                force_llm=FORCE_LLM,
                fast_scope_options=FAST_SCOPE_OPTIONS,
            ) and (
                project_kind_for_route in IMPORTED_KINDS
                or project_kind_for_route in DASHBOARD_KINDS
            )
        except Exception:
            prefer_local_scope = (
                project_kind_for_route
                in {"imported", "web", "dashboard", "slice", "monitor", "ecosystem", "api", "mcp", "frontend"}
                and active_scope_for_route in {
                    "colors",
                    "shapes",
                    "display",
                    "orientation",
                }
            )
        fast_labels = self._try_intract_fast_options() if prefer_local_scope else []
        if fast_labels:
            self.options_written = fast_labels
            self.status_msg = 'proposed_options_offline'
            self.llm_error = None
            from nexu.fast_delivery import read_option_files
            batch_files = read_option_files(DIRECTORY)
            _store_options_cache(
                stage_html=self.current_html,
                ledger=ledger_raw,
                focus_scope=self.focus_scope or "functions",
                goal=self.user_goal,
                keep_els=self.keep_els,
                delete_els=self.delete_els,
                files=batch_files,
                labels=self.options_written,
                source="offline",
            )
        function_labels = [] if self.options_written else self._try_function_patch_options()
        if function_labels:
            self.options_written = function_labels
            self.status_msg = 'proposed_options_by_intract_patch'
            self.llm_error = None
            from nexu.fast_delivery import read_option_files
            batch_files = read_option_files(DIRECTORY)
            _store_options_cache(
                stage_html=self.current_html,
                ledger=ledger_raw,
                focus_scope=self.focus_scope or "functions",
                goal=self.user_goal,
                keep_els=self.keep_els,
                delete_els=self.delete_els,
                files=batch_files,
                labels=self.options_written,
                source="function_patch",
            )
        patch_html, patch_labels, patch_err = (
            ({}, [], None)
            if self.options_written
            else self._try_llm_patch_options(option_variants)
        )
        if patch_html:
            for index, filename in enumerate(("alt_a.html", "alt_b.html", "alt_c.html")):
                if index < len(patch_labels) and patch_labels[index]:
                    label_by_file[filename] = patch_labels[index]
            self.options_written = self._write_option_files(patch_html, label_by_file)
            if self.options_written:
                self.status_msg = 'proposed_options_by_llm_patch'
                self.llm_error = None
                _store_options_cache(
                    stage_html=self.current_html,
                    ledger=ledger_raw,
                    focus_scope=self.focus_scope or "functions",
                    goal=self.user_goal,
                    keep_els=self.keep_els,
                    delete_els=self.delete_els,
                    files=patch_html,
                    labels=patch_labels or self.options_written,
                    source="llm_patch",
                )
            else:
                self.llm_error = patch_err
        elif not self.options_written:
            self._execute_full_llm_options(option_variants, label_by_file, ledger_raw, active_scope_for_route, project_kind_for_route)
    
    def _execute_full_llm_options(self, option_variants, label_by_file, ledger_raw, active_scope_for_route, project_kind_for_route):
        """Execute full LLM options generation as fallback."""
        from repatch import should_block_full_html_iterate
        block_full_html = should_block_full_html_iterate(
            project_kind_for_route,
            self.keep_els,
            self.delete_els,
            focus_scope=self.focus_scope or "",
        )
        if block_full_html:
            self.status_msg = "llm_blocked_marks_require_patch"
            self.llm_error = (
                "Marked fragments require patch/offline path; "
                "full-page LLM skipped for imported/web projects."
            )
        elif OPTION_GENERATION_MODE in {"batch", "single", "1"}:
            batch_html, batch_err = self._call_llm_batch_options(option_variants)
            self.options_written = self._write_option_files(batch_html, label_by_file)
            if self.options_written:
                self.status_msg = 'proposed_options_by_llm'
                self.llm_error = None
                _store_options_cache(
                    stage_html=self.current_html,
                    ledger=ledger_raw,
                    focus_scope=self.focus_scope or "functions",
                    goal=self.user_goal,
                    keep_els=self.keep_els,
                    delete_els=self.delete_els,
                    files=batch_html,
                    labels=self.options_written,
                    source="llm",
                )
            else:
                self.llm_error = batch_err
                self.status_msg = f'llm_failed: {self.llm_error or "No option HTML generated"}'
        else:
            parallel_html, parallel_err = self._generate_parallel_options(option_variants)
            self.options_written = self._write_option_files(parallel_html, label_by_file)
            if self.options_written:
                self.status_msg = 'proposed_options_by_llm'
                self.llm_error = None
                _store_options_cache(
                    stage_html=self.current_html,
                    ledger=ledger_raw,
                    focus_scope=self.focus_scope or "functions",
                    goal=self.user_goal,
                    keep_els=self.keep_els,
                    delete_els=self.delete_els,
                    files=parallel_html,
                    labels=self.options_written,
                    source="llm",
                )
            else:
                self.status_msg = f'llm_failed: {parallel_err or "No option HTML generated"}'
    
    def _execute_active_workspace_mode(self):
        """Execute active workspace iteration mode."""
        self.iteration_mode = "active_workspace"
        stage_file = DIRECTORY / f'stage{self.current_stage}.html'
        if self.delete_els:
            self.evolved_html, self.spatial_removed = self._apply_spatial_patch(self.current_html, self.delete_els)
        if self.delete_els and self.spatial_removed:
            stage_file.write_text(self.evolved_html, encoding="utf-8")
            self.status_msg = 'evolved_by_spatial_patch'
            self.llm_error = None
        else:
            self.evolved_html, self.llm_error = self._call_llm(
                self._build_llm_prompt(),
                trace_label="active workspace",
            )
            if self.evolved_html:
                reject_reason = None
                try:
                    import nexu_hooks
                    from nexu.cinema_project_imports import reject_import_stage_replacement
                    active = nexu_hooks.active_project() or {}
                    project_id = str(active.get("id") or "")
                    if project_id.startswith("http-"):
                        meta_path = (
                            DIRECTORY / "imported_projects" / project_id / "project.json"
                        )
                        if meta_path.is_file():
                            import_meta = json.loads(
                                meta_path.read_text(encoding="utf-8")
                            )
                            reject_reason = reject_import_stage_replacement(
                                self.evolved_html, import_meta
                            )
                except Exception:
                    reject_reason = None
                if reject_reason:
                    self.status_msg = "llm_blocked_import_guard"
                    self.llm_error = reject_reason
                else:
                    stage_file.write_text(self.evolved_html, encoding="utf-8")
                    self.status_msg = 'evolved_by_llm'
            else:
                self.status_msg = f'llm_failed: {self.llm_error or "Invalid HTML returned"}'
    
    def _log_iteration(self):
        """Log the iteration to CSV."""
        file_exists = LOG_CSV.exists()
        with open(LOG_CSV, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['timestamp', 'action', 'details'])
            writer.writerow([datetime.now().isoformat(), 'ITERATION_LLM', f"Stage: {self.current_stage} | Status: {self.status_msg} | Keep: {len(self.keep_els)} | Delete: {len(self.delete_els)}" ])
    
    def _sync_options(self):
        """Sync option previews."""
        from nexu.fast_delivery import is_options_ready_status
        options_sync = None
        if is_options_ready_status(self.status_msg) and self.options_written:
            options_sync = {
                "status": "options_fresh",
                "files": list(self.options_written or []),
            }
        elif self.status_msg in ('evolved_by_spatial_patch', 'evolved_by_llm') or (
            is_options_ready_status(self.status_msg) and self.options_written
        ):
            options_sync = _patch_option_previews(
                self.current_stage,
                session_keep=self.session_keep,
                session_delete=self.session_delete,
                focus_scope=self.focus_scope,
            )
        self.options_sync = options_sync
    
    def _append_policy_entry(self):
        """Append policy entry if there are keep/delete elements."""
        self.policy_entry = None
        if self.keep_els or self.delete_els:
            self.policy_entry = _append_policy_entry(
                self.current_stage,
                self.keep_els,
                self.delete_els,
                self.status_msg,
                self.model,
                focus_scope=self.focus_scope,
            )
    
    def _validate_intract_artifact(self):
        """Validate Intract artifact if evolved HTML exists."""
        self.intract_validation = None
        if self.evolved_html and self.policy_entry:
            self.intract_validation = _validate_intract_artifact(
                self.evolved_html,
                self.policy_entry.get("proposed_contracts", []),
                f"stage{self.current_stage}.html",
            )
    
    def _save_history_checkpoint(self):
        """Save history checkpoint if iteration was successful."""
        from nexu.fast_delivery import is_options_ready_status
        self.history_checkpoint = None
        if is_options_ready_status(self.status_msg) or self.status_msg in (
            'evolved_by_llm',
            'evolved_by_spatial_patch',
            'promoted',
        ):
            extra = ', '.join(self.options_written) if self.options_written else ''
            self.history_checkpoint = _save_history_checkpoint(
                action='iterate',
                stage=self.current_stage,
                status=self.status_msg,
                keep=self.keep_els,
                delete=self.delete_els,
                extra=extra,
            )
    
    def _send_response(self):
        """Send the response to the client."""
        self.handler.send_response(200)
        self.handler.send_header('Content-type', 'application/json; charset=utf-8')
        self.handler.send_header('Access-Control-Allow-Origin', '*')
        self.handler.end_headers()
        from nexu.cinema_iterate import build_iterate_response_payload
        payload = build_iterate_response_payload(
            status_msg=self.status_msg,
            iteration_mode=self.iteration_mode,
            focus_scope=self.focus_scope,
            focus_scope_label=self.focus_scope_label,
            current_stage=self.current_stage,
            keep_els=self.keep_els,
            delete_els=self.delete_els,
            ledger_keep=self.ledger_keep,
            ledger_delete=self.ledger_delete,
            session_keep=self.session_keep,
            session_delete=self.session_delete,
            options_written=self.options_written,
            spatial_removed=self.spatial_removed,
            llm_error=self.llm_error,
            policy_entry=self.policy_entry,
            intract_validation=self.intract_validation,
            history_checkpoint=self.history_checkpoint,
            options_sync=self.options_sync,
        )
        self.handler.wfile.write(json.dumps(payload).encode('utf-8'))
    
    # Nested closure methods (to be extracted from original code)
    def _build_llm_prompt(self, *, variant_note: str = "") -> str:
        """Build the LLM prompt for iteration."""
        markpact_context = ""
        markpact_mode = _effective_markpact_mode(
            self.focus_scope or "functions",
            self.project_kind,
        )
        try:
            import nexu_hooks
            _mp_payload = nexu_hooks.export_markpact_readme(self.current_stage, self.user_goal)
            _mp_body = str(_mp_payload.get("markdown") or "")
            if _mp_body:
                markpact_context = (
                    "Markpact context pack (active app, contracts, runnable HTML):\n"
                    "```markdown\n"
                    + _compact_markpact_for_llm(_mp_body, mode=markpact_mode)
                    + "\n```\n\n"
                )
        except Exception:
            markpact_context = ""
        variant_block = f"Variant direction:\n{variant_note}\n\n" if variant_note else ""
        variant_label = variant_note.split(":", 1)[0].strip() if variant_note else "active"
        llm_contract_block = _llm_communication_contract_block(
            ui_type=str(self.ui_profile.get("ui_type") or "web"),
            focus_scope=self.focus_scope or "functions",
            variant_label=variant_label,
            keep_els=self.keep_els,
            delete_els=self.delete_els,
            project_goal=self.user_goal,
            current_state=self.current_state,
            expected_version=self.expected_version,
            element_hints=self.normalized_element_hints,
        )
        ledger_block = ""
        if self.ledger_keep or self.ledger_delete:
            ledger_block = (
                "Accumulated policy contracts from earlier Cinema iterations (MUST respect):\n"
                "- KEEP from ledger: " + (', '.join(self.ledger_keep) if self.ledger_keep else 'none') + "\n"
                "- DELETE from ledger: " + (', '.join(self.ledger_delete) if self.ledger_delete else 'none') + "\n\n"
            )
        goal_contract_block = ""
        if self.goal_contract_lines:
            baseline_note = (
                "Intract goal extensions (extend frozen baseline; do NOT regress layout/contracts):\n"
                if self.ui_profile.get("ui_type") == "calculator"
                else "Intract goal extensions (extend imported/template baseline; preserve page structure):\n"
            )
            goal_contract_block = (
                baseline_note
                + "\n".join(f"- {line}" for line in self.goal_contract_lines)
                + "\n\n"
            )
        active_ctx = ""
        active = self.ui_profile.get("active") or {}
        if active.get("title") or active.get("id"):
            active_ctx = (
                f"Active example project: {active.get('title') or active.get('id')} "
                f"({active.get('kind') or self.ui_profile.get('ui_type')}).\n\n"
            )
        prompt = (
            _llm_prompt_intro(self.ui_profile)
            + "\n\n"
            + active_ctx
            + markpact_context
            + "Current HTML:\n```html\n"
            + self.current_html_for_prompt
            + "\n```\n\n"
            + variant_block
            + goal_contract_block
            + "Intract LLM communication contract (this model call must satisfy):\n"
            + llm_contract_block
            + "\n\n"
            + "Contract precedence:\n"
            "1. The Intract LLM communication contract is canonical.\n"
            "2. Goal/scope/hints below are supporting evidence only.\n"
            "3. If text conflicts with KEEP/DELETE or baseline contracts, follow the contracts.\n\n"
            + ledger_block
            + "Effective UI constraints for this request (ledger + current marks):\n"
            "- KEEP these elements (user likes them): "
            + (', '.join(self.keep_els) if self.keep_els else 'none specified')
            + "\n"
            + (
                "- REDESIGN these marked fragments within the selected scope: "
                if self.active_scope_name in self.visual_redesign_scopes
                else "- REDESIGN/DELETE these elements (user wants them changed or removed): "
            )
            + (', '.join(self.delete_els) if self.delete_els else 'none specified')
            + "\n\n"
            + "Project goal (overall target):\n"
            + self.goal_block
            + "\n\n"
            + "Focus scope for this iteration (single-choice hashtag):\n"
            + self.scope_block
            + "\n\n"
            + "Element hints (notes about marked controls):\n"
            + self.element_hints_block
            + "\n\n"
            + "Compiled summary from player:\n"
            + self.spatial_feedback
            + "\n\n"
            + "Rules:\n"
            + _llm_prompt_rules(self.ui_profile)
        )
        if self.ui_profile.get("ui_type") == "calculator" and self.keep_els and self.apply_options:
            trig = [t for t in self.keep_els if t in ('sin', 'cos', 'tan', 'log', 'ln')]
            if trig:
                prompt += (
                    "\n\nCRITICAL: These controls were explicitly kept and must appear in the HTML: "
                    + ", ".join(trig) + "."
                )
        if self.delete_els and not variant_note:
            delete_list = ", ".join(self.delete_els)
            if self.ui_profile.get("ui_type") == "calculator":
                prompt += (
                    "\n\nCRITICAL: Remove ONLY these controls: "
                    + delete_list
                    + ". Every other button (sin, cos, tan, log, ln, EXP, pi, digits, operators) must remain."
                )
            else:
                if self.active_scope_name in self.visual_redesign_scopes:
                    prompt += (
                        "\n\nCRITICAL: Modify ONLY these marked targets for the current visual scope: "
                        + delete_list
                        + ". Do not remove them; change only color/shape/display/orientation as requested."
                    )
                else:
                    prompt += (
                        "\n\nCRITICAL: Remove or redesign ONLY these targets: "
                        + delete_list
                        + ". Keep all other dashboard widgets unless listed."
                    )
        if self.marked_llm_context or self.ui_profile.get("llm_context_mode") == "patch":
            prompt += (
                "\n\nPATCH FRAGMENTS ONLY: apply scope changes to DELETE-marked "
                "targets; KEEP-marked elements must stay unchanged. "
                "Return a complete HTML document that preserves unmarked structure "
                "(minimal xpatch — do not replace the whole page)."
            )
        else:
            prompt += "\n\nReturn the full HTML:"
        return prompt
    
    def _apply_spatial_patch(self, html: str, delete_els: list) -> tuple[str | None, list]:
        """Apply spatial patch to HTML."""
        try:
            import nexu_hooks
        except ImportError:
            return None, []
        return nexu_hooks.apply_spatial_patch(html, delete_els)
    
    def _finalize_llm_html(self, html: str) -> str:
        """Finalize LLM-generated HTML."""
        import re
        from html import escape
        if not html:
            return html
        cleaned = re.sub(
            r'<script\b[^>]*>[\s\S]*?</script>', '', html, flags=re.I
        )
        def _screen_repl(match):
            attrs = match.group(1)
            inner = match.group(2)
            text = re.sub(r"<[^>]+>", " ", inner)
            text = re.sub(r"\s+", " ", text).strip()
            lower_text = text.lower()
            if (
                "🎯" not in text
                and "chemical &" not in lower_text
                and "keypad evolution" not in lower_text
                and "variant" not in lower_text
            ):
                return match.group(0)
            parts = [part.strip() for part in re.split(r"\s*[·|]\s*", text) if part.strip()]
            display = parts[-1] if parts else "0"
            caption = " · ".join(parts[:-1]) if len(parts) > 1 else text
            if not caption or caption == display:
                return match.group(0)
            return (
                '<div class="nexu-screen-caption">'
                + escape(caption)
                + '</div><div'
                + attrs
                + '>'
                + escape(display)
                + '</div>'
            )
        cleaned = re.sub(
            r'<div([^>]*\bid=["\']screen["\'][^>]*)>([\s\S]*?)</div>',
            _screen_repl,
            cleaned,
            count=1,
            flags=re.I,
        )
        inject = ''
        for name in ('_inject_shield.html', '_inject_runtime.html'):
            path = DIRECTORY / name
            if path.exists():
                inject += path.read_text(encoding='utf-8')
        lower = cleaned.lower()
        if '</body>' in lower:
            idx = lower.rfind('</body>')
            return cleaned[:idx] + inject + cleaned[idx:]
        return cleaned.rstrip() + inject + '\n</body>\n</html>\n'
    
    def _call_llm(self, prompt: str, trace_label: str = "active") -> tuple[str | None, str | None]:
        """Call LLM to generate HTML."""
        _ensure_api_key_env()
        started = time.time()
        model_name = _resolve_model()
        if not _llm_network_allowed():
            err = 'llm.allow_network_calls disabled in nexu.yaml'
            _write_llm_trace(
                label=trace_label,
                prompt=prompt,
                error=err,
                model=model_name,
                duration_ms=int((time.time() - started) * 1000),
            )
            return None, err
        if not _litellm_available():
            err = 'litellm is not available. From the nexu repo run: uv sync'
            _write_llm_trace(
                label=trace_label,
                prompt=prompt,
                error=err,
                model=model_name,
                duration_ms=int((time.time() - started) * 1000),
            )
            return None, err
        try:
            from nexu.cinema_llm import has_terminal_artifacts
            from nexu.cinema_llm import call_cinema_html_llm
            raw, err = call_cinema_html_llm(
                prompt,
                ROOT_PATH,
                model=model_name,
                max_tokens=MAX_TOKENS,
                ui_type=str(self.ui_profile.get("ui_type") or "web"),
            )
            if err:
                _write_llm_trace(
                    label=trace_label,
                    prompt=prompt,
                    error=err,
                    model=model_name,
                    duration_ms=int((time.time() - started) * 1000),
                )
                return None, err
            if raw:
                if has_terminal_artifacts(raw):
                    err = 'LLM output contained terminal artifacts, not clean HTML'
                    _write_llm_trace(
                        label=trace_label,
                        prompt=prompt,
                        output=raw,
                        error=err,
                        model=model_name,
                        duration_ms=int((time.time() - started) * 1000),
                    )
                    return None, err
                html = self._finalize_llm_html(raw)
                _write_llm_trace(
                    label=trace_label,
                    prompt=prompt,
                    output=html,
                    model=model_name,
                    duration_ms=int((time.time() - started) * 1000),
                )
                return html, None
            err = 'LLM did not return a complete HTML document'
            _write_llm_trace(
                label=trace_label,
                prompt=prompt,
                error=err,
                model=model_name,
                duration_ms=int((time.time() - started) * 1000),
            )
            return None, err
        except Exception as llm_exc:
            err = _compact_llm_error(str(llm_exc))
            _write_llm_trace(
                label=trace_label,
                prompt=prompt,
                error=err,
                model=model_name,
                duration_ms=int((time.time() - started) * 1000),
            )
            return None, err
    
    def _parse_batch_options(self, text: str) -> dict[str, str]:
        """Parse batch options from LLM response."""
        from nexu.cinema_llm import parse_batch_alt_options
        return parse_batch_alt_options(
            text or "",
            ui_type=str(self.ui_profile.get("ui_type") or "web"),
        )
    
    def _generate_parallel_options(
        self, option_variants: list[tuple[str, str, str]]
    ) -> tuple[dict[str, str], str | None]:
        """Generate parallel options using ThreadPoolExecutor."""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        batch: dict[str, str] = {}
        llm_err: str | None = None
        def _generate_option(filename: str, label: str, variant_note: str):
            prompt = self._build_llm_prompt(variant_note=variant_note)
            html, err = self._call_llm(prompt, trace_label=label)
            return filename, label, html, err
        with ThreadPoolExecutor(max_workers=len(option_variants)) as pool:
            futures = [
                pool.submit(_generate_option, filename, label, variant_note)
                for filename, label, variant_note in option_variants
            ]
            for future in as_completed(futures):
                filename, _label, html, err = future.result()
                if html:
                    batch[filename] = html
                elif not llm_err:
                    llm_err = err
        return batch, llm_err
    
    def _build_batch_options_prompt(self, option_variants: list[tuple[str, str, str]]) -> str:
        """Build prompt for batch options generation."""
        notes = "\n".join(
            f"- {label}: {variant_note}"
            for _filename, label, variant_note in option_variants
        )
        base = self._build_llm_prompt(
            variant_note=(
                "BATCH OPTIONS REQUEST. Generate all three option variants in one response. "
                "Use the option directions listed below."
            )
        )
        return (
            base
            + "\n\nBatch option directions:\n"
            + notes
            + "\n\nReturn exactly this structure, with no markdown fences or prose:\n"
            "<!-- NEXU_ALT_A -->\n"
            "<!DOCTYPE html>...complete Option A HTML...</html>\n"
            "<!-- NEXU_ALT_B -->\n"
            "<!DOCTYPE html>...complete Option B HTML...</html>\n"
            "<!-- NEXU_ALT_C -->\n"
            "<!DOCTYPE html>...complete Option C HTML...</html>\n"
        )
    
    def _call_llm_batch_options(
        self, option_variants: list[tuple[str, str, str]]
    ) -> tuple[dict[str, str], str | None]:
        """Call LLM to generate batch options."""
        prompt = self._build_batch_options_prompt(option_variants)
        _ensure_api_key_env()
        started = time.time()
        model_name = _resolve_model()
        if not _llm_network_allowed():
            err = 'llm.allow_network_calls disabled in nexu.yaml'
            _write_llm_trace(
                label="Options A-C batch",
                prompt=prompt,
                error=err,
                model=model_name,
                duration_ms=int((time.time() - started) * 1000),
            )
            return {}, err
        try:
            from nexu.cinema_llm import call_cinema_text_llm
            text, err = call_cinema_text_llm(
                prompt,
                ROOT_PATH,
                model=model_name,
                max_tokens=max(MAX_TOKENS, 8192),
                system_prompt=(
                    "You are a UI evolution engine. Return exactly three complete HTML "
                    "documents using the requested NEXU_ALT_A/B/C markers. "
                    "No markdown fences, no explanation."
                ),
            )
            if err:
                _write_llm_trace(
                    label="Options A-C batch",
                    prompt=prompt,
                    error=err,
                    model=model_name,
                    duration_ms=int((time.time() - started) * 1000),
                )
                return {}, err
            parsed = self._parse_batch_options(text or "")
            if not parsed:
                preview = " ".join(str(text or "").split())[:800]
                err = (
                    "LLM batch response did not contain valid NEXU_ALT_A/B/C HTML"
                    + (f"; response_preview={preview}" if preview else "")
                )
                _write_llm_trace(
                    label="Options A-C batch",
                    prompt=prompt,
                    output=text or "",
                    error=err,
                    model=model_name,
                    duration_ms=int((time.time() - started) * 1000),
                )
                return {}, err
            finalized = {
                filename: self._finalize_llm_html(html)
                for filename, html in parsed.items()
            }
            _write_llm_trace(
                label="Options A-C batch",
                prompt=prompt,
                output=text or "",
                model=model_name,
                duration_ms=int((time.time() - started) * 1000),
            )
            return finalized, None
        except Exception as exc:
            err = _compact_llm_error(str(exc))
            _write_llm_trace(
                label="Options A-C batch",
                prompt=prompt,
                error=err,
                model=model_name,
                duration_ms=int((time.time() - started) * 1000),
            )
            return {}, err
    
    def _try_llm_patch_options(
        self, option_variants: list[tuple[str, str, str]]
    ) -> tuple[dict[str, str], list[str], str | None]:
        """Try LLM patch options for visual scopes."""
        if not LLM_PATCH_OPTIONS:
            return {}, [], None
        active_scope = (self.focus_scope or "").strip().lower()
        project_kind = str(self.ui_profile.get("kind") or "").lower()
        try:
            from nexu.cinema_scope import cinema_has_offline_baseline
            from repatch.ui_patch import (
                apply_ui_patch_options,
                build_ui_patch_prompt,
                parse_ui_patch_response,
                supports_llm_patch_scope,
            )
            if not supports_llm_patch_scope(
                active_scope,
                project_kind,
                has_marks=bool(self.marked_llm_context),
            ):
                return {}, [], None
            if not cinema_has_offline_baseline(DIRECTORY):
                return {}, [], None
        except Exception as exc:
            return {}, [], _compact_llm_error(str(exc))
        patch_source_html = self.current_html
        if self.marked_llm_context:
            patch_source_html = self.marked_llm_context
        elif self.ui_profile.get("llm_context_mode") == "patch":
            try:
                from nexu.cinema_http_preprocess import build_http_llm_context
                patch_ctx = build_http_llm_context(self.ui_profile)
                if patch_ctx:
                    patch_source_html = patch_ctx
            except Exception:
                pass
        prompt = build_ui_patch_prompt(
            patch_source_html,
            focus_scope=active_scope,
            project_kind=project_kind,
            option_variants=option_variants,
            user_goal=self.user_goal,
            keep_els=self.keep_els,
            delete_els=self.delete_els,
            context_fragment=self.marked_llm_context,
        )
        _ensure_api_key_env()
        started = time.time()
        model_name = _resolve_model()
        if not _llm_network_allowed():
            err = 'llm.allow_network_calls disabled in nexu.yaml'
            _write_llm_trace(
                label=f"Options A-C LLM patch ({active_scope or 'none'})",
                prompt=prompt,
                error=err,
                model=model_name,
                duration_ms=int((time.time() - started) * 1000),
            )
            return {}, [], err
        try:
            from nexu.cinema_llm import call_cinema_text_llm
            text, err = call_cinema_text_llm(
                prompt,
                ROOT_PATH,
                model=model_name,
                max_tokens=min(MAX_TOKENS, 4096),
                system_prompt=(
                    "You are a UI patch generator. Return JSON only. "
                    "The JSON must contain variants.alt_a.html/css, "
                    "variants.alt_b.html/css, and variants.alt_c.html/css. "
                    "Never return HTML, markdown, prose, scripts, or external URLs."
                ),
            )
            if err:
                _write_llm_trace(
                    label=f"Options A-C LLM patch ({active_scope or 'none'})",
                    prompt=prompt,
                    error=err,
                    model=model_name,
                    duration_ms=int((time.time() - started) * 1000),
                )
                return {}, [], err
            patch = parse_ui_patch_response(text or "")
            files, labels = apply_ui_patch_options(
                self.current_html,
                patch,
                option_variants=option_variants,
                focus_scope=active_scope,
                project_kind=project_kind,
                keep_els=self.keep_els,
                delete_els=self.delete_els,
            )
            _write_llm_trace(
                label=f"Options A-C LLM patch ({active_scope or 'none'})",
                prompt=prompt,
                output=text or "",
                model=model_name,
                duration_ms=int((time.time() - started) * 1000),
            )
            return files, labels, None
        except Exception as exc:
            err = _compact_llm_error(str(exc))
            _write_llm_trace(
                label=f"Options A-C LLM patch ({active_scope or 'none'})",
                prompt=prompt,
                error=err,
                model=model_name,
                duration_ms=int((time.time() - started) * 1000),
            )
            return {}, [], err
    
    def _try_intract_fast_options(self) -> list[str]:
        """Try Intract fast options for visual scopes."""
        if FORCE_LLM or not FAST_SCOPE_OPTIONS:
            return []
        active_scope = (self.focus_scope or "").strip().lower()
        project_kind = str(self.ui_profile.get("kind") or "").lower()
        try:
            from nexu.cinema_scope import can_use_offline_fast_iterate
            if not can_use_offline_fast_iterate(
                active_scope,
                project_kind,
                DIRECTORY,
                force_llm=FORCE_LLM,
                fast_scope_options=FAST_SCOPE_OPTIONS,
            ):
                return []
        except Exception:
            if active_scope not in {
                "colors",
                "shapes",
                "display",
                "orientation",
                "keypad",
            }:
                return []
        try:
            from nexu.cinema_offline_options import write_goal_options_offline
            started = time.time()
            labels = write_goal_options_offline(
                DIRECTORY,
                keep_els=self.keep_els,
                delete_els=self.delete_els,
                hints=self.normalized_hints + self.normalized_element_hints,
                user_goal=self.user_goal,
                goal_contract_lines=self.goal_contract_lines,
                focus_scope=active_scope,
            )
            if labels:
                _write_llm_trace(
                    label=f"Intract fast patch ({active_scope})",
                    prompt=(
                        "Local Intract-controlled option generation; no LLM call.\n\n"
                        f"scope: #{active_scope}\n"
                        f"goal: {self.user_goal or '(none)'}\n"
                        f"keep: {', '.join(self.keep_els) if self.keep_els else 'none'}\n"
                        f"change: {', '.join(self.delete_els) if self.delete_els else 'none'}\n"
                        f"hard_delete: {', '.join(self.hard_delete_els) if self.hard_delete_els else 'none'}\n"
                        "contract: preserve baseline and change only the selected scope."
                    ),
                    output="\n".join(labels),
                    model="intract-local-patch",
                    duration_ms=int((time.time() - started) * 1000),
                )
            return labels
        except Exception as exc:
            _write_llm_trace(
                label=f"Intract fast patch ({active_scope or 'none'})",
                prompt="Local Intract-controlled option generation failed before LLM fallback.",
                error=_compact_llm_error(str(exc)),
                model="intract-local-patch",
            )
            return []
    
    def _try_function_patch_options(self) -> list[str]:
        """Try function patch options for #functions scope."""
        active_scope = (self.focus_scope or "").strip().lower()
        project_kind = str(self.ui_profile.get("kind") or "").lower()
        try:
            from nexu.cinema_dom_patch import (
                build_function_option_patches,
                build_function_patch_context,
                supports_function_patch,
            )
            if not supports_function_patch(active_scope, project_kind):
                return []
            started = time.time()
            files, labels, meta = build_function_option_patches(
                self.current_html,
                user_goal=self.user_goal,
                project_kind=project_kind,
                keep_els=self.keep_els,
                delete_els=self.delete_els,
            )
            if not files:
                _write_llm_trace(
                    label="Intract function patch",
                    prompt=build_function_patch_context(
                        self.current_html,
                        user_goal=self.user_goal,
                    ),
                    error=_compact_llm_error(str(meta)),
                    model="intract-function-patch",
                )
                return []
            for filename, html in files.items():
                (DIRECTORY / filename).write_text(html, encoding="utf-8")
            _write_llm_trace(
                label="Intract function patch",
                prompt=build_function_patch_context(
                    self.current_html,
                    user_goal=self.user_goal,
                ),
                output="\n".join(labels),
                model="intract-function-patch",
                duration_ms=int((time.time() - started) * 1000),
            )
            return labels
        except Exception as exc:
            _write_llm_trace(
                label="Intract function patch",
                prompt="Local function patch generation failed before LLM fallback.",
                error=_compact_llm_error(str(exc)),
                model="intract-function-patch",
            )
            return []
    
    def _llm_option_variants(
        self, scope: str, focus_text: str, ui_type: str
    ) -> list[tuple[str, str, str]]:
        """Get LLM option variants for the given scope."""
        try:
            from nexu.cinema_scope import scope_option_variants
            return list(
                scope_option_variants(
                    scope or "functions",
                    ui_type or "web",
                    focus_text,
                )
            )
        except Exception:
            pass
        try:
            from nexu.cinema_llm_contracts import build_llm_option_variants
            return build_llm_option_variants(
                focus_scope=scope or "functions",
                focus_text=focus_text,
            )
        except Exception:
            active_scope = (scope or "functions").strip().lower()
            suffix = (" " + focus_text.strip()) if focus_text.strip() else ""
            return [
                (
                    "alt_a.html",
                    f"Option A ({active_scope}: conservative)",
                    "INTRACT-SCOPED VARIANT. Conservative change inside the selected scope only."
                    + suffix,
                ),
                (
                    "alt_b.html",
                    f"Option B ({active_scope}: balanced)",
                    "INTRACT-SCOPED VARIANT. Balanced change inside the selected scope only."
                    + suffix,
                ),
                (
                    "alt_c.html",
                    f"Option C ({active_scope}: ambitious)",
                    "INTRACT-SCOPED VARIANT. Ambitious change inside the selected scope only."
                    + suffix,
                ),
            ]
    
    def _write_option_files(self, batch: dict[str, str], label_by_file: dict) -> list[str]:
        """Write option files to disk."""
        from nexu.cinema_html_validate import filter_valid_option_batch
        valid, validation_errors = filter_valid_option_batch(
            batch,
            ui_type=str(self.ui_profile.get("ui_type") or "web"),
        )
        if not valid:
            if validation_errors:
                self.llm_error = (
                    "LLM options failed HTML structure validation: "
                    + "; ".join(validation_errors[:6])
                )
            return []
        written: list[str] = []
        for filename, html in valid.items():
            (DIRECTORY / filename).write_text(html, encoding="utf-8")
            written.append(label_by_file.get(filename, filename))
        return written


class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIRECTORY), **kwargs)

    def _handle_get_root_redirect(self):
        suffix = ""
        if "?" in self.path:
            suffix = "?" + self.path.split("?", 1)[1]
        self.send_response(302)
        self.send_header("Location", "cinema_player.html" + suffix)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

    def _handle_get_policy(self):
        try:
            from urllib.parse import parse_qs, urlparse
            parsed = urlparse(self.path)
            qs = parse_qs(parsed.query or "")
            focus_scope = str((qs.get("focus_scope") or [""])[0] or "").strip()
            payload = _load_policy_payload(focus_scope=focus_scope)
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            self.send_response(500)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(str(e).encode("utf-8"))

    def _handle_get_projects_catalog(self):
        try:
            payload = _projects_catalog()
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            self.send_response(500)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(str(e).encode("utf-8"))

    def _handle_get_projects_active(self):
        try:
            payload = _active_project()
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            self.send_response(500)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(str(e).encode("utf-8"))

    def _handle_get_services_catalog(self):
        try:
            payload = _services_catalog()
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            self.send_response(500)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(str(e).encode("utf-8"))

    def _handle_get_health(self):
        player_path = DIRECTORY / "cinema_player.html"
        player_mtime = None
        if player_path.is_file():
            try:
                player_mtime = player_path.stat().st_mtime
            except OSError:
                player_mtime = None
        body = json.dumps(
            {
                "ok": True,
                "cinema": CAPSULE_NAME,
                "capsule": CAPSULE_NAME,
                "cinema_root": str(DIRECTORY),
                "workspace_root": str(ROOT_PATH),
                "cinema_player_mtime": player_mtime,
                "template_synced_hint": "Refreshed on cinema server start (sync_cinema_templates); re-run make cinema if player lags package templates.",
            }
        ).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _handle_get_llm_status(self):
        try:
            payload = _llm_status_payload()
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            self.send_response(500)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(str(e).encode("utf-8"))

    def _handle_get_llm_traces(self):
        try:
            from urllib.parse import parse_qs, urlparse
            parsed = urlparse(self.path)
            qs = parse_qs(parsed.query)
            project_id = str((qs.get("project") or [""])[0])
            payload = _list_llm_traces(project_id)
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            self.send_response(500)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(str(e).encode("utf-8"))

    def _handle_get_imported_project_route(self):
        imported_route = _parse_imported_project_route(self.path)
        if not imported_route:
            return False
        project_id, action = imported_route
        try:
            if action == "markpact":
                payload = _imported_markpact(project_id)
            else:
                payload = _imported_llm_log(project_id)
            status = 404 if payload.get("error") else 200
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            self.send_response(500)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(str(e).encode("utf-8"))
        return True

    def _handle_get_llm_trace(self):
        try:
            from urllib.parse import parse_qs, urlparse
            parsed = urlparse(self.path)
            qs = parse_qs(parsed.query)
            trace_id = str((qs.get("id") or [""])[0])
            payload = _read_llm_trace(trace_id)
            status = 404 if payload.get("error") else 200
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            self.send_response(500)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(str(e).encode("utf-8"))

    def _handle_get_history(self):
        try:
            payload = _list_history()
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            self.send_response(500)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(str(e).encode("utf-8"))

    def _handle_get_export_markpact(self):
        try:
            from urllib.parse import parse_qs, urlparse
            parsed = urlparse(self.path)
            qs = parse_qs(parsed.query)
            stage = int((qs.get("stage") or ["0"])[0])
            user_goal = str((qs.get("goal") or [""])[0])
            payload = _export_markpact_markdown(stage=stage, user_goal=user_goal)
            if payload.get("error"):
                self.send_response(404)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(payload["error"].encode("utf-8"))
                return
            filename = str(payload.get("filename") or "nexu-markpact.md")
            body = str(payload.get("markdown") or "").encode("utf-8")
            self.send_response(200)
            self.send_header("Content-type", "text/markdown; charset=utf-8")
            self.send_header(
                "Content-Disposition",
                f'attachment; filename="{{filename}}"',
            )
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            self.send_response(500)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(str(e).encode("utf-8"))

    def do_GET(self):
        from urllib.parse import urlparse

        parsed_root_path = urlparse(self.path).path
        
        # Dispatch table for GET endpoints
        dispatch = {
            "/projects/catalog": self._handle_get_projects_catalog,
            "/projects/active": self._handle_get_projects_active,
            "/services/catalog": self._handle_get_services_catalog,
            "/health": self._handle_get_health,
            "/llm/status": self._handle_get_llm_status,
            "/llm/traces": self._handle_get_llm_traces,
            "/history": self._handle_get_history,
        }
        
        # Handle root redirect
        if parsed_root_path in ("", "/"):
            self._handle_get_root_redirect()
            return
        
        # Handle policy endpoint (startswith)
        if self.path.startswith("/policy"):
            self._handle_get_policy()
            return
        
        # Handle imported project routes
        if self._handle_get_imported_project_route():
            return
        
        # Handle llm/trace endpoint (startswith)
        if self.path.startswith("/llm/trace"):
            self._handle_get_llm_trace()
            return
        
        # Handle export/markpact endpoint (startswith)
        if self.path.startswith("/export/markpact"):
            self._handle_get_export_markpact()
            return
        
        # Handle paths with multiple variants
        handler = None
        for path, handler_func in dispatch.items():
            if self.path in (path, f"{path}/"):
                handler = handler_func
                break
        
        if handler:
            handler()
            return
        
        return super().do_GET()

    def _handle_post_log(self, post_data: bytes):
        try:
            data = json.loads(post_data.decode('utf-8', errors='replace'))
            timestamp = datetime.now().isoformat()
            action = data.get('action', 'unknown')
            details = data.get('details', '')
            
            file_exists = LOG_CSV.exists()
            with open(LOG_CSV, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(['timestamp', 'action', 'details'])
                writer.writerow([timestamp, action, details])
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "logged"}).encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode('utf-8'))

    def _handle_post_manifest_apply_ledger(self, post_data: bytes):
        try:
            data = json.loads(post_data.decode('utf-8', errors='replace')) if post_data else {}
            dry_run = bool(data.get('dry_run', False))
            target = str(data.get('target', 'both'))
            payload = _nexu_hooks_apply(dry_run=dry_run, target=target)
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(payload, ensure_ascii=False).encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(str(e).encode('utf-8'))

    def _handle_post_capsule_verify(self):
        try:
            payload = _nexu_hooks_verify()
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(payload, ensure_ascii=False).encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(str(e).encode('utf-8'))

    def _handle_post_propose_llm(self, post_data: bytes):
        try:
            data = json.loads(post_data.decode('utf-8', errors='replace')) if post_data else {}
            stage = int(data.get('current_stage', 0))
            goal = str(data.get('goal', '') or '')
            payload = _propose_llm_for_stage(stage, goal)
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(payload, ensure_ascii=False).encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(str(e).encode('utf-8'))

    def _handle_post_propose_goal(self, post_data: bytes):
        try:
            data = json.loads(post_data.decode('utf-8', errors='replace')) if post_data else {}
            stage = int(data.get('current_stage', 0))
            goal = str(data.get('goal', '') or data.get('user_goal', '') or '').strip()
            if not goal:
                payload = {"error": "goal required"}
            else:
                import nexu_hooks
                entry = nexu_hooks.append_goal_policy_entry(
                    stage, goal, **_goal_entry_kwargs(data)
                )
                proposals = entry.get("proposed_contracts") or []
                payload = {
                    "status": "goal_defined",
                    "count": len(proposals),
                    "user_goal": goal,
                    "proposals": proposals,
                }
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(payload, ensure_ascii=False).encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(str(e).encode('utf-8'))

    def _handle_post_history_restore(self, post_data: bytes):
        try:
            data = json.loads(post_data.decode('utf-8', errors='replace')) if post_data else {}
            cp_id = str(data.get('checkpoint_id', '') or data.get('id', '')).strip()
            if not cp_id:
                payload = {"error": "checkpoint_id required"}
            else:
                apply_manifest = bool(data.get('apply_manifest', True))
                target = str(data.get('target', 'both'))
                payload = _restore_history(cp_id, apply_manifest=apply_manifest, target=target)
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(payload, ensure_ascii=False).encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(str(e).encode('utf-8'))

    def _handle_post_services_publish(self, post_data: bytes):
        try:
            data = json.loads(post_data.decode('utf-8', errors='replace')) if post_data else {}
            payload = _publish_service(
                stage=int(data.get('stage', 0)),
                project_id=str(data.get('project_id') or data.get('id') or ''),
                project_title=str(data.get('project_title') or data.get('title') or ''),
                user_goal=str(data.get('goal') or data.get('user_goal') or ''),
            )
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(payload, ensure_ascii=False).encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(str(e).encode('utf-8'))

    def _handle_post_services_start(self, post_data: bytes):
        try:
            data = json.loads(post_data.decode('utf-8', errors='replace')) if post_data else {}
            service_id = str(data.get('service_id') or data.get('id') or '').strip()
            if not service_id:
                payload = {"error": "missing service_id"}
            else:
                payload = _start_service(service_id)
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(payload, ensure_ascii=False).encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(str(e).encode('utf-8'))

    def _handle_post_services_stop(self, post_data: bytes):
        try:
            data = json.loads(post_data.decode('utf-8', errors='replace')) if post_data else {}
            service_id = str(data.get('service_id') or data.get('id') or '').strip()
            if not service_id:
                payload = {"error": "missing service_id"}
            else:
                payload = _stop_service(service_id)
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(payload, ensure_ascii=False).encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(str(e).encode('utf-8'))

    def _handle_post_services_delete(self, post_data: bytes):
        try:
            data = json.loads(post_data.decode('utf-8', errors='replace')) if post_data else {}
            service_id = str(data.get('service_id') or data.get('id') or '').strip()
            if not service_id:
                payload = {"error": "missing service_id"}
            else:
                payload = _delete_service(service_id)
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(payload, ensure_ascii=False).encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(str(e).encode('utf-8'))

    def _handle_post_projects_activate(self, post_data: bytes):
        try:
            data = json.loads(post_data.decode('utf-8', errors='replace')) if post_data else {}
            project_id = str(data.get('id') or data.get('project_id') or '').strip()
            if not project_id:
                payload = {"error": "missing project id"}
            else:
                payload = _activate_project(project_id)
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(payload, ensure_ascii=False).encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(str(e).encode('utf-8'))

    def _handle_post_projects_import(self, post_data: bytes):
        try:
            data = json.loads(post_data.decode('utf-8', errors='replace')) if post_data else {}
            payload = _import_project(data)
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(payload, ensure_ascii=False).encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(str(e).encode('utf-8'))

    def _handle_post_projects_import_zip(self, post_data: bytes):
        try:
            content_type = str(self.headers.get('Content-Type') or '')
            if 'multipart/form-data' in content_type:
                parsed = _parse_multipart_zip(post_data, content_type)
                if isinstance(parsed, dict):
                    payload = parsed
                else:
                    filename, content = parsed
                    payload = _import_project_zip(content, filename)
            else:
                data = json.loads(post_data.decode('utf-8', errors='replace')) if post_data else {}
                payload = _import_project_zip(
                    base64.b64decode(str(data.get('content_base64') or '')),
                    str(data.get('filename') or 'project.zip'),
                )
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(payload, ensure_ascii=False).encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(str(e).encode('utf-8'))

    def _handle_post_projects_import_git(self, post_data: bytes):
        try:
            data = json.loads(post_data.decode('utf-8', errors='replace')) if post_data else {}
            payload = _import_project_git(data)
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(payload, ensure_ascii=False).encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(str(e).encode('utf-8'))

    def _handle_post_projects_import_http(self, post_data: bytes):
        try:
            data = json.loads(post_data.decode('utf-8', errors='replace')) if post_data else {}
            payload = _import_project_http(data)
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(payload, ensure_ascii=False).encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(str(e).encode('utf-8'))

    def _handle_post_projects_import_markpact(self, post_data: bytes):
        try:
            content_type = str(self.headers.get('Content-Type') or '')
            if 'multipart/form-data' in content_type:
                parsed = _parse_multipart_markpact(post_data, content_type)
                if isinstance(parsed, dict):
                    payload = parsed
                else:
                    filename, content = parsed
                    payload = _import_project_markpact(content, filename)
            else:
                data = json.loads(post_data.decode('utf-8', errors='replace')) if post_data else {}
                payload = _import_project_markpact(
                    base64.b64decode(str(data.get('content_base64') or '')),
                    str(data.get('filename') or 'project.md'),
                )
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(payload, ensure_ascii=False).encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(str(e).encode('utf-8'))

    def _handle_post_projects_delete(self, post_data: bytes):
        try:
            data = json.loads(post_data.decode('utf-8', errors='replace')) if post_data else {}
            from urllib.parse import unquote
            project_id = unquote(str(data.get('id') or data.get('project_id') or '').strip())
            if not project_id:
                payload = {"error": "missing project id"}
            else:
                payload = _delete_project(project_id)
            status = 404 if str(payload.get("error") or "").startswith("unknown project") else 200
            self.send_response(status)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(payload, ensure_ascii=False).encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(str(e).encode('utf-8'))

    def _handle_post_promote(self, post_data: bytes):
        try:
            data = json.loads(post_data.decode('utf-8', errors='replace')) if post_data else {}
            alt_name = str(data.get('alt', 'alt_a.html')).split('?')[0]
            stage = int(data.get('stage', 0))
            focus_scope = str(data.get('focus_scope', '') or '').strip()
            allowed_alts = {'alt_a.html', 'alt_b.html', 'alt_c.html'}
            if alt_name not in allowed_alts:
                payload = {"error": f"unsupported option file: {alt_name}"}
            elif stage < 0 or stage > 2:
                payload = {"error": f"unsupported stage: S{stage}"}
            else:
                from nexu.cinema_project_imports import promote_cinema_option
                promote_result = promote_cinema_option(
                    DIRECTORY,
                    alt_name=alt_name,
                    stage=stage,
                )
                if promote_result.get("error"):
                    payload = {"error": promote_result["error"]}
                else:
                    options_sync = _patch_option_previews(
                        stage, focus_scope=focus_scope
                    )
                    patch_files = list(options_sync.get("files") or [])
                    restore_files = list(
                        (promote_result.get("options_sync") or {}).get("files") or []
                    )
                    if restore_files and not patch_files:
                        options_sync = promote_result.get("options_sync") or options_sync
                    history_entry = _save_history_checkpoint(
                        action='promote',
                        stage=stage,
                        status='promoted',
                        extra=alt_name,
                    )
                    payload = {
                        "status": "promoted",
                        "alt": alt_name,
                        "stage": stage,
                        "stage_path": promote_result.get("stage_path"),
                        "history_checkpoint": history_entry,
                        "options_sync": options_sync,
                    }
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(payload, ensure_ascii=False).encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(str(e).encode('utf-8'))

    def _handle_post_iterate(self, post_data: bytes):
        handler = _IterateHandler(self, post_data)
        handler.handle()
    def do_POST(self):
        # Dispatch table for POST endpoints
        dispatch = {
            '/log': self._handle_post_log,
            '/manifest/apply-ledger': self._handle_post_manifest_apply_ledger,
            '/capsule/verify': lambda _: self._handle_post_capsule_verify(),
            '/propose/llm': self._handle_post_propose_llm,
            '/propose/goal': self._handle_post_propose_goal,
            '/history/restore': self._handle_post_history_restore,
            '/services/publish': self._handle_post_services_publish,
            '/services/start': self._handle_post_services_start,
            '/services/stop': self._handle_post_services_stop,
            '/services/delete': self._handle_post_services_delete,
            '/projects/activate': self._handle_post_projects_activate,
            '/promote': self._handle_post_promote,
            '/iterate': self._handle_post_iterate,
        }
        
        # Handle paths with multiple variants
        if self.path in ('/projects/import', '/projects/import/'):
            handler = self._handle_post_projects_import
        elif self.path in ('/projects/import/zip', '/projects/import/zip/'):
            handler = self._handle_post_projects_import_zip
        elif self.path in ('/projects/import/git', '/projects/import/git/'):
            handler = self._handle_post_projects_import_git
        elif self.path in ('/projects/import/http', '/projects/import/http/'):
            handler = self._handle_post_projects_import_http
        elif self.path in ('/projects/import/markpact', '/projects/import/markpact/'):
            handler = self._handle_post_projects_import_markpact
        elif self.path in ('/projects/delete', '/projects/delete/'):
            handler = self._handle_post_projects_delete
        else:
            handler = dispatch.get(self.path)
        
        if handler:
            if self.path != '/capsule/verify':
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                handler(post_data)
            else:
                handler(None)
            return
        
        super().do_POST()

    def do_DELETE(self):
        parts = _path_segments(self.path)
        if len(parts) == 3 and parts[0] == "projects" and parts[1] == "imported":
            project_id = parts[2]
            try:
                payload = _delete_imported_project(project_id)
                status = 404 if str(payload.get("error") or "").startswith("unknown imported project") else 200
                if payload.get("error") and status == 200:
                    status = 400
                body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(body)
                return
            except Exception as e:
                self.send_response(500)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(str(e).encode("utf-8"))
                return
        self.send_response(405)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

socketserver.TCPServer.allow_reuse_address = True


class ThreadingHTTPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    daemon_threads = True


with ThreadingHTTPServer((BIND_HOST, PORT), CustomHTTPRequestHandler) as httpd:
    httpd.serve_forever()
