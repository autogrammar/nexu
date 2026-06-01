import base64
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from http.client import HTTPConnection
from pathlib import Path
from socket import AF_INET, SOCK_STREAM, socket

import nexu
from nexu.cinema import _cinema_template_text, _render_cinema_template, write_cinema_nexu_hooks
from nexu.cinema_server import _render_server_script, start_cinema_player_server
from nexu.config import CinemaConfig, LLMConfig

CINEMA_LLM_MODEL = "openrouter/deepseek/deepseek-v4-pro"


@dataclass
class _LLMConfig:
    allow_network_calls: bool = False
    api_key_env: str = "OPENROUTER_API_KEY"
    model: str = "test-model"


def test_render_server_script_embeds_runtime_context() -> None:
    script = _render_server_script(
        Path("/tmp/workspace"),
        "demo",
        _LLMConfig(),
        CinemaConfig(),
        "/usr/bin/python3",
    )

    assert script.startswith("#!/usr/bin/python3")
    assert "WORKSPACE_PATH = '/tmp/workspace'" in script
    assert "CAPSULE_NAME = 'demo'" in script
    assert '"cinema_root": str(DIRECTORY)' in script
    assert '"workspace_root": str(ROOT_PATH)' in script
    assert "cinema_player_mtime" in script
    assert "_load_cinema_ui_profile" in script
    assert "load_cinema_ui_profile" in script
    assert "build_iterate_response_payload" in script
    assert "_llm_prompt_rules" in script
    assert "Intract LLM communication contract" in script
    assert "build_llm_contract_block" in script
    assert "build_llm_option_variants" in script
    assert "KPI overview workflow" not in script
    assert "Build chemical-calculator UIs" not in script
    assert "call_cinema_html_llm" in script
    assert "Markpact context pack" in script
    assert "_mp_payload = nexu_hooks.export_markpact_readme" in script
    assert "has_terminal_artifacts" in script
    assert "_compact_html_for_llm" in script
    assert "_compact_markpact_for_llm" in script
    assert "from nexu.fast_delivery import compact_html_for_llm" in script
    assert "from nexu.fast_delivery import compact_markpact_for_llm" in script
    assert "from nexu.fast_delivery import effective_markpact_mode" in script
    assert "from nexu.fast_delivery import is_options_ready_status" in script
    assert "DEFAULT_MARKPACT_CONTEXT_MODE" in script
    assert "DEFAULT_MARKPACT_CONTEXT_CHARS" in script
    assert "DEFAULT_HTML_CONTEXT_CHARS" in script
    assert "DEFAULT_LLM_TRACE_KEEP" in script
    assert "OPTION_GENERATION_MODE" in script
    assert "FAST_SCOPE_OPTIONS" in script
    assert "LLM_PATCH_OPTIONS" in script
    assert "_try_intract_fast_options" in script
    assert "_try_llm_patch_options" in script
    assert "_try_function_patch_options" in script
    assert "build_function_option_patches" in script
    assert "_call_llm_batch_options" in script
    assert "_generate_parallel_options" in script
    assert 'OPTION_GENERATION_MODE in {"batch", "single", "1"}' in script
    assert "parse_batch_alt_options" in script
    assert "from nexu.cinema_traces import write_llm_trace" in script
    assert "class ThreadingHTTPServer" in script
    assert 'self.send_header("Location", "cinema_player.html" + suffix)' in script
    assert "if not batch_html" not in script
    assert "ThreadPoolExecutor" in script
    assert '"llx"' not in script
    assert "proposed_options_offline" in script
    assert "proposed_options_by_intract_patch" in script
    assert "proposed_options_cached" in script
    assert "proposed_options_by_llm_patch" in script
    assert "supports_llm_patch_scope" in script
    assert "can_use_offline_fast_iterate" in script
    assert "cinema_has_offline_baseline" in script
    assert "FORCE_LLM" in script
    assert "FAST_SCOPE_OPTIONS" in script
    assert "OPTIONS_CACHE" in script
    assert "llm_patch_options" in script
    assert "_effective_markpact_mode" in script
    assert "_try_read_options_cache" in script
    assert "from nexu.fast_delivery import read_cached_options" in script
    assert "from nexu.fast_delivery import store_options_cache" in script
    assert "from nexu.cinema_iterate import build_iterate_response_payload" in script
    assert "SYS_EXE = '/usr/bin/python3'" in script
    assert "ALLOW_NETWORK_CALLS = False" in script
    assert "def _llm_network_allowed()" in script
    assert "def _llm_status_payload()" in script
    assert "import shutil" in script
    assert "def _service_id_from_host(self)" in script
    assert 'os.environ.get("NEXU_SERVICE_DOMAIN"' in script
    assert 'prefix = "/services/view/"' in script
    assert "shutil.copyfileobj(fh, self.wfile)" in script
    assert '"/llm/status"' in script
    assert '"/llm/traces"' in script
    assert '"/llm/trace"' in script
    assert "LLM_TRACE_DIR" in script
    assert '"cinema": {' in script
    assert "_cached_config(ROOT_PATH).llm.allow_network_calls" in script
    assert "API_KEY_ENV = 'OPENROUTER_API_KEY'" in script
    assert "DEFAULT_MODEL = 'test-model'" in script


