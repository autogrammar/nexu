"""Import arbitrary projects into Cinema and migrate them to Markpact first."""
# ruff: noqa: E501

from __future__ import annotations

import base64
import json
import re
import shutil
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

from repatch import fetch_complete_web_page, organize_html_project_dir, organize_result_manifest

from .cinema_http_preprocess import (
    ensure_http_preprocess_artifacts,
    prepare_http_preview_html,
    preprocess_http_import,
)
from .cinema_policy import (
    ensure_http_option_previews_from_stage0,
    ensure_option_previews_from_stages,
    refresh_imported_policy_snapshot,
    reset_cinema_policy_ledger,
)
from .cinema_projects import (
    ACTIVE_PROJECT_FILE,
    activate_example_project,
    delete_example_project,
    list_project_catalog,
    load_active_project,
)
from .cinema_scope import scope_meta_for_project
from .cinema_scripts import inject_cinema_shield, write_cinema_inject_files
from .cinema_traces import list_llm_traces

IMPORTS_DIR = "imported_projects"
MAX_EMBED_FILES = 18
MAX_FILE_BYTES = 60_000
MAX_ZIP_BYTES = 25_000_000
MAX_UNCOMPRESSED_BYTES = 100_000_000
MAX_ZIP_FILES = 500
MAX_HTTP_BYTES = 5_000_000
MAX_STYLESHEET_BYTES = 500_000
MAX_STYLESHEETS = 5
HTTP_TIMEOUT = 30
HTTP_USER_AGENT = "Mozilla/5.0 (compatible; nexu-cinema-import/1.0; +https://github.com/semcod/nexu)"
_LINK_TAG_RE = re.compile(r"<link\b[^>]*>", re.IGNORECASE)
_HREF_ATTR_RE = re.compile(r"""\bhref\s*=\s*(['"])(.*?)\1""", re.IGNORECASE)
_REL_ATTR_RE = re.compile(r"""\brel\s*=\s*(['"])(.*?)\1""", re.IGNORECASE)
_CHARSET_RE = re.compile(r"charset=([^\s;]+)", re.IGNORECASE)
GIT_TIMEOUT = 120
SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "dist", "build", "__pycache__"}
IMPORTED_ID_RE = re.compile(r"^(zip|git|http)-[a-zA-Z0-9._-]+$")
DEFAULT_FALLBACK_PROJECT = "web_app_calculator"


_IMPORT_PREVIEW_ATTR = 'data-nexu-import-preview="http"'
_CALCULATOR_POLLUTION_RE = re.compile(
    r"(?:"
    r"calc-body|"
    r'id=["\']functions["\']|'
    r"Scientific Calculator|"
    r'class=["\'][^"\']*\bbtn-sci\b|'
    r'data-project=["\']web_app_calculator["\']'
    r")",
    re.IGNORECASE,
)


def http_stage_matches_import(html: str, meta: dict[str, Any]) -> bool:
    """True when live stage HTML still reflects the stored HTTP import snapshot."""
    text = str(html or "")
    if not text.strip():
        return False
    if _CALCULATOR_POLLUTION_RE.search(text):
        return False
    project_id = str(meta.get("id") or "")
    if not project_id.startswith("http-"):
        return True
    if _IMPORT_PREVIEW_ATTR in text:
        netloc = urlparse(_source_url_from_meta(meta)).netloc.lower()
        if netloc and netloc in text.lower():
            return True
    netloc = urlparse(_source_url_from_meta(meta)).netloc.lower()
    return bool(netloc and netloc in text.lower())


def reject_import_stage_replacement(html: str, meta: dict[str, Any]) -> str | None:
    """Block full-page writes that replace an HTTP import with unrelated template HTML."""
    project_id = str(meta.get("id") or "")
    import_kind = str(meta.get("import_kind") or _import_kind_from_id(project_id))
    if import_kind != "http" and not project_id.startswith("http-"):
        return None
    if http_stage_matches_import(html, meta):
        return None
    return (
        "Rejected full-page replacement: HTML does not match imported site snapshot "
        f"({project_id or import_kind})"
    )


def restore_http_import_stages_if_needed(cinema_dir: Path, meta: dict[str, Any]) -> dict[str, Any]:
    """Rebuild stage0 and option previews when live HTML drifted from the import seed."""
    project_id = str(meta.get("id") or "")
    if not project_id.startswith("http-"):
        return {"status": "skipped", "files": []}
    stage0_path = cinema_dir / "stage0.html"
    current = stage0_path.read_text(encoding="utf-8") if stage0_path.is_file() else ""
    if current and http_stage_matches_import(current, meta):
        return {"status": "unchanged", "files": []}
    stage0_html = _build_http_preview_stage0(meta)
    if not stage0_html:
        return {"status": "error", "reason": "missing import seed HTML", "files": []}
    stage0_path.write_text(stage0_html, encoding="utf-8")
    options_sync = ensure_http_option_previews_from_stage0(cinema_dir)
    return {
        "status": "restored",
        "files": ["stage0.html", *list(options_sync.get("files") or [])],
        "options_sync": options_sync,
    }


def _slug(value: str) -> str:
    safe = re.sub(r"[^a-zA-Z0-9._-]+", "-", value).strip("-").lower()
    return safe[:64] or "imported-project"


def _imports_root(cinema_dir: Path) -> Path:
    root = cinema_dir / IMPORTS_DIR
    root.mkdir(parents=True, exist_ok=True)
    return root


def _project_dir(cinema_dir: Path, project_id: str) -> Path:
    return _imports_root(cinema_dir) / project_id


def _validate_http_url(url: str) -> str | None:
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"}:
        return "URL must be http or https"
    if not parsed.netloc:
        return "invalid URL"
    return None


