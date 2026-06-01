"""HTTP import preprocessing: compact visual CSS + HTML outline for LLM patch iteration."""

from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

MAX_VISUAL_CSS_BYTES = 65_536
OUTLINE_TEXT_PLACEHOLDER = "…"

_STYLE_BLOCK_RE = re.compile(r"<style\b[^>]*>([\s\S]*?)</style>", re.IGNORECASE)
_LINK_HREF_RE = re.compile(
    r"""<link\b[^>]*\brel\s*=\s*(['"])[^'"]*stylesheet[^'"]*\1[^>]*\bhref\s*=\s*(['"])(.*?)\2""",
    re.IGNORECASE,
)
_LINK_HREF_ALT_RE = re.compile(
    r"""<link\b[^>]*\bhref\s*=\s*(['"])(.*?)\1[^>]*\brel\s*=\s*(['"])[^'"]*stylesheet[^'"]*\3""",
    re.IGNORECASE,
)
_SKIP_AT_RULE_RE = re.compile(r"@(font-face|keyframes)\b", re.IGNORECASE)
_PRINT_MEDIA_RE = re.compile(r"@media\s+print\b", re.IGNORECASE)

_SCRIPT_BLOCK_RE = re.compile(r"<script\b[^>]*>[\s\S]*?</script>", re.IGNORECASE)
_SCRIPT_SRC_ATTR_RE = re.compile(r"""\bsrc\s*=\s*(['"])(.*?)\1""", re.IGNORECASE)
_NEXU_PREVIEW_SHIM_MARKER = "nexu preview: block cross-origin fetch"

HTTP_PREVIEW_NETWORK_SHIM = f"""<script>/* {_NEXU_PREVIEW_SHIM_MARKER} */
(function(){{
  var previewOrigin = location.origin;
  function nexuCrossOrigin(url) {{
    try {{
      var resolved = new URL(String(url || ""), document.baseURI || location.href);
      return resolved.origin !== previewOrigin;
    }} catch (_) {{
      return true;
    }}
  }}
  var nativeFetch = window.fetch;
  if (typeof nativeFetch === "function") {{
    window.fetch = function(input, init) {{
      var url = typeof input === "string" ? input : (input && input.url) || "";
      if (nexuCrossOrigin(url)) {{
        return Promise.resolve(new Response("", {{status: 204, statusText: "nexu preview blocked"}}));
      }}
      return nativeFetch.apply(this, arguments);
    }};
  }}
  var NativeXHR = window.XMLHttpRequest;
  if (typeof NativeXHR === "function") {{
    window.XMLHttpRequest = function() {{
      var xhr = new NativeXHR();
      var nativeOpen = xhr.open;
      xhr.open = function(method, url) {{
        if (nexuCrossOrigin(url)) {{
          xhr._nexuBlocked = true;
          return;
        }}
        return nativeOpen.apply(xhr, arguments);
      }};
      var nativeSend = xhr.send;
      xhr.send = function() {{
        if (xhr._nexuBlocked) return;
        return nativeSend.apply(xhr, arguments);
      }};
      return xhr;
    }};
  }}
  window.kadenceConfig = window.kadenceConfig || {{}};
}})();
</script>"""

_VISUAL_PROPS = frozenset(
    {
        "color",
        "background",
        "background-color",
        "background-image",
        "border",
        "border-color",
        "border-radius",
        "border-width",
        "border-style",
        "box-shadow",
        "font",
        "font-family",
        "font-size",
        "font-weight",
        "fill",
        "stroke",
        "width",
        "height",
        "min-width",
        "min-height",
        "max-width",
        "max-height",
        "aspect-ratio",
        "display",
        "flex",
        "flex-direction",
        "flex-wrap",
        "grid",
        "grid-template",
        "grid-template-columns",
        "grid-template-rows",
        "gap",
        "padding",
        "margin",
        "opacity",
        "transform",
        "clip-path",
        "outline",
        "outline-color",
        "outline-width",
    }
)
_PROP_PATTERN = re.compile(
    r"(?<![\w-])(" + "|".join(re.escape(p) for p in sorted(_VISUAL_PROPS, key=len, reverse=True)) + r")\s*:",
    re.IGNORECASE,
)
_VAR_PATTERN = re.compile(r"--[\w-]+\s*:", re.IGNORECASE)