def test_render_server_script_embeds_openrouter_model() -> None:
    llm = LLMConfig(
        provider="openrouter",
        model=CINEMA_LLM_MODEL,
        allow_network_calls=True,
    )
    script = _render_server_script(
        Path("/tmp/workspace"),
        "demo",
        llm,
        CinemaConfig(),
        "/usr/bin/python3",
    )

    assert f"DEFAULT_MODEL = '{CINEMA_LLM_MODEL}'" in script
    assert 'os.environ.get("LLM_MODEL")' in script


def test_write_cinema_nexu_hooks_uses_template(tmp_path: Path) -> None:
    write_cinema_nexu_hooks(tmp_path, Path("/tmp/workspace"), "demo")

    hooks = (tmp_path / "nexu_hooks.py").read_text(encoding="utf-8")

    assert "ROOT = Path('/tmp/workspace')" in hooks
    assert "CAPSULE = 'demo'" in hooks
    assert "__ROOT_PATH__" not in hooks
    assert "__CAPSULE_NAME__" not in hooks


def test_render_stage_template_injects_runtime_scripts() -> None:
    html = _render_cinema_template("stage0.html.tmpl", injected_scripts="<script>ok()</script>")

    assert "<title>Simple Calculator</title>" in html
    assert "<script>ok()</script>" in html
    assert "$INJECTED_SCRIPTS" not in html


def test_cinema_player_template_is_externalized() -> None:
    html = _cinema_template_text("cinema_player.html.tmpl")

    assert "<title>Nexu" in html
    assert (
        'src="stage0.html?role=workspace&amp;active=true&amp;mark=1&amp;'
        'calc=0&amp;review=0&amp;stage=0"'
    ) in html
    assert 'function calcEnabledForProject()' in html
    assert 'function flushPendingLogEvents()' in html
    assert 'src="alt_a.html?role=option&amp;pane=a&amp;mark=0&amp;calc=0"' in html
    assert 'id="goal-input"' in html
    assert "goalContractPayload" in html
    assert "focus_scope" in html
    assert "lastIteration" in html
    assert "buildSessionDiagnostics" in html
    assert "diagnostics: buildSessionDiagnostics()" in html
    assert "recordProjectsCatalog" in html
    assert "sessionDiagnostics.delete_flow" in html
    assert "focus_scope: data.focus_scope" in html
    assert "#functions requires an LLM" in html
    assert "offline templates" not in html
    assert 'id="llm-status-badge"' in html
    assert "refreshLlmStatus" in html
    assert 'id="tab-llm"' in html
    assert "flex-wrap: wrap;" in html
    assert "pointer-events: none;" in html
    assert 'id="llm-shell"' in html
    assert "loadLlmTraces" in html
    assert "renderTraceMarkdown" in html
    assert 'id="llm-trace-stats"' in html
    assert "copyLlmRequest" in html
    assert "downloadLlmRequest" in html
    assert "tokens est" in html
    assert "proposed_options_offline" in html
    assert "proposed_options_by_llm_patch" in html
    assert "LLM patch" in html
    assert "scope offline" in html
    assert "user_goal" in html
    assert "active_example_project" in html
    assert "goal_bootstrap" in html
    assert "hasIterationContext" in html
    assert "ledgerGoalFromPolicy" in html
    assert "syncGoalFromLedger" in html
    assert "server-offline-banner" in html
    assert "updateServerOfflineBanner" in html
    assert 'data-theme="dark"' in html
    assert "setCinemaTheme" in html
    assert "nexu-cinema-theme" in html
    assert 'id="projects-shell"' in html
    assert "importProjectZip" in html
    assert "importProjectMarkpact" in html
    assert "importProjectGit" in html
    assert "importProjectHttp" in html
    assert "/projects/import/zip" in html
    assert "/projects/import/markpact" in html
    assert "/projects/import/git" in html
    assert "/projects/import/http" in html
    assert "Upload Markpact" in html
    assert "README.markpact.md" in html
    assert "publishImportedProject" in html
    assert "Gotowe do edycji i publikacji" in html
    assert "ZIP, Markpact README, Git URL albo HTTP website" in html
    assert "onclick='activateProject(${idJson})'" in html
    assert 'onclick="activateProject(${idJson})"' not in html
    assert "onclick='event.stopPropagation(); previewImportedMarkpact(${idJson})'" in html
    assert "onclick='event.stopPropagation(); publishImportedProject(${idJson})'" in html
    assert "onclick='event.stopPropagation(); deleteProject(${idJson})'" in html
    assert "function deleteImportedProject(projectId)" in html
    assert "/projects/delete" in html
    assert "function promptForRequiredGoalOnEditor" in html
    assert (
        "const requestedTab = ['projects', 'editor', 'llm', 'services'].includes(bootTab)"
        in html
    )
    assert "if (needsGoal && tab === 'editor')" in html
    assert "if (mainTab !== 'editor') {" in html
    assert "if (tab !== 'editor')" in html
    assert "closeGoalPromptModal();" in html
    assert "iterationAllowedWithoutGoal" in html
    assert "FRAGMENT_ITERATE_MS" in html
    assert "skipEditorSwitch: !httpImport" in html
    assert "const needsGoal = activeProjectRequiresGoal()" in html
    assert "selected_fragments: selectedFragmentsPayload()" in html
    assert "function selectedFragmentsPayload()" in html
    assert "let scopedAnnotations = {}" in html
    assert "function annotationsFromLedgerForScope" in html
    assert "function loadActiveScopeAnnotations" in html
    assert "entryMatchesVisibleContractScope" in html
    assert "seenPolicyLines" in html
    assert "scope ${activeScope || 'all'}" in html
    assert "persistActiveScopeAnnotations()" in html
    assert "function scopeMarkLabel" in html
    assert "attachIframeSyncHandlers" in html
    assert "syncAllIframeVisuals(true)" in html
    assert "deletePublishedService" in html
    assert "/services/delete" in html
    assert "btn-service danger" in html