def _validate_git_url(url: str) -> str | None:
    source = url.strip()
    if not source:
        return "git_url required"
    lowered = source.lower()
    if lowered.startswith("file:"):
        return "file:// URLs are not allowed"
    if lowered.startswith(("http://", "https://", "git@", "ssh://")):
        return None
    if re.match(r"^[a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+:", source):
        return None
    return "unsupported git URL scheme"


def _safe_extract_zip(zip_path: Path, target: Path) -> None:
    if zip_path.stat().st_size > MAX_ZIP_BYTES:
        raise ValueError(f"zip exceeds {MAX_ZIP_BYTES} bytes")
    with zipfile.ZipFile(zip_path) as zf:
        infos = zf.infolist()
        if len(infos) > MAX_ZIP_FILES:
            raise ValueError(f"zip contains more than {MAX_ZIP_FILES} files")
        total_uncompressed = 0
        for info in infos:
            dest = (target / info.filename).resolve()
            if not str(dest).startswith(str(target.resolve())):
                raise ValueError(f"unsafe zip path: {info.filename}")
            total_uncompressed += max(info.file_size, 0)
            if total_uncompressed > MAX_UNCOMPRESSED_BYTES:
                raise ValueError("zip uncompressed size limit exceeded")
        zf.extractall(target)


def _charset_from_content_type(content_type: str) -> str | None:
    match = _CHARSET_RE.search(content_type)
    if not match:
        return None
    return match.group(1).strip('"\'').lower() or None


def _decode_http_bytes(body: bytes, *, content_type: str, charset: str | None = None) -> str:
    encoding = charset or _charset_from_content_type(content_type) or "utf-8"
    try:
        return body.decode(encoding)
    except (LookupError, UnicodeDecodeError):
        return body.decode("utf-8", errors="replace")


def _document_base_href(url: str) -> str:
    parsed = urlparse(url.strip())
    path = parsed.path or "/"
    if not path.endswith("/"):
        last = path.rsplit("/", 1)[-1]
        if "." in last:
            path = path.rsplit("/", 1)[0] + "/"
        else:
            path = path + "/"
    return f"{parsed.scheme}://{parsed.netloc}{path}"


def _fetch_http_body(url: str) -> tuple[bytes, str, str, str | None]:
    err = _validate_http_url(url)
    if err:
        raise ValueError(err)
    req = Request(url.strip(), headers={"User-Agent": HTTP_USER_AGENT})
    with urlopen(req, timeout=HTTP_TIMEOUT) as resp:
        final_url = str(getattr(resp, "url", None) or url.strip())
        content_type = str(resp.headers.get("Content-Type") or "text/html")
        charset = _charset_from_content_type(content_type)
        chunks: list[bytes] = []
        total = 0
        while True:
            block = resp.read(65536)
            if not block:
                break
            total += len(block)
            if total > MAX_HTTP_BYTES:
                raise ValueError(f"HTTP response exceeds {MAX_HTTP_BYTES} bytes")
            chunks.append(block)
    return b"".join(chunks), content_type, final_url, charset


def _same_origin(url: str, base_url: str) -> bool:
    left = urlparse(url)
    right = urlparse(base_url)
    return left.scheme in {"http", "https"} and left.netloc == right.netloc


def _extract_stylesheet_hrefs(html: str) -> list[str]:
    hrefs: list[str] = []
    for tag in _LINK_TAG_RE.findall(html):
        rel_match = _REL_ATTR_RE.search(tag)
        if not rel_match or "stylesheet" not in rel_match.group(2).lower():
            continue
        href_match = _HREF_ATTR_RE.search(tag)
        if href_match:
            hrefs.append(href_match.group(2).strip())
    return hrefs


def _fetch_http_stylesheets(
    html: str,
    *,
    page_url: str,
    assets_dir: Path,
) -> tuple[list[dict[str, str]], list[str]]:
    saved: list[dict[str, str]] = []
    errors: list[str] = []
    assets_dir.mkdir(parents=True, exist_ok=True)
    for index, href in enumerate(_extract_stylesheet_hrefs(html)):
        if index >= MAX_STYLESHEETS:
            break
        absolute = urljoin(page_url, href)
        if not _same_origin(absolute, page_url):
            continue
        try:
            body, content_type, _, _ = _fetch_http_body(absolute)
        except (HTTPError, URLError, TimeoutError, ValueError) as exc:
            errors.append(f"{href}: {exc}"[:200])
            continue
        if len(body) > MAX_STYLESHEET_BYTES:
            errors.append(f"{href}: exceeds {MAX_STYLESHEET_BYTES} bytes"[:200])
            continue
        rel_name = f"asset-{index}.css"
        (assets_dir / rel_name).write_bytes(body)
        saved.append(
            {
                "href": href,
                "local": f"assets/{rel_name}",
                "content_type": content_type,
            }
        )
    return saved, errors


def _rewrite_local_stylesheets(html: str, *, project_id: str, saved: list[dict[str, str]]) -> str:
    if not saved:
        return html
    href_to_local = {item["href"]: item["local"] for item in saved}

    def _replace_tag(tag: str) -> str:
        href_match = _HREF_ATTR_RE.search(tag)
        if not href_match:
            return tag
        href = href_match.group(2).strip()
        local = href_to_local.get(href)
        if not local:
            return tag
        cinema_path = f"imported_projects/{project_id}/source/{local}"
        return _HREF_ATTR_RE.sub(f'href="{cinema_path}"', tag, count=1)

    return _LINK_TAG_RE.sub(lambda match: _replace_tag(match.group(0)), html)