def _safe_read_under(base_dir: Path, rel_path: str) -> str | None:
    """Read a file only when it resolves under base_dir."""
    try:
        root = base_dir.resolve()
        candidate = (base_dir / rel_path).resolve()
        if not str(candidate).startswith(str(root) + "/") and candidate != root:
            return None
        if not candidate.is_file():
            return None
        return candidate.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def _extract_inline_css(html: str) -> str:
    blocks = _STYLE_BLOCK_RE.findall(html or "")
    return "\n\n".join(block.strip() for block in blocks if block.strip())


def _extract_stylesheet_hrefs(html: str) -> list[str]:
    hrefs: list[str] = []
    for pattern in (_LINK_HREF_RE, _LINK_HREF_ALT_RE):
        for match in pattern.finditer(html or ""):
            href = match.group(3 if pattern is _LINK_HREF_RE else 2).strip()
            if href and href not in hrefs:
                hrefs.append(href)
    return hrefs


def _normalize_linked_paths(linked_css_paths: list[str] | None, html: str) -> list[str]:
    paths: list[str] = []
    for item in linked_css_paths or []:
        rel = str(item).strip().lstrip("/")
        if rel and rel not in paths:
            paths.append(rel)
    for href in _extract_stylesheet_hrefs(html):
        rel = href.strip()
        if rel.startswith(("http://", "https://", "//", "data:")):
            continue
        rel = rel.lstrip("/")
        if rel and rel not in paths:
            paths.append(rel)
    return paths


def _split_css_rules(css: str) -> list[str]:
    """Split CSS into top-level rule blocks (best-effort, no full parser)."""
    text = str(css or "")
    rules: list[str] = []
    depth = 0
    start = 0
    for index, char in enumerate(text):
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                chunk = text[start : index + 1].strip()
                if chunk:
                    rules.append(chunk)
                start = index + 1
    tail = text[start:].strip()
    if tail and depth == 0:
        rules.append(tail)
    return rules


def _rule_is_visual(rule: str) -> bool:
    body = rule.strip()
    if not body:
        return False
    if _SKIP_AT_RULE_RE.search(body):
        return False
    if _PRINT_MEDIA_RE.search(body):
        return False
    if _VAR_PATTERN.search(body):
        return True
    if _PROP_PATTERN.search(body):
        return True
    selector = body.split("{", 1)[0].strip().lower()
    if selector in {":root", "html", "body"}:
        return True
    return False


def _filter_visual_css(css: str) -> str:
    kept: list[str] = []
    for rule in _split_css_rules(css):
        if _rule_is_visual(rule):
            kept.append(rule)
    return "\n\n".join(kept)


def extract_visual_css(
    html: str,
    linked_css_paths: list[str] | None,
    source_dir: Path,
) -> tuple[str, dict[str, Any]]:
    """Extract color/shape/layout CSS from inline styles and linked sheets under source_dir."""
    chunks: list[str] = []
    inline = _extract_inline_css(html)
    if inline:
        chunks.append(inline)
    for rel in _normalize_linked_paths(linked_css_paths, html):
        local = rel
        if local.startswith("assets/"):
            pass
        elif local.startswith("source/"):
            local = local[len("source/") :]
        text = _safe_read_under(source_dir, local)
        if text:
            chunks.append(f"/* from {rel} */\n{text}")
    merged = "\n\n".join(chunks)
    filtered = _filter_visual_css(merged)
    meta: dict[str, Any] = {
        "visual_css_bytes": len(filtered.encode("utf-8")),
        "visual_css_truncated": False,
    }
    encoded = filtered.encode("utf-8")
    if len(encoded) > MAX_VISUAL_CSS_BYTES:
        truncated = encoded[:MAX_VISUAL_CSS_BYTES].decode("utf-8", errors="ignore").rstrip()
        if not truncated.endswith("}"):
            truncated += "\n/* nexu: visual CSS truncated at 64KB */"
        filtered = truncated
        meta["visual_css_bytes"] = len(filtered.encode("utf-8"))
        meta["visual_css_truncated"] = True
    return filtered, meta


