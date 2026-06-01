"""Shared Cinema HTML normalization helpers."""

from __future__ import annotations


def ensure_html_document_closure(html: str) -> str:
    """Add missing body/html closing tags to a partial HTML document."""
    out = str(html or "").strip()
    lower = out.lower()
    if "<html" not in lower:
        return out
    if "</body>" not in lower:
        out += "\n</body>"
    if "</html>" not in lower:
        out += "\n</html>"
    return out