def _rewrite_local_asset_refs(html: str, *, project_id: str, assets: list[dict[str, Any]]) -> str:
    """Rewrite mirrored source asset paths so preview HTML can load them from Cinema."""
    if not assets:
        return html
    rewritten = html
    seen: set[str] = set()
    for item in assets:
        local = str(item.get("local") or "").strip()
        if not local or local in seen:
            continue
        seen.add(local)
        cinema_path = f"imported_projects/{project_id}/source/{local}"
        rewritten = rewritten.replace(f'"{local}"', f'"{cinema_path}"')
        rewritten = rewritten.replace(f"'{local}'", f"'{cinema_path}'")
        rewritten = rewritten.replace(f"{local} ", f"{cinema_path} ")
        rewritten = rewritten.replace(f"{local},", f"{cinema_path},")
    return rewritten


def _fetch_meta_assets(fetch_meta: dict[str, Any]) -> list[dict[str, Any]]:
    assets: list[dict[str, Any]] = []
    seen: set[str] = set()
    for key in ("assets", "stylesheets", "images"):
        value = fetch_meta.get(key)
        if not isinstance(value, list):
            continue
        for item in value:
            if not isinstance(item, dict):
                continue
            local = str(item.get("local") or "").strip()
            if not local or local in seen:
                continue
            seen.add(local)
            assets.append(item)
    return assets


def _inject_base_href(html: str, base_href: str) -> str:
    if re.search(r"<base\b", html, re.IGNORECASE):
        return html
    base_tag = f'<base href="{base_href}">'
    head_match = re.search(r"<head\b[^>]*>", html, re.IGNORECASE)
    if head_match:
        insert_at = head_match.end()
        return html[:insert_at] + "\n  " + base_tag + html[insert_at:]
    html_match = re.search(r"<html\b[^>]*>", html, re.IGNORECASE)
    if html_match:
        insert_at = html_match.end()
        return html[:insert_at] + f"\n<head>{base_tag}</head>" + html[insert_at:]
    return (
        f"<!DOCTYPE html><html><head><meta charset=\"UTF-8\">{base_tag}</head>"
        f"<body>{html}</body></html>"
    )


def _find_http_index_path(source_dir: Path) -> Path | None:
    for name in ("index.html", "index.htm"):
        candidate = source_dir / name
        if candidate.is_file():
            return candidate
    for path in sorted(source_dir.glob("index.*")):
        if path.is_file() and path.suffix.lower() in {".html", ".htm"}:
            return path
    return None


def _load_http_fetch_meta(source_dir: Path) -> dict[str, Any]:
    meta_path = source_dir / "nexu-fetch-meta.json"
    if not meta_path.is_file():
        return {}
    try:
        raw = json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return raw if isinstance(raw, dict) else {}


def _build_http_preview_stage0(meta: dict[str, Any]) -> str | None:
    project_id = str(meta.get("id") or "")
    if not project_id.startswith("http-"):
        return None
    source_dir = Path(str(meta.get("source_dir") or ""))
    if not source_dir.is_dir():
        return None
    index_path = _find_http_index_path(source_dir)
    if index_path is None:
        return None
    fetch_meta = _load_http_fetch_meta(source_dir)
    page_url = str(fetch_meta.get("final_url") or meta.get("source") or "").strip()
    if not page_url:
        return None
    try:
        html = index_path.read_text(encoding="utf-8")
    except OSError:
        return None
    saved_assets = fetch_meta.get("stylesheets")
    if isinstance(saved_assets, list):
        saved = [item for item in saved_assets if isinstance(item, dict)]
        html = _rewrite_local_stylesheets(html, project_id=project_id, saved=saved)
    html = _rewrite_local_asset_refs(html, project_id=project_id, assets=_fetch_meta_assets(fetch_meta))
    html = _inject_base_href(html, _document_base_href(page_url))
    html, _preview_meta = prepare_http_preview_html(html)
    html = inject_cinema_shield(html)
    if 'data-nexu-import-preview="http"' not in html:
        html = re.sub(
            r"(<body\b)([^>]*>)",
            r'\1 data-nexu-import-preview="http"\2',
            html,
            count=1,
            flags=re.IGNORECASE,
        )
    return html


def _iter_project_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        files.append(path)
    return sorted(files)


def _detect_run_notes(root: Path) -> list[str]:
    notes: list[str] = []
    if (root / "package.json").exists():
        notes.append("npm install")
        notes.append("npm run dev")
    if (root / "pyproject.toml").exists():
        notes.append("uv sync")
        notes.append("uv run python -m pytest")
    if (root / "requirements.txt").exists():
        notes.append("python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt")
    if not notes:
        notes.append("inspect project files and define the first Markpact run block")
    return notes


def _read_text_for_markpact(path: Path) -> str | None:
    if path.stat().st_size > MAX_FILE_BYTES:
        return None
    try:
        data = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None
    return data


def _build_markpact_migration(root: Path, *, project_id: str, title: str, source: str) -> str:
    files = _iter_project_files(root)
    tree = "\n".join(f"- `{p.relative_to(root)}`" for p in files[:80])
    run_notes = "\n".join(f"# {line}" for line in _detect_run_notes(root))
    meta = {
        "project_id": project_id,
        "title": title,
        "source": source,
        "migrated_at": datetime.now(timezone.utc).isoformat(),
        "file_count": len(files),
    }
    embedded: list[str] = []
    for path in files[:MAX_EMBED_FILES]:
        text = _read_text_for_markpact(path)
        if text is None:
            continue
        rel = str(path.relative_to(root))
        fence = "````" if "```" in text else "```"
        embedded.append(f"{fence}text markpact:file path={rel}\n{text}\n{fence}")
    embedded_block = "\n\n".join(embedded) or "_No small text files embedded yet._"
    return f"""# {title} — Markpact migration

This project was imported into Nexu. The first required step is Markpact migration:
turn the source tree into an explicit, runnable README contract before visual iterations.

```json markpact:file path=nexu-import-meta.json
{json.dumps(meta, indent=2, ensure_ascii=False)}
```

## Source Tree

{tree or "- (empty project)"}

## Suggested First Run

```bash markpact:run
{run_notes}
```

## Imported Files

{embedded_block}
"""