class _OutlineParser(HTMLParser):
    _SKIP_TAGS = frozenset({"script", "style", "noscript"})
    _VOID_TAGS = frozenset(
        {
            "area",
            "base",
            "br",
            "col",
            "embed",
            "hr",
            "img",
            "input",
            "link",
            "meta",
            "param",
            "source",
            "track",
            "wbr",
        }
    )
    _KEEP_ATTR_PREFIXES = ("data-nexu", "aria-")

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.node_count = 0
        self._skip_depth = 0
        self._indent = 0

    def _keep_attr(self, name: str) -> bool:
        key = name.lower()
        return key in {"id", "class", "role"} or key.startswith(self._KEEP_ATTR_PREFIXES)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in self._SKIP_TAGS:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        kept = [(k, v) for k, v in attrs if v is not None and self._keep_attr(k)]
        attr_text = "".join(f' {k}="{v}"' for k, v in kept)
        indent = "  " * self._indent
        if tag in self._VOID_TAGS:
            self.parts.append(f"{indent}<{tag}{attr_text} />")
        else:
            self.parts.append(f"{indent}<{tag}{attr_text}>")
            self._indent += 1
        self.node_count += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in self._SKIP_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)
            return
        if self._skip_depth or tag in self._VOID_TAGS:
            return
        self._indent = max(0, self._indent - 1)
        indent = "  " * self._indent
        self.parts.append(f"{indent}</{tag}>")

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        text = re.sub(r"\s+", " ", data or "").strip()
        if not text:
            return
        indent = "  " * self._indent
        self.parts.append(f"{indent}{OUTLINE_TEXT_PLACEHOLDER}")


def _script_src_allowed_for_preview(src: str) -> bool:
    """Only cinema-local script paths are safe in HTTP preview iframes."""
    cleaned = str(src or "").strip()
    if not cleaned:
        return False
    if cleaned.startswith(("http://", "https://", "//", "data:")):
        return False
    lowered = cleaned.lower()
    return lowered.startswith("imported_projects/")


def _should_remove_preview_script(tag: str) -> bool:
    src_match = _SCRIPT_SRC_ATTR_RE.search(tag)
    if src_match:
        return not _script_src_allowed_for_preview(src_match.group(2))
    # Inline scripts (LiteSpeed guest.vary fetch, theme bootstraps) are not needed for static preview.
    return True


def sanitize_http_preview_html(html: str) -> tuple[str, dict[str, Any]]:
    """Strip live-site scripts from HTTP preview HTML; keep CSS/layout markup."""
    source = str(html or "")
    removed = 0

    def _replace_script(match: re.Match[str]) -> str:
        nonlocal removed
        block = match.group(0)
        if _should_remove_preview_script(block):
            removed += 1
            return "<!-- nexu: preview script removed -->"
        return block

    cleaned = _SCRIPT_BLOCK_RE.sub(_replace_script, source)
    meta = {"preview_scripts_removed": removed}
    return cleaned, meta


def inject_http_preview_shim(html: str) -> str:
    """Inject early head shim that blocks cross-origin fetch/XHR in preview iframes."""
    if _NEXU_PREVIEW_SHIM_MARKER in html:
        return html
    head_match = re.search(r"(<head\b[^>]*>)", html, re.IGNORECASE)
    if head_match:
        insert_at = head_match.end()
        return html[:insert_at] + "\n" + HTTP_PREVIEW_NETWORK_SHIM + html[insert_at:]
    html_match = re.search(r"(<html\b[^>]*>)", html, re.IGNORECASE)
    if html_match:
        insert_at = html_match.end()
        wrapped = (
            f"<head>{HTTP_PREVIEW_NETWORK_SHIM}</head>"
            f"{html[insert_at:]}"
        )
        return html[:insert_at] + wrapped
    return HTTP_PREVIEW_NETWORK_SHIM + html


def prepare_http_preview_html(html: str) -> tuple[str, dict[str, Any]]:
    """Sanitize scripts and inject network isolation shim for cinema preview iframes."""
    cleaned, meta = sanitize_http_preview_html(html)
    out = inject_http_preview_shim(cleaned)
    meta["preview_shim_injected"] = _NEXU_PREVIEW_SHIM_MARKER in out
    return out, meta


def build_html_outline(html: str) -> tuple[str, dict[str, Any]]:
    """Build a compact HTML skeleton without scripts or full text content."""
    cleaned = re.sub(r"<!--[\s\S]*?-->", "", str(html or ""))
    parser = _OutlineParser()
    parser.feed(cleaned)
    parser.close()
    outline = "\n".join(parser.parts).strip()
    if not outline.lower().startswith("<!doctype"):
        outline = f"<!DOCTYPE html>\n{outline}"
    meta = {"outline_node_count": parser.node_count, "outline_bytes": len(outline.encode("utf-8"))}
    return outline, meta