def test_render_server_script_embeds_project_import_routes() -> None:
    script = _render_server_script(
        Path("/tmp/workspace"),
        "demo",
        _LLMConfig(),
        CinemaConfig(),
        "/usr/bin/python3",
    )
    assert "/projects/import/zip" in script
    assert "/projects/import/git" in script
    assert "/projects/import/http" in script
    assert "def _import_project_zip(" in script
    assert "def _import_project_git(" in script
    assert "def _import_project_http(" in script
    assert "import_project_from_http" in script
    assert "def _delete_service(" in script
    assert "/services/delete" in script
    assert "import_project_from_markpact" in script
    assert "prefer_local_scope" in script
    assert "DASHBOARD_KINDS" in script
    assert "can_use_offline_fast_iterate" in script
    assert "resolve_marked_llm_context" in script
    assert "selected_fragments = data.get('selected_fragments')" in script
    assert "hard_delete_els" in script
    assert "REDESIGN these marked fragments within the selected scope" in script
    assert "should_block_full_html_iterate" in script
    assert "delete_workspace_project" in script


def test_cinema_server_imports_markpact_upload(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    cinema = tmp_path / "cinema"
    workspace.mkdir()
    cinema.mkdir()
    (cinema / "stage0.html").write_text(
        "<!DOCTYPE html><html><body><h1>Base</h1></body></html>",
        encoding="utf-8",
    )
    (cinema / "intract_policy_ledger.json").write_text("[]", encoding="utf-8")
    write_cinema_nexu_hooks(cinema, workspace, "demo")
    (cinema / "server.py").write_text(
        _render_server_script(
            workspace,
            "demo",
            LLMConfig(allow_network_calls=False, model=CINEMA_LLM_MODEL),
            CinemaConfig(),
            sys.executable,
        ),
        encoding="utf-8",
    )

    port = _free_port()
    nexu_src = str(Path(nexu.__file__).resolve().parent.parent)
    proc = subprocess.Popen(
        [sys.executable, str(cinema / "server.py"), str(port)],
        cwd=cinema,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env={**os.environ, "PYTHONPATH": nexu_src},
    )
    try:
        deadline = time.time() + 8.0
        while time.time() < deadline:
            try:
                conn = HTTPConnection("127.0.0.1", port, timeout=0.5)
                conn.request("GET", "/projects/catalog")
                conn.getresponse().read()
                conn.close()
                break
            except OSError:
                time.sleep(0.05)
        else:
            raise AssertionError("cinema server did not start")

        markdown = (
            "# Uploaded App\n\n"
            "```html markpact:file path=index.html\n"
            "<!DOCTYPE html><html><body><main><h1>Uploaded</h1></main></body></html>\n"
            "```\n"
        )
        body = json.dumps(
            {
                "filename": "uploaded-app.md",
                "content_base64": base64.b64encode(markdown.encode("utf-8")).decode("ascii"),
            }
        ).encode("utf-8")
        conn = HTTPConnection("127.0.0.1", port, timeout=10.0)
        conn.request(
            "POST",
            "/projects/import/markpact",
            body=body,
            headers={"Content-Type": "application/json", "Content-Length": str(len(body))},
        )
        resp = conn.getresponse()
        payload = json.loads(resp.read().decode("utf-8"))
        conn.close()

        assert resp.status == 200
        assert payload["status"] == "project_imported"
        assert payload["project"]["import_kind"] == "markpact"
        assert payload["project"]["id"].startswith("markpact-uploaded-app")
        project_dir = cinema / "imported_projects" / payload["project"]["id"]
        assert (project_dir / "README.markpact.md").read_text(encoding="utf-8") == markdown
        assert "Uploaded" in (project_dir / "source" / "index.html").read_text(encoding="utf-8")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


def test_write_cinema_nexu_hooks_includes_import_helpers(tmp_path: Path) -> None:
    write_cinema_nexu_hooks(tmp_path, Path("/tmp/workspace"), "demo")
    hooks = (tmp_path / "nexu_hooks.py").read_text(encoding="utf-8")
    assert "merged_projects_catalog" in hooks
    assert "import_project_from_zip" in hooks
    assert "import_project_from_markpact" in hooks
    assert "import_project_from_git" in hooks
    assert "import_project_from_http" in hooks
    assert "activate_imported_project" in hooks


def _free_port() -> int:
    with socket(AF_INET, SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def test_iterate_colors_scope_uses_offline_path(tmp_path: Path) -> None:
    cinema = tmp_path / "cinema"
    cinema.mkdir()
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "nexu.yaml").write_text(
        "project:\n  name: demo\ncinema:\n  fast_scope_options: true\n  force_llm: false\n",
        encoding="utf-8",
    )
    cap = workspace / ".nexu" / "capsules" / "demo"
    (cap / "src").mkdir(parents=True)
    (cap / "src" / "app.py").write_text("# demo\n", encoding="utf-8")
    (cap / "policy.json").write_text('{"keep":[],"delete":[]}', encoding="utf-8")
    (cinema / "active_project.json").write_text(
        json.dumps({"id": "web_app_calculator", "kind": "calculator", "title": "Calculator"}),
        encoding="utf-8",
    )
    stage_html = (
        "<!DOCTYPE html><html><head></head><body>"
        "<div class='calc-body'><div class='screen' id='screen'>0</div>"
        "<div class='grid'><div class='btn' id='btn-7'>7</div></div></div></body></html>"
    )
    (cinema / "stage0.html").write_text(stage_html, encoding="utf-8")
    (cinema / "intract_policy_ledger.json").write_text("[]", encoding="utf-8")
    write_cinema_nexu_hooks(cinema, workspace, "demo")
    llm = LLMConfig(allow_network_calls=False, model=CINEMA_LLM_MODEL)
    cinema_cfg = CinemaConfig(force_llm=False, fast_scope_options=True, options_cache=True)
    (cinema / "server.py").write_text(
        _render_server_script(workspace, "demo", llm, cinema_cfg, sys.executable),
        encoding="utf-8",
    )

    port = _free_port()
    nexu_src = str(Path(nexu.__file__).resolve().parent.parent)
    proc = subprocess.Popen(
        [sys.executable, str(cinema / "server.py"), str(port)],
        cwd=cinema,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env={**os.environ, "PYTHONPATH": nexu_src},
    )
    try:
        deadline = time.time() + 8.0
        while time.time() < deadline:
            try:
                conn = HTTPConnection("127.0.0.1", port, timeout=0.5)
                conn.request("GET", "/llm/status")
                conn.getresponse().read()
                conn.close()
                break
            except OSError:
                time.sleep(0.05)
        else:
            raise AssertionError("cinema server did not start")

        body = json.dumps(
            {
                "iteration_mode": "goal_options",
                "focus_scope": "colors",
                "focus_scope_label": "#colors",
                "current_stage": 0,
                "prompt": "",
                "annotations": [],
            }
        ).encode("utf-8")
        conn = HTTPConnection("127.0.0.1", port, timeout=10.0)
        conn.request(
            "POST",
            "/iterate",
            body=body,
            headers={"Content-Type": "application/json", "Content-Length": str(len(body))},
        )
        resp = conn.getresponse()
        payload = json.loads(resp.read().decode("utf-8"))
        conn.close()

        assert resp.status == 200
        assert payload["status"] == "proposed_options_offline"
        assert payload["focus_scope"] == "colors"
        assert payload["focus_scope_label"] == "#colors"
        assert len(payload.get("options_written") or []) == 3
        alt_a = (cinema / "alt_a.html").read_text(encoding="utf-8")
        assert "nexu-scope-variant" in alt_a
        assert "colors:" in " ".join(payload["options_written"]).lower()

        conn = HTTPConnection("127.0.0.1", port, timeout=10.0)
        conn.request(
            "POST",
            "/iterate",
            body=body,
            headers={"Content-Type": "application/json", "Content-Length": str(len(body))},
        )
        cached_resp = conn.getresponse()
        cached_payload = json.loads(cached_resp.read().decode("utf-8"))
        conn.close()
        assert cached_resp.status == 200
        assert cached_payload["status"] == "proposed_options_cached"
        assert cached_payload.get("options_written") == payload.get("options_written")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()


def test_iterate_dashboard_kinds_colors_prefers_offline_before_llm(
    tmp_path: Path,
) -> None:
    """Dashboard-family kinds should use offline path before LLM patch (like imported/web)."""
    for kind, project_id in (
        ("dashboard", "web_app_dashboard"),
        ("slice", "web_app_slice"),
    ):
        cinema = tmp_path / f"cinema_{kind}"
        cinema.mkdir()
        workspace = tmp_path / f"workspace_{kind}"
        workspace.mkdir()
        (workspace / "nexu.yaml").write_text(
            "\n".join(
                [
                    "project:",
                    "  name: demo",
                    "cinema:",
                    "  fast_scope_options: true",
                    "  force_llm: false",
                    "  llm_patch_options: true",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        cap = workspace / ".nexu" / "capsules" / "demo"
        (cap / "src").mkdir(parents=True)
        (cap / "src" / "app.py").write_text("# demo\n", encoding="utf-8")
        (cap / "policy.json").write_text('{"keep":[],"delete":[]}', encoding="utf-8")
        (cinema / "active_project.json").write_text(
            json.dumps({"id": project_id, "kind": kind, "title": kind.title()}),
            encoding="utf-8",
        )
        stage_html = (
            "<!DOCTYPE html><html><head></head><body>"
            "<div class='app-shell kpi-grid'><section class='kpi-card'>"
            "Revenue</section></div></body></html>"
        )
        for name in ("stage0.html", "stage1.html", "stage2.html"):
            (cinema / name).write_text(stage_html, encoding="utf-8")
        (cinema / "intract_policy_ledger.json").write_text("[]", encoding="utf-8")
        write_cinema_nexu_hooks(cinema, workspace, "demo")
        llm = LLMConfig(allow_network_calls=True, model=CINEMA_LLM_MODEL)
        cinema_cfg = CinemaConfig(
            force_llm=False,
            fast_scope_options=True,
            llm_patch_options=True,
            options_cache=False,
        )
        (cinema / "server.py").write_text(
            _render_server_script(workspace, "demo", llm, cinema_cfg, sys.executable),
            encoding="utf-8",
        )

        port = _free_port()
        nexu_src = str(Path(nexu.__file__).resolve().parent.parent)
        proc = subprocess.Popen(
            [sys.executable, str(cinema / "server.py"), str(port)],
            cwd=cinema,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env={**os.environ, "PYTHONPATH": nexu_src},
        )
        try:
            deadline = time.time() + 8.0
            while time.time() < deadline:
                try:
                    conn = HTTPConnection("127.0.0.1", port, timeout=0.5)
                    conn.request("GET", "/llm/status")
                    conn.getresponse().read()
                    conn.close()
                    break
                except OSError:
                    time.sleep(0.05)
            else:
                raise AssertionError("cinema server did not start")

            body = json.dumps(
                {
                    "iteration_mode": "goal_options",
                    "focus_scope": "colors",
                    "focus_scope_label": "#colors",
                    "current_stage": 0,
                    "prompt": "",
                    "annotations": [],
                    "force_refresh": True,
                }
            ).encode("utf-8")
            conn = HTTPConnection("127.0.0.1", port, timeout=10.0)
            conn.request(
                "POST",
                "/iterate",
                body=body,
                headers={
                    "Content-Type": "application/json",
                    "Content-Length": str(len(body)),
                },
            )
            resp = conn.getresponse()
            payload = json.loads(resp.read().decode("utf-8"))
            conn.close()

            assert resp.status == 200, kind
            assert payload["status"] == "proposed_options_offline", (
                f"{kind}: expected offline before LLM patch, got {payload['status']}"
            )
            assert payload["focus_scope"] == "colors"
            assert len(payload.get("options_written") or []) == 3
            alt_a = (cinema / "alt_a.html").read_text(encoding="utf-8")
            assert "nexu-scope-variant" in alt_a
            assert "colors:" in " ".join(payload["options_written"]).lower()
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()


def test_iterate_colors_scope_uses_llm_patch_when_available(tmp_path: Path) -> None:
    cinema = tmp_path / "cinema"
    cinema.mkdir()
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "nexu.yaml").write_text(
        "\n".join(
            [
                "project:",
                "  name: demo",
                "llm:",
                "  provider: openrouter",
                "  model: test-model",
                "  api_key_env: OPENROUTER_API_KEY",
                "  allow_network_calls: true",
                "cinema:",
                "  fast_scope_options: true",
                "  llm_patch_options: true",
                "  options_cache: false",
                "  force_llm: false",
                "",
            ]
        ),
        encoding="utf-8",
    )
    cap = workspace / ".nexu" / "capsules" / "demo"
    (cap / "src").mkdir(parents=True)
    (cap / "src" / "app.py").write_text("# demo\n", encoding="utf-8")
    (cap / "policy.json").write_text('{"keep":[],"delete":[]}', encoding="utf-8")
    (cinema / "active_project.json").write_text(
        json.dumps({"id": "web_app_calculator", "kind": "calculator", "title": "Calculator"}),
        encoding="utf-8",
    )
    stage_html = (
        "<!DOCTYPE html><html><head></head><body>"
        "<div class='calc-body'><div class='screen' id='screen'>0</div>"
        "<div class='grid'><div class='btn' id='btn-7'>7</div></div></div></body></html>"
    )
    (cinema / "stage0.html").write_text(stage_html, encoding="utf-8")
    (cinema / "intract_policy_ledger.json").write_text("[]", encoding="utf-8")
    write_cinema_nexu_hooks(cinema, workspace, "demo")
    llm = LLMConfig(allow_network_calls=True, model="test-model")
    cinema_cfg = CinemaConfig(
        force_llm=False,
        fast_scope_options=True,
        llm_patch_options=True,
        options_cache=False,
    )
    (cinema / "server.py").write_text(
        _render_server_script(workspace, "demo", llm, cinema_cfg, sys.executable),
        encoding="utf-8",
    )
    hooks_dir = tmp_path / "hooks"
    hooks_dir.mkdir()
    (hooks_dir / "sitecustomize.py").write_text(
        """
import nexu.cinema_llm

def fake_call_cinema_text_llm(*args, **kwargs):
    return (
        '{"variants":{'
        '"alt_a.html":{"label":"Option A (colors: blue)","css":".screen{color:#38bdf8;}"}'
        ',"alt_b.html":{"label":"Option B (colors: white)","css":".screen{color:#fff;}"}'
        ',"alt_c.html":{"label":"Option C (colors: pink)","css":".screen{color:#f47;}"}'
        '}}',
        None,
    )

nexu.cinema_llm.call_cinema_text_llm = fake_call_cinema_text_llm
""".lstrip(),
        encoding="utf-8",
    )

    port = _free_port()
    nexu_src = str(Path(nexu.__file__).resolve().parent.parent)
    proc = subprocess.Popen(
        [sys.executable, str(cinema / "server.py"), str(port)],
        cwd=cinema,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env={
            **os.environ,
            "PYTHONPATH": f"{hooks_dir}{os.pathsep}{nexu_src}",
            "OPENROUTER_API_KEY": "test-key",
        },
    )
    try:
        deadline = time.time() + 8.0
        while time.time() < deadline:
            try:
                conn = HTTPConnection("127.0.0.1", port, timeout=0.5)
                conn.request("GET", "/llm/status")
                conn.getresponse().read()
                conn.close()
                break
            except OSError:
                time.sleep(0.05)
        else:
            raise AssertionError("cinema server did not start")

        body = json.dumps(
            {
                "iteration_mode": "goal_options",
                "focus_scope": "colors",
                "focus_scope_label": "#colors",
                "current_stage": 0,
                "prompt": "",
                "annotations": [],
                "force_refresh": True,
            }
        ).encode("utf-8")
        conn = HTTPConnection("127.0.0.1", port, timeout=10.0)
        conn.request(
            "POST",
            "/iterate",
            body=body,
            headers={"Content-Type": "application/json", "Content-Length": str(len(body))},
        )
        resp = conn.getresponse()
        payload = json.loads(resp.read().decode("utf-8"))
        conn.close()

        assert resp.status == 200
        assert payload["status"] == "proposed_options_by_llm_patch"
        assert payload["options_written"] == [
            "Option A (colors: blue)",
            "Option B (colors: white)",
            "Option C (colors: pink)",
        ]
        assert ".screen{color:#38bdf8;}" in (cinema / "alt_a.html").read_text(
            encoding="utf-8"
        )
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()


def test_effective_markpact_mode_off_for_visual_scope() -> None:
    script = _render_server_script(
        Path("/tmp/workspace"),
        "demo",
        _LLMConfig(),
        CinemaConfig(markpact_context_mode="summary"),
        "/usr/bin/python3",
    )
    assert "def _effective_markpact_mode(" in script
    assert "effective_markpact_mode(" in script
    assert "default_mode=default" in script
    assert "env_off=env_off" in script


def test_iterate_functions_scope_skips_offline_fast_path(tmp_path: Path) -> None:
    cinema = tmp_path / "cinema"
    cinema.mkdir()
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "nexu.yaml").write_text(
        "project:\n  name: demo\ncinema:\n  fast_scope_options: true\n  force_llm: false\n",
        encoding="utf-8",
    )
    cap = workspace / ".nexu" / "capsules" / "demo"
    (cap / "src").mkdir(parents=True)
    (cap / "src" / "app.py").write_text("# demo\n", encoding="utf-8")
    (cap / "policy.json").write_text('{"keep":[],"delete":[]}', encoding="utf-8")
    (cinema / "active_project.json").write_text(
        json.dumps({"id": "web_app_calculator", "kind": "calculator", "title": "Calculator"}),
        encoding="utf-8",
    )
    stage_html = (
        "<!DOCTYPE html><html><head></head><body>"
        "<div class='calc-body'><div class='screen' id='screen'>0</div>"
        "<div class='grid'><div class='btn' id='btn-7'>7</div></div></div></body></html>"
    )
    (cinema / "stage0.html").write_text(stage_html, encoding="utf-8")
    (cinema / "intract_policy_ledger.json").write_text("[]", encoding="utf-8")
    write_cinema_nexu_hooks(cinema, workspace, "demo")
    llm = LLMConfig(allow_network_calls=False, model=CINEMA_LLM_MODEL)
    cinema_cfg = CinemaConfig(force_llm=False, fast_scope_options=True, options_cache=False)
    (cinema / "server.py").write_text(
        _render_server_script(workspace, "demo", llm, cinema_cfg, sys.executable),
        encoding="utf-8",
    )

    port = _free_port()
    nexu_src = str(Path(nexu.__file__).resolve().parent.parent)
    proc = subprocess.Popen(
        [sys.executable, str(cinema / "server.py"), str(port)],
        cwd=cinema,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env={**os.environ, "PYTHONPATH": nexu_src},
    )
    try:
        deadline = time.time() + 8.0
        while time.time() < deadline:
            try:
                conn = HTTPConnection("127.0.0.1", port, timeout=0.5)
                conn.request("GET", "/llm/status")
                conn.getresponse().read()
                conn.close()
                break
            except OSError:
                time.sleep(0.05)
        else:
            raise AssertionError("cinema server did not start")

        body = json.dumps(
            {
                "iteration_mode": "goal_options",
                "focus_scope": "functions",
                "focus_scope_label": "#functions",
                "current_stage": 0,
                "prompt": "",
                "annotations": [],
            }
        ).encode("utf-8")
        conn = HTTPConnection("127.0.0.1", port, timeout=10.0)
        conn.request(
            "POST",
            "/iterate",
            body=body,
            headers={"Content-Type": "application/json", "Content-Length": str(len(body))},
        )
        resp = conn.getresponse()
        payload = json.loads(resp.read().decode("utf-8"))
        conn.close()

        assert resp.status == 200
        assert payload["status"].startswith("llm_failed")
        assert payload["focus_scope"] == "functions"
        assert "proposed_options_offline" not in payload["status"]
        assert payload.get("error")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()


def test_iterate_colors_without_stage0_skips_offline(tmp_path: Path) -> None:
    cinema = tmp_path / "cinema"
    cinema.mkdir()
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "nexu.yaml").write_text(
        "project:\n  name: demo\ncinema:\n  fast_scope_options: true\n  force_llm: false\n",
        encoding="utf-8",
    )
    cap = workspace / ".nexu" / "capsules" / "demo"
    (cap / "src").mkdir(parents=True)
    (cap / "src" / "app.py").write_text("# demo\n", encoding="utf-8")
    (cap / "policy.json").write_text('{"keep":[],"delete":[]}', encoding="utf-8")
    (cinema / "active_project.json").write_text(
        json.dumps({"id": "web_app_calculator", "kind": "calculator", "title": "Calculator"}),
        encoding="utf-8",
    )
    (cinema / "intract_policy_ledger.json").write_text("[]", encoding="utf-8")
    write_cinema_nexu_hooks(cinema, workspace, "demo")
    llm = LLMConfig(allow_network_calls=False, model=CINEMA_LLM_MODEL)
    cinema_cfg = CinemaConfig(force_llm=False, fast_scope_options=True, options_cache=False)
    (cinema / "server.py").write_text(
        _render_server_script(workspace, "demo", llm, cinema_cfg, sys.executable),
        encoding="utf-8",
    )

    port = _free_port()
    nexu_src = str(Path(nexu.__file__).resolve().parent.parent)
    proc = subprocess.Popen(
        [sys.executable, str(cinema / "server.py"), str(port)],
        cwd=cinema,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env={**os.environ, "PYTHONPATH": nexu_src},
    )
    try:
        deadline = time.time() + 8.0
        while time.time() < deadline:
            try:
                conn = HTTPConnection("127.0.0.1", port, timeout=0.5)
                conn.request("GET", "/llm/status")
                conn.getresponse().read()
                conn.close()
                break
            except OSError:
                time.sleep(0.05)
        else:
            raise AssertionError("cinema server did not start")

        body = json.dumps(
            {
                "iteration_mode": "goal_options",
                "focus_scope": "colors",
                "focus_scope_label": "#colors",
                "current_stage": 0,
                "prompt": "",
                "annotations": [],
            }
        ).encode("utf-8")
        conn = HTTPConnection("127.0.0.1", port, timeout=10.0)
        conn.request(
            "POST",
            "/iterate",
            body=body,
            headers={"Content-Type": "application/json", "Content-Length": str(len(body))},
        )
        resp = conn.getresponse()
        payload = json.loads(resp.read().decode("utf-8"))
        conn.close()

        assert resp.status == 200
        assert payload["status"].startswith("llm_failed")
        assert payload["focus_scope"] == "colors"
        assert payload["status"] != "proposed_options_offline"
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()


def test_start_cinema_player_server_returns_url_without_opening(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr("nexu.cinema_server.start_persistent_http_server", lambda *_: 8099)

    url = start_cinema_player_server(tmp_path, Path("/tmp/workspace"), "demo", open_browser=False)

    assert url == "http://127.0.0.1:8099/cinema_player.html"


def test_projects_import_zip_endpoint(tmp_path: Path) -> None:
    import base64
    import zipfile

    cinema = tmp_path / "cinema"
    cinema.mkdir()
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "nexu.yaml").write_text("project:\n  name: demo\n", encoding="utf-8")
    write_cinema_nexu_hooks(cinema, workspace, "demo")
    llm = LLMConfig(allow_network_calls=False, model=CINEMA_LLM_MODEL)
    (cinema / "server.py").write_text(
        _render_server_script(workspace, "demo", llm, CinemaConfig(), sys.executable),
        encoding="utf-8",
    )

    archive = tmp_path / "pkg.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("app/index.html", "<html><body>ok</body></html>")

    port = _free_port()
    nexu_src = str(Path(nexu.__file__).resolve().parent.parent)
    proc = subprocess.Popen(
        [sys.executable, str(cinema / "server.py"), str(port)],
        cwd=cinema,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env={**os.environ, "PYTHONPATH": nexu_src},
    )
    try:
        deadline = time.time() + 8.0
        while time.time() < deadline:
            try:
                conn = HTTPConnection("127.0.0.1", port, timeout=0.5)
                conn.request("GET", "/health")
                conn.getresponse().read()
                conn.close()
                break
            except OSError:
                time.sleep(0.05)
        else:
            raise AssertionError("cinema server did not start")

        body = json.dumps(
            {
                "filename": "pkg.zip",
                "content_base64": base64.b64encode(archive.read_bytes()).decode("ascii"),
            }
        ).encode("utf-8")
        conn = HTTPConnection("127.0.0.1", port, timeout=10.0)
        conn.request(
            "POST",
            "/projects/import/zip",
            body=body,
            headers={"Content-Type": "application/json", "Content-Length": str(len(body))},
        )
        resp = conn.getresponse()
        payload = json.loads(resp.read().decode("utf-8"))
        conn.close()

        assert resp.status == 200
        assert payload["status"] == "project_imported"
        assert payload["project"]["kind"] == "imported"

        conn = HTTPConnection("127.0.0.1", port, timeout=10.0)
        conn.request("GET", "/projects/catalog")
        resp = conn.getresponse()
        catalog = json.loads(resp.read().decode("utf-8"))
        conn.close()
        imported = [p for p in catalog.get("projects", []) if p.get("imported")]
        assert imported
        entry = imported[0]
        assert entry.get("source_url")
        assert entry.get("file_count", 0) >= 1
        assert entry.get("total_bytes", 0) > 0
        project_id = entry["id"]

        conn = HTTPConnection("127.0.0.1", port, timeout=10.0)
        conn.request("GET", f"/projects/imported/{project_id}/markpact")
        resp = conn.getresponse()
        markpact = json.loads(resp.read().decode("utf-8"))
        conn.close()
        assert resp.status == 200
        assert "Markpact migration" in markpact.get("markdown", "")

        conn = HTTPConnection("127.0.0.1", port, timeout=10.0)
        conn.request("DELETE", f"/projects/imported/{project_id}")
        resp = conn.getresponse()
        deleted = json.loads(resp.read().decode("utf-8"))
        conn.close()
        assert resp.status == 200
        assert deleted.get("status") == "deleted"
        assert not (cinema / "imported_projects" / project_id).exists()
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()


def test_delete_imported_http_domain_id_via_api(tmp_path: Path) -> None:
    cinema = tmp_path / "cinema"
    cinema.mkdir()
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "nexu.yaml").write_text("project:\n  name: demo\n", encoding="utf-8")
    write_cinema_nexu_hooks(cinema, workspace, "demo")
    llm = LLMConfig(allow_network_calls=False, model=CINEMA_LLM_MODEL)
    (cinema / "server.py").write_text(
        _render_server_script(workspace, "demo", llm, CinemaConfig(), sys.executable),
        encoding="utf-8",
    )

    project_id = "http-malortgdynia.pl"
    project_dir = cinema / "imported_projects" / project_id
    project_dir.mkdir(parents=True)
    (project_dir / "project.json").write_text(
        json.dumps(
            {
                "id": project_id,
                "title": "Malortgdynia.Pl",
                "import_kind": "http",
                "source": "https://malortgdynia.pl/",
            }
        ),
        encoding="utf-8",
    )
    (project_dir / "source").mkdir()
    (project_dir / "README.markpact.md").write_text("# Markpact migration\n", encoding="utf-8")

    port = _free_port()
    nexu_src = str(Path(nexu.__file__).resolve().parent.parent)
    proc = subprocess.Popen(
        [sys.executable, str(cinema / "server.py"), str(port)],
        cwd=cinema,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env={**os.environ, "PYTHONPATH": nexu_src},
    )
    try:
        deadline = time.time() + 8.0
        while time.time() < deadline:
            try:
                conn = HTTPConnection("127.0.0.1", port, timeout=0.5)
                conn.request("GET", "/health")
                conn.getresponse().read()
                conn.close()
                break
            except OSError:
                time.sleep(0.05)
        else:
            raise AssertionError("cinema server did not start")

        conn = HTTPConnection("127.0.0.1", port, timeout=10.0)
        conn.request("GET", "/projects/catalog")
        resp = conn.getresponse()
        catalog = json.loads(resp.read().decode("utf-8"))
        conn.close()
        entry = next(p for p in catalog["projects"] if p["id"] == project_id)
        assert entry["deletable"] is True
        assert entry["imported"] is True

        conn = HTTPConnection("127.0.0.1", port, timeout=10.0)
        conn.request("DELETE", f"/projects/imported/{project_id}/")
        resp = conn.getresponse()
        deleted = json.loads(resp.read().decode("utf-8"))
        conn.close()
        assert resp.status == 200
        assert deleted.get("status") == "deleted"
        assert deleted.get("id") == project_id
        assert not project_dir.exists()
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