def _stage_html(meta: dict[str, Any], *, variant: str) -> str:
    project_id = str(meta["id"])
    title = str(meta["title"])
    count = int(meta.get("file_count") or 0)
    source = str(meta.get("source") or "")
    markpact = str(meta.get("markpact_path") or "")
    focus = {
        "stage0": ("Migration baseline", "Inspect imported project and Markpact README"),
        "stage1": ("Contract shape", "Add run/deps/file blocks and project intent"),
        "stage2": ("Executable app", "Promote runnable Markpact service"),
    }.get(variant, ("Migration baseline", "Inspect imported project"))
    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>{title} — {focus[0]}</title>
  <style>
    body {{ margin:0; min-height:100vh; background:#0b1020; color:#e2e8f0; font-family:Arial,sans-serif; }}
    .app-shell {{ display:grid; grid-template-columns:220px 1fr; gap:18px; padding:26px; min-height:100vh; }}
    aside, .panel, .card {{ background:#111827; border:1px solid rgba(148,163,184,.22); border-radius:8px; }}
    aside {{ padding:18px; }}
    main {{ display:grid; gap:16px; align-content:start; }}
    h1 {{ margin:0; color:#38bdf8; }}
    .grid {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px; }}
    .card {{ padding:16px; }}
    .card strong {{ display:block; color:#22c55e; font-size:1.5rem; margin-top:8px; }}
    .panel {{ padding:18px; }}
    code {{ color:#a5b4fc; word-break:break-all; }}
    .badge {{ display:inline-block; padding:6px 10px; border-radius:999px; background:#1e293b; color:#fbbf24; }}
  </style>
</head>
<body>
  <div class="app-shell" data-project="{project_id}" data-kind="imported">
    <aside class="nexu-selectable" data-nexu-target="markpact-nav">
      <h2>Markpact migration</h2>
      <p class="badge">{focus[0]}</p>
      <p>{focus[1]}</p>
    </aside>
    <main>
      <section class="panel nexu-selectable" id="btn-import-summary" data-nexu-target="import-summary">
        <h1>{title}</h1>
        <p>Imported source must become a Markpact contract before Nexu visual iterations.</p>
      </section>
      <section class="grid">
        <div class="card nexu-selectable" id="btn-files" data-nexu-target="files"><span>Files</span><strong>{count}</strong></div>
        <div class="card nexu-selectable" id="btn-source" data-nexu-target="source"><span>Source</span><strong>{source[:18] or "local"}</strong></div>
        <div class="card nexu-selectable" id="btn-markpact" data-nexu-target="markpact"><span>Markpact</span><strong>README</strong></div>
      </section>
      <section class="panel nexu-selectable" id="btn-markpact-path" data-nexu-target="markpact-path">
        <h2>First artifact</h2>
        <code>{markpact}</code>
      </section>
    </main>
  </div>
</body>
</html>"""


def _apply_http_preprocess_fields(meta: dict[str, Any], preprocess_fields: dict[str, Any]) -> dict[str, Any]:
    if not preprocess_fields:
        return meta
    updated = {**meta, **preprocess_fields}
    artifacts = list(updated.get("artifacts") or [])
    for kind, path_key in (
        ("visual_css", "visual_css_path"),
        ("html_outline", "html_outline_path"),
    ):
        path_val = str(preprocess_fields.get(path_key) or "").strip()
        if not path_val:
            continue
        if not any(str(item.get("kind") or "") == kind for item in artifacts):
            artifacts.append({"kind": kind, "path": path_val})
    updated["artifacts"] = artifacts
    return updated


def _refresh_http_preprocess_if_needed(cinema_dir: Path, meta: dict[str, Any]) -> dict[str, Any]:
    project_id = str(meta.get("id") or "")
    if not project_id.startswith("http-"):
        return meta
    source_dir = Path(str(meta.get("source_dir") or (_project_dir(cinema_dir, project_id) / "source")))
    fetch_meta = _load_http_fetch_meta(source_dir)
    preprocess_fields = ensure_http_preprocess_artifacts(
        source_dir,
        fetch_meta=fetch_meta,
        meta=meta,
    )
    if not preprocess_fields:
        return meta
    updated = _apply_http_preprocess_fields(meta, preprocess_fields)
    meta_path = _project_dir(cinema_dir, project_id) / "project.json"
    try:
        meta_path.write_text(
            json.dumps(updated, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    except OSError:
        pass
    return updated


def _activate_imported(cinema_dir: Path, meta: dict[str, Any]) -> dict[str, Any]:
    import_kind = str(meta.get("import_kind") or _import_kind_from_id(str(meta.get("id") or "")))
    if import_kind == "http":
        meta = _refresh_http_preprocess_if_needed(cinema_dir, meta)
    reset_cinema_policy_ledger(cinema_dir)
    stage0_html = _build_http_preview_stage0(meta) or _stage_html(meta, variant="stage0")
    (cinema_dir / "stage0.html").write_text(stage0_html, encoding="utf-8")
    for name, variant in (("stage1.html", "stage1"), ("stage2.html", "stage2")):
        (cinema_dir / name).write_text(_stage_html(meta, variant=variant), encoding="utf-8")
    if import_kind == "http":
        options_sync = ensure_http_option_previews_from_stage0(cinema_dir)
    else:
        options_sync = ensure_option_previews_from_stages(cinema_dir)
    write_cinema_inject_files(cinema_dir)
    active = {
        "id": meta["id"],
        "title": meta["title"],
        "subtitle": "",
        "domain": "import",
        "kind": "imported",
        "import_kind": import_kind,
        "activated_at": datetime.now(timezone.utc).isoformat(),
        "source": meta.get("source", ""),
        "markpact_path": meta.get("markpact_path", ""),
    }
    (cinema_dir / ACTIVE_PROJECT_FILE).write_text(
        json.dumps(active, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    refresh_imported_policy_snapshot(cinema_dir, meta, active)
    goal_required = import_kind == "http"
    payload: dict[str, Any] = {
        "status": "project_imported",
        "project": {
            **active,
            "tags": ["imported", "markpact"],
            "emoji": "📦",
            "markpact": True,
            "imported": True,
            "deletable": is_deletable_imported_id(str(meta["id"])),
            "source_url": _source_url_from_meta(meta),
            "file_count": int(meta.get("file_count") or 0),
            "total_bytes": int(meta.get("total_bytes") or 0),
            "path_hint": str(meta.get("path_hint") or f"imported_projects/{meta['id']}"),
            "source_paths": [],
        },
        "files_copied": ["stage0.html", "stage1.html", "stage2.html", "alt_a.html", "alt_b.html", "alt_c.html"],
        "options_sync": options_sync,
        "scope": scope_meta_for_project("imported"),
        "ui_type": "web",
        "is_calculator": False,
        "goal_required": goal_required,
    }
    if goal_required:
        payload["goal_bootstrap"] = {"status": "requires_user_goal"}
    return payload


def import_git_project(
    cinema_dir: Path,
    git_url: str,
    *,
    branch: str | None = None,
    allow_network: bool = True,
) -> dict[str, Any]:
    if not allow_network:
        return {"error": "Git import requires llm.allow_network_calls in nexu.yaml"}
    source = git_url.strip()
    err = _validate_git_url(source)
    if err:
        return {"error": err}
    project_id = "git-" + _slug(Path(source.rstrip("/")).stem or source)
    dest = _project_dir(cinema_dir, project_id)
    if dest.exists():
        shutil.rmtree(dest)
    source_dir = dest / "source"
    dest.mkdir(parents=True, exist_ok=True)
    cmd = ["git", "clone", "--depth", "1"]
    branch_name = (branch or "").strip()
    if branch_name:
        cmd.extend(["--branch", branch_name])
    cmd.extend([source, str(source_dir)])
    try:
        proc = subprocess.run(
            cmd,
            text=True,
            capture_output=True,
            timeout=GIT_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        return {"error": "git clone timed out"}
    if proc.returncode != 0:
        return {"error": (proc.stderr or proc.stdout or "git clone failed").strip()[:500]}
    return _finish_import(
        cinema_dir,
        project_id=project_id,
        source_dir=source_dir,
        source=source,
        import_kind="git",
    )


def import_http_project(
    cinema_dir: Path,
    site_url: str,
    *,
    allow_network: bool = True,
) -> dict[str, Any]:
    if not allow_network:
        return {"error": "HTTP import requires llm.allow_network_calls in nexu.yaml"}
    parsed = urlparse(site_url.strip())
    slug_source = parsed.netloc + parsed.path.rstrip("/")
    project_id = "http-" + _slug(slug_source or site_url)
    dest = _project_dir(cinema_dir, project_id)
    if dest.exists():
        shutil.rmtree(dest)
    source_dir = dest / "source"
    source_dir.mkdir(parents=True, exist_ok=True)
    try:
        fetched = fetch_complete_web_page(site_url, source_dir=source_dir, render_js=True, mirror_assets=True)
    except (HTTPError, URLError, TimeoutError, ValueError) as exc:
        return {"error": str(exc)[:500]}
    content_type = fetched.content_type
    final_url = fetched.final_url
    charset = fetched.charset
    html = fetched.html
    ext = ".html" if "html" in content_type.lower() else ".txt"
    index_path = source_dir / f"index{ext}"
    index_path.write_text(html, encoding="utf-8")
    assets = [
        {
            "url": asset.url,
            "href": asset.original,
            "original": asset.original,
            "local": asset.local,
            "content_type": asset.content_type,
            "kind": asset.kind,
        }
        for asset in fetched.assets
    ]
    stylesheets = [item for item in assets if item.get("kind") == "stylesheet"]
    images = [item for item in assets if item.get("kind") == "image"]
    fetch_errors = list(fetched.errors)
    if fetched.render_error:
        fetch_errors.append(f"playwright: {fetched.render_error}"[:500])
    fetch_meta = {
        "url": site_url.strip(),
        "final_url": final_url,
        "content_type": content_type,
        "charset": charset,
        "fetch_method": fetched.method,
        "assets": assets,
        "stylesheets": stylesheets,
        "images": images,
        "fetch_errors": fetch_errors,
    }
    (source_dir / "nexu-fetch-meta.json").write_text(
        json.dumps(fetch_meta, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return _finish_import(
        cinema_dir,
        project_id=project_id,
        source_dir=source_dir,
        source=site_url.strip(),
        import_kind="http",
        fetch_meta=fetch_meta,
    )


def import_zip_project(
    cinema_dir: Path,
    filename: str,
    content_base64: str = "",
    *,
    content_bytes: bytes | None = None,
) -> dict[str, Any]:
    safe_name = Path(filename or "project.zip").name
    project_id = "zip-" + _slug(Path(safe_name).stem)
    dest = _project_dir(cinema_dir, project_id)
    if dest.exists():
        shutil.rmtree(dest)
    source_dir = dest / "source"
    source_dir.mkdir(parents=True, exist_ok=True)
    zip_path = dest / safe_name
    if content_bytes is not None:
        zip_path.write_bytes(content_bytes)
    else:
        zip_path.write_bytes(base64.b64decode(content_base64))
    try:
        _safe_extract_zip(zip_path, source_dir)
    except (ValueError, zipfile.BadZipFile) as exc:
        return {"error": str(exc)}
    return _finish_import(
        cinema_dir,
        project_id=project_id,
        source_dir=source_dir,
        source=safe_name,
        import_kind="zip",
    )


def _import_kind_from_id(project_id: str) -> str:
    if project_id.startswith("http-"):
        return "http"
    if project_id.startswith("git-"):
        return "git"
    if project_id.startswith("zip-"):
        return "zip"
    return "unknown"


def _project_title_from_id(project_id: str) -> str:
    for prefix in ("git-", "zip-", "http-"):
        if project_id.startswith(prefix):
            return project_id[len(prefix) :].replace("-", " ").title()
    return project_id.replace("-", " ").title()


def _maybe_organize_import_source(source_dir: Path, import_kind: str) -> dict[str, Any]:
    """Organize index HTML for imported web snapshots (HTTP/ZIP/git); skip when no index."""
    if import_kind not in {"http", "zip", "git"}:
        return {}
    organized = organize_html_project_dir(source_dir)
    if organized is None:
        return {}
    return organize_result_manifest(organized)


def _finish_import(
    cinema_dir: Path,
    *,
    project_id: str,
    source_dir: Path,
    source: str,
    import_kind: str | None = None,
    fetch_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    title = _project_title_from_id(project_id)
    resolved_kind = import_kind or _import_kind_from_id(project_id)
    preprocess_fields: dict[str, Any] = {}
    organize_meta = _maybe_organize_import_source(source_dir, resolved_kind)
    if resolved_kind == "http":
        preprocess_fields = preprocess_http_import(source_dir, fetch_meta=fetch_meta)
    files = _iter_project_files(source_dir)
    _, total_bytes = _source_stats(source_dir)
    markpact = _build_markpact_migration(source_dir, project_id=project_id, title=title, source=source)
    markpact_path = _project_dir(cinema_dir, project_id) / "README.markpact.md"
    markpact_path.write_text(markpact, encoding="utf-8")
    capsule, workspace_root = _infer_workspace_context(cinema_dir)
    now = datetime.now(timezone.utc).isoformat()
    source_url = source
    if fetch_meta and isinstance(fetch_meta.get("final_url"), str):
        source_url = str(fetch_meta["final_url"]).strip() or source
    meta = {
        "id": project_id,
        "title": title,
        "source": source,
        "source_url": source_url,
        "source_dir": str(source_dir),
        "markpact_path": str(markpact_path),
        "file_count": len(files),
        "total_bytes": total_bytes,
        "import_kind": resolved_kind,
        "imported_at": now,
        "path_hint": f"imported_projects/{project_id}",
        "capsule": capsule,
        "workspace_root": workspace_root,
        "artifacts": [
            {"kind": "markpact", "path": "README.markpact.md"},
            {"kind": "source", "path": "source/"},
        ],
        "services": [],
    }
    if preprocess_fields:
        meta.update(preprocess_fields)
        meta["artifacts"] = list(meta["artifacts"]) + [
            {"kind": "visual_css", "path": preprocess_fields.get("visual_css_path", "source/nexu-visual.css")},
            {"kind": "html_outline", "path": preprocess_fields.get("html_outline_path", "source/nexu-outline.html")},
        ]
    if organize_meta:
        meta["organize"] = organize_meta
        css_path = organize_meta.get("extracted_css_path")
        if css_path:
            meta["artifacts"] = list(meta["artifacts"]) + [
                {"kind": "extracted_css", "path": f"source/{css_path}"},
            ]
    if fetch_meta:
        meta["fetch_meta"] = fetch_meta
    (_project_dir(cinema_dir, project_id) / "project.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return _activate_imported(cinema_dir, meta)


def _infer_workspace_context(cinema_dir: Path) -> tuple[str | None, str | None]:
    parts = cinema_dir.resolve().parts
    if ".nexu" not in parts or "capsules" not in parts:
        return None, None
    capsule_idx = parts.index("capsules")
    if capsule_idx + 1 >= len(parts):
        return None, None
    capsule = parts[capsule_idx + 1]
    nexu_idx = parts.index(".nexu")
    workspace_root = str(Path(*parts[:nexu_idx]))
    return capsule, workspace_root


def _source_stats(source_dir: Path) -> tuple[int, int]:
    if not source_dir.is_dir():
        return 0, 0
    count = 0
    total = 0
    for path in _iter_project_files(source_dir):
        count += 1
        try:
            total += path.stat().st_size
        except OSError:
            pass
    return count, total


def _source_url_from_meta(meta: dict[str, Any]) -> str:
    fetch = meta.get("fetch_meta")
    if isinstance(fetch, dict):
        final = str(fetch.get("final_url") or "").strip()
        if final:
            return final
    return str(meta.get("source_url") or meta.get("source") or "").strip()


def normalize_imported_project_id(project_id: str) -> str:
    from urllib.parse import unquote

    return unquote(str(project_id or "").strip())


def is_deletable_imported_id(project_id: str) -> bool:
    normalized = normalize_imported_project_id(project_id)
    match = IMPORTED_ID_RE.match(normalized)
    if not match:
        return False
    suffix = normalized[match.end(1) + 1 :]
    return not suffix.startswith(("zip-", "git-", "http-"))


def _resolve_markpact_path(cinema_dir: Path, project_id: str, meta: dict[str, Any]) -> str:
    markpact_path = str(meta.get("markpact_path") or "")
    if markpact_path:
        return markpact_path
    candidate = _project_dir(cinema_dir, project_id) / "README.markpact.md"
    return str(candidate) if candidate.is_file() else ""


def _with_workspace_meta_defaults(
    meta: dict[str, Any],
    updated: dict[str, Any],
    *,
    capsule: str,
    workspace_root: str,
) -> dict[str, Any]:
    if capsule and not meta.get("capsule"):
        updated["capsule"] = capsule
    if workspace_root and not meta.get("workspace_root"):
        updated["workspace_root"] = workspace_root
    if "artifacts" not in meta:
        updated["artifacts"] = [
            {"kind": "markpact", "path": "README.markpact.md"},
            {"kind": "source", "path": "source/"},
        ]
    if "services" not in meta:
        updated["services"] = []
    return updated


def _compile_meta_fields(cinema_dir: Path, meta: dict[str, Any]) -> dict[str, Any]:
    project_id = str(meta.get("id") or "")
    source_dir = Path(str(meta.get("source_dir") or (_project_dir(cinema_dir, project_id) / "source")))
    scanned_count, scanned_bytes = _source_stats(source_dir)
    file_count = int(meta.get("file_count") or 0) or scanned_count
    total_bytes = int(meta.get("total_bytes") or 0) or scanned_bytes
    capsule, workspace_root = _infer_workspace_context(cinema_dir)
    markpact_path = _resolve_markpact_path(cinema_dir, project_id, meta)
    updated = {
        **meta,
        "file_count": file_count,
        "total_bytes": total_bytes,
        "source_url": _source_url_from_meta(meta),
        "path_hint": str(meta.get("path_hint") or f"imported_projects/{project_id}"),
        "markpact_path": markpact_path,
    }
    return _with_workspace_meta_defaults(
        meta,
        updated,
        capsule=capsule,
        workspace_root=workspace_root,
    )


def _ensure_project_meta_fields(
    cinema_dir: Path,
    meta: dict[str, Any],
    *,
    persist: bool = True,
) -> dict[str, Any]:
    updated = _compile_meta_fields(cinema_dir, meta)
    if persist and updated != meta:
        project_id = str(meta.get("id") or "")
        meta_path = _project_dir(cinema_dir, project_id) / "project.json"
        try:
            meta_path.write_text(
                json.dumps(updated, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
        except OSError:
            pass
    return updated


def _catalog_entry_from_meta(meta: dict[str, Any], cinema_dir: Path) -> dict[str, Any]:
    project_id = str(meta.get("id") or "")
    import_kind = str(meta.get("import_kind") or _import_kind_from_id(project_id))
    kind_emoji = {"zip": "📦", "git": "🔗", "http": "🌐"}.get(import_kind, "📦")
    return {
        "id": project_id,
        "title": meta.get("title"),
        "subtitle": "Imported project — Markpact migration",
        "domain": "import",
        "kind": "imported",
        "tags": ["imported", "markpact", import_kind],
        "emoji": kind_emoji,
        "source_paths": [],
        "markpact": True,
        "imported": True,
        "deletable": is_deletable_imported_id(project_id),
        "import_kind": import_kind,
        "source_url": _source_url_from_meta(meta),
        "file_count": int(meta.get("file_count") or 0),
        "total_bytes": int(meta.get("total_bytes") or 0),
        "path_hint": str(meta.get("path_hint") or f"imported_projects/{project_id}"),
        "markpact_path": str(meta.get("markpact_path") or ""),
        "capsule": meta.get("capsule"),
        "workspace_root": meta.get("workspace_root"),
        "visual_css_bytes": meta.get("visual_css_bytes"),
        "outline_node_count": meta.get("outline_node_count"),
        "llm_context_mode": meta.get("llm_context_mode"),
    }


def _filter_traces_for_project(
    traces: list[dict[str, Any]],
    *,
    project_id: str,
    since: str = "",
) -> list[dict[str, Any]]:
    filtered = traces
    if since:
        prefix = since[:19]
        filtered = [t for t in filtered if str(t.get("timestamp") or "") >= prefix]
    needle = project_id.lower()
    labeled = [
        t
        for t in filtered
        if needle in str(t.get("label") or "").lower()
        or project_id in str(t.get("id") or "")
    ]
    return labeled if labeled else filtered


def read_imported_markpact(cinema_dir: Path, project_id: str) -> dict[str, Any]:
    project_id = normalize_imported_project_id(project_id)
    if not is_deletable_imported_id(project_id):
        return {"error": "invalid imported project id"}
    meta_path = _project_dir(cinema_dir, project_id) / "project.json"
    if not meta_path.is_file():
        return {"error": f"unknown imported project: {project_id}"}
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"error": f"corrupt imported project: {project_id}"}
    if not isinstance(meta, dict):
        return {"error": f"invalid imported project: {project_id}"}
    meta = _ensure_project_meta_fields(cinema_dir, meta, persist=False)
    markpact_path = Path(str(meta.get("markpact_path") or ""))
    if not markpact_path.is_file():
        markpact_path = _project_dir(cinema_dir, project_id) / "README.markpact.md"
    if not markpact_path.is_file():
        return {"error": "markpact README not found"}
    try:
        markdown = markpact_path.read_text(encoding="utf-8")
    except OSError as exc:
        return {"error": str(exc)[:200]}
    return {
        "project_id": project_id,
        "filename": markpact_path.name,
        "path": str(markpact_path),
        "markdown": markdown,
    }


def imported_project_llm_log(
    cinema_dir: Path,
    project_id: str,
    trace_dir: Path,
    *,
    limit: int = 40,
) -> dict[str, Any]:
    project_id = normalize_imported_project_id(project_id)
    if not is_deletable_imported_id(project_id):
        return {"error": "invalid imported project id"}
    meta_path = _project_dir(cinema_dir, project_id) / "project.json"
    if not meta_path.is_file():
        return {"error": f"unknown imported project: {project_id}"}
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"error": f"corrupt imported project: {project_id}"}
    since = str(meta.get("imported_at") or meta.get("activated_at") or "")
    traces = list(list_llm_traces(trace_dir).get("traces") or [])
    filtered = _filter_traces_for_project(traces, project_id=project_id, since=since)
    return {
        "project_id": project_id,
        "since": since or None,
        "traces": filtered[:limit],
        "total": len(filtered),
    }


def _verify_delete_paths(project_dir: Path, imports_root: Path) -> str | None:
    try:
        resolved = project_dir.resolve()
    except OSError:
        return "project not found"
    if resolved != imports_root and not str(resolved).startswith(str(imports_root) + "/"):
        return "invalid project path"
    if not project_dir.is_dir():
        return "project not found"
    return None


def _activate_delete_fallback(
    cinema_dir: Path,
    fallback: str,
    workspace_root: Path,
    capsule_name: str,
    repo_root: Path,
) -> str | None:
    activation = activate_example_project(
        cinema_dir,
        fallback,
        repo_root=repo_root,
        capsule_name=capsule_name,
        workspace_root=workspace_root,
    )
    if activation.get("error"):
        active_path = cinema_dir / ACTIVE_PROJECT_FILE
        if active_path.exists():
            active_path.unlink()
        return str(activation["error"])
    return None


def _clear_active_project(cinema_dir: Path) -> None:
    active_path = cinema_dir / ACTIVE_PROJECT_FILE
    if active_path.exists():
        active_path.unlink()


def _delete_active_project_fallback(
    cinema_dir: Path,
    result: dict[str, Any],
    workspace_root: Path | None,
    capsule_name: str | None,
    repo_root: Path | None,
) -> None:
    fallback = DEFAULT_FALLBACK_PROJECT
    if repo_root and workspace_root and capsule_name:
        err = _activate_delete_fallback(cinema_dir, fallback, workspace_root, capsule_name, repo_root)
        if err:
            result["activated"] = None
            result["activate_error"] = err
        else:
            result["activated"] = fallback
        return
    _clear_active_project(cinema_dir)
    result["activated"] = None


def delete_imported_project(
    cinema_dir: Path,
    project_id: str,
    *,
    workspace_root: Path | None = None,
    capsule_name: str | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    normalized_id = normalize_imported_project_id(project_id)
    if not is_deletable_imported_id(normalized_id):
        return {"error": "only imported projects (zip-/git-/http-) can be deleted"}

    project_dir = _project_dir(cinema_dir, normalized_id)
    imports_root = _imports_root(cinema_dir).resolve()
    path_err = _verify_delete_paths(project_dir, imports_root)
    if path_err:
        return {"error": path_err}
    if not project_dir.is_dir():
        return {"error": f"unknown imported project: {normalized_id}"}

    active = load_active_project(cinema_dir) or {}
    was_active = str(active.get("id") or "") == normalized_id
    shutil.rmtree(project_dir)
    result: dict[str, Any] = {"status": "deleted", "id": normalized_id, "was_active": was_active}
    if was_active:
        _delete_active_project_fallback(
            cinema_dir,
            result,
            workspace_root,
            capsule_name,
            repo_root,
        )
    return result


def delete_project(
    cinema_dir: Path,
    project_id: str,
    *,
    workspace_root: Path | None = None,
    capsule_name: str | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Delete a workspace project entry, whether imported or seeded demo."""
    normalized = normalize_imported_project_id(project_id)
    if is_deletable_imported_id(normalized) and (
        _project_dir(cinema_dir, normalized) / "project.json"
    ).is_file():
        return delete_imported_project(
            cinema_dir,
            normalized,
            workspace_root=workspace_root,
            capsule_name=capsule_name,
            repo_root=repo_root,
        )
    return delete_example_project(
        cinema_dir,
        normalized,
        repo_root=repo_root,
        workspace_root=workspace_root,
        capsule_name=capsule_name,
    )

def list_imported_projects(cinema_dir: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    root = _imports_root(cinema_dir)
    for path in sorted(root.glob("*/project.json")):
        try:
            meta = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(meta, dict):
            continue
        meta = _ensure_project_meta_fields(cinema_dir, meta)
        out.append(_catalog_entry_from_meta(meta, cinema_dir))
    return [item for item in out if item.get("id")]


def merged_projects_catalog(cinema_dir: Path) -> dict[str, Any]:
    base = list_project_catalog(cinema_dir)
    imported = list_imported_projects(cinema_dir)
    projects = list(base["projects"]) + imported
    domains = sorted({str(p.get("domain") or "") for p in projects if p.get("domain")})
    kinds = sorted({str(p.get("kind") or "") for p in projects if p.get("kind")})
    tags = sorted({tag for p in projects for tag in (p.get("tags") or [])})
    return {"projects": projects, "filters": {"domains": domains, "kinds": kinds, "tags": tags}}


def activate_imported_project(cinema_dir: Path, project_id: str) -> dict[str, Any]:
    meta_path = _project_dir(cinema_dir, project_id) / "project.json"
    if not meta_path.exists():
        return {"error": f"unknown imported project: {project_id}"}
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"error": f"corrupt imported project: {project_id}"}
    if not isinstance(meta, dict):
        return {"error": f"invalid imported project: {project_id}"}
    return _activate_imported(cinema_dir, meta)