def _write_preprocess_artifacts(
    html: str,
    *,
    output_dir: Path,
    linked_css_paths: list[str] | None = None,
    css_path_rel: str,
    outline_path_rel: str,
) -> dict[str, Any]:
    linked = list(linked_css_paths or [])
    visual_css, css_meta = extract_visual_css(html, linked, output_dir)
    outline, outline_meta = build_html_outline(html)
    css_path = output_dir / css_path_rel
    outline_path = output_dir / outline_path_rel
    try:
        css_path.write_text(visual_css + ("\n" if visual_css else ""), encoding="utf-8")
        outline_path.write_text(outline + "\n", encoding="utf-8")
    except OSError:
        return {}
    return {
        "llm_context_mode": "patch",
        "visual_css_path": css_path_rel,
        "visual_css_bytes": css_meta.get("visual_css_bytes", 0),
        "visual_css_truncated": bool(css_meta.get("visual_css_truncated")),
        "html_outline_path": outline_path_rel,
        "outline_node_count": outline_meta.get("outline_node_count", 0),
        "outline_bytes": outline_meta.get("outline_bytes", 0),
    }


def preprocess_cinema_seed(cinema_dir: Path) -> dict[str, Any]:
    """Write nexu-visual.css and nexu-outline.html beside stage0.html; return active_project fields."""
    stage0 = cinema_dir / "stage0.html"
    if not stage0.is_file():
        return {}
    try:
        html = stage0.read_text(encoding="utf-8")
    except OSError:
        return {}
    return _write_preprocess_artifacts(
        html,
        output_dir=cinema_dir,
        css_path_rel="nexu-visual.css",
        outline_path_rel="nexu-outline.html",
    )


def http_preprocess_artifacts_present(
    source_dir: Path,
    meta: dict[str, Any] | None = None,
) -> bool:
    """True when compact LLM patch artifacts exist under source_dir."""
    project = meta if isinstance(meta, dict) else {}
    css_rel = str(project.get("visual_css_path") or "source/nexu-visual.css")
    outline_rel = str(project.get("html_outline_path") or "source/nexu-outline.html")
    css_local = css_rel[len("source/") :] if css_rel.startswith("source/") else css_rel
    outline_local = outline_rel[len("source/") :] if outline_rel.startswith("source/") else outline_rel
    css_ok = (source_dir / css_local).is_file()
    outline_ok = (source_dir / outline_local).is_file()
    mode_ok = str(project.get("llm_context_mode") or "") == "patch"
    return css_ok and outline_ok and mode_ok


def ensure_http_preprocess_artifacts(
    source_dir: Path,
    *,
    fetch_meta: dict[str, Any] | None = None,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Regenerate nexu-visual.css + nexu-outline.html when missing (HTTP re-activate migration)."""
    if not source_dir.is_dir():
        return {}
    if http_preprocess_artifacts_present(source_dir, meta):
        return {}
    fields = preprocess_http_import(source_dir, fetch_meta=fetch_meta)
    if not fields:
        return {}
    return {
        **fields,
        "visual_css_path": "source/nexu-visual.css",
        "html_outline_path": "source/nexu-outline.html",
    }


def preprocess_http_import(source_dir: Path, *, fetch_meta: dict[str, Any] | None = None) -> dict[str, Any]:
    """Write nexu-visual.css and nexu-outline.html under source_dir; return project.json fields."""
    index_path = source_dir / "index.html"
    if not index_path.is_file():
        for name in ("index.htm",):
            candidate = source_dir / name
            if candidate.is_file():
                index_path = candidate
                break
    if not index_path.is_file():
        return {}
    try:
        html = index_path.read_text(encoding="utf-8")
    except OSError:
        return {}

    linked: list[str] = []
    meta = fetch_meta if isinstance(fetch_meta, dict) else {}
    sheets = meta.get("stylesheets")
    if isinstance(sheets, list):
        for item in sheets:
            if isinstance(item, dict):
                local = str(item.get("local") or "").strip()
                if local:
                    linked.append(local)

    return _write_preprocess_artifacts(
        html,
        output_dir=source_dir,
        linked_css_paths=linked,
        css_path_rel="nexu-visual.css",
        outline_path_rel="nexu-outline.html",
    ) | {
        "visual_css_path": "source/nexu-visual.css",
        "html_outline_path": "source/nexu-outline.html",
    }


def _project_meta_path(cinema_dir: Path, project_id: str) -> Path:
    return cinema_dir / "imported_projects" / project_id / "project.json"


def load_cinema_seed_preprocess_artifacts(
    cinema_dir: Path | str,
    active: dict[str, Any] | None,
) -> dict[str, Any]:
    """Load compact seed preprocess artifacts from cinema dir when active_project uses patch mode."""
    project = active if isinstance(active, dict) else {}
    if str(project.get("llm_context_mode") or "") != "patch":
        return {}
    root = Path(cinema_dir)
    css_rel = str(project.get("visual_css_path") or "nexu-visual.css")
    outline_rel = str(project.get("html_outline_path") or "nexu-outline.html")
    visual_css = _safe_read_under(root, css_rel) or ""
    html_outline = _safe_read_under(root, outline_rel) or ""
    if not visual_css and not html_outline:
        return {}
    return {
        "llm_context_mode": "patch",
        "visual_css": visual_css,
        "html_outline": html_outline,
        "visual_css_bytes": int(project.get("visual_css_bytes") or len(visual_css.encode("utf-8"))),
        "outline_node_count": int(project.get("outline_node_count") or 0),
        "visual_css_truncated": bool(project.get("visual_css_truncated")),
    }


def _load_project_meta(meta_path: Path) -> dict[str, Any] | None:
    if not meta_path.is_file():
        return None
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        if isinstance(meta, dict):
            return meta
    except (OSError, json.JSONDecodeError):
        pass
    return None


def load_http_preprocess_artifacts(
    cinema_dir: Path | str,
    active: dict[str, Any] | None,
) -> dict[str, Any]:
    """Load compact HTTP import artifacts for LLM prompts when the active project is http-*."""
    project = active if isinstance(active, dict) else {}
    project_id = str(project.get("id") or "")
    if not project_id.startswith("http-"):
        return {}
    meta_path = _project_meta_path(Path(cinema_dir), project_id)
    meta = _load_project_meta(meta_path)
    if not meta:
        return {}
    project_dir = meta_path.parent
    source_dir = project_dir / "source"
    css_rel = str(meta.get("visual_css_path") or "source/nexu-visual.css")
    outline_rel = str(meta.get("html_outline_path") or "source/nexu-outline.html")
    css_local = css_rel[len("source/") :] if css_rel.startswith("source/") else css_rel
    outline_local = outline_rel[len("source/") :] if outline_rel.startswith("source/") else outline_rel
    visual_css = _safe_read_under(source_dir, css_local) or ""
    html_outline = _safe_read_under(source_dir, outline_local) or ""
    if not visual_css and not html_outline:
        return {}
    return {
        "llm_context_mode": str(meta.get("llm_context_mode") or "patch"),
        "visual_css": visual_css,
        "html_outline": html_outline,
        "visual_css_bytes": int(meta.get("visual_css_bytes") or len(visual_css.encode("utf-8"))),
        "outline_node_count": int(meta.get("outline_node_count") or 0),
        "visual_css_truncated": bool(meta.get("visual_css_truncated")),
    }


def build_http_llm_context(artifacts: dict[str, Any]) -> str:
    """Combine visual CSS + HTML outline for compact LLM patch prompts."""
    css = str(artifacts.get("visual_css") or "").strip()
    outline = str(artifacts.get("html_outline") or "").strip()
    if not css and not outline:
        return ""
    parts = [
        "IMPORTED WEB PAGE (patch mode — change CSS property values and minimal HTML attributes only; "
        "do not replace the entire document).",
    ]
    if css:
        parts.append("Visual CSS (colors, shapes, layout tokens):\n```css\n" + css + "\n```")
    if outline:
        parts.append("HTML structure outline:\n```html\n" + outline + "\n```")
    return "\n\n".join(parts)


def http_patch_llm_rules() -> str:
    """Extra LLM rules when iterating imported HTTP projects in patch mode."""
    return "\n".join(
        [
            "PATCH MODE: the page was imported from the live web.",
            "Prefer editing CSS property values in the visual CSS block; avoid regenerating the full HTML document.",
            "Preserve ids, classes, data-nexu-* markers, and the HTML skeleton structure.",
            "When HTML changes are required, patch only attributes or minimal wrapper nodes — never replace the whole tree.",
            "Do NOT include <script> tags — runtime is injected by Nexu after generation.",
        ]
    )
