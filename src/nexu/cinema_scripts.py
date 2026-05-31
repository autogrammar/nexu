"""Canonical Cinema iframe scripts (annotation shield + calculator runtime)."""

from __future__ import annotations

import re
from pathlib import Path

SHIELD_SCRIPT = """
    <script>
        console.log("[NEXU CHILD] IFrame loaded: " + window.location.pathname);

        const style = document.createElement('style');
        style.innerHTML = `
            .selection-box {
                position: fixed;
                border: 2px dashed #2ed573;
                background: rgba(46, 213, 115, 0.15);
                pointer-events: none;
                z-index: 99999;
                display: none;
                border-radius: 4px;
                box-shadow: 0 0 8px rgba(46, 213, 115, 0.3);
            }
            .selection-box.delete {
                border-color: #ff4757;
                background: rgba(255, 71, 87, 0.15);
                box-shadow: 0 0 8px rgba(255, 71, 87, 0.3);
            }
        `;
        document.head.appendChild(style);

        let selectionBox = null;
        let isDrawing = false;
        let startX = 0, startY = 0;
        let selectionType = 'KEEP';

        function getSelectionBox() {
            if (!selectionBox) {
                selectionBox = document.createElement('div');
                selectionBox.className = 'selection-box';
                document.body.appendChild(selectionBox);
            }
            return selectionBox;
        }

        function calcButtonTarget(node) {
            return node && node.closest
                ? node.closest('.btn, .btn-sci, .btn-sci-excess, .btn-op')
                : null;
        }

        document.addEventListener('contextmenu', (e) => {
            e.preventDefault();
            e.stopPropagation();
        }, true);

        document.addEventListener('mousedown', (e) => {
            const isActiveWorkspace = window.location.search.includes('active=true');
            if (!isActiveWorkspace) return;

            const onBtn = calcButtonTarget(e.target);
            if (onBtn && e.button === 0) {
                return;
            }

            if (e.button === 0) {
                selectionType = 'KEEP';
            } else if (e.button === 2) {
                selectionType = 'DELETE';
            } else {
                return;
            }

            isDrawing = true;
            startX = e.clientX;
            startY = e.clientY;
            const box = getSelectionBox();
            box.className = 'selection-box' + (selectionType === 'DELETE' ? ' delete' : '');
            box.style.left = startX + 'px';
            box.style.top = startY + 'px';
            box.style.width = '0px';
            box.style.height = '0px';
            box.style.display = 'block';
            e.preventDefault();
        });

        document.addEventListener('mousemove', (e) => {
            if (!isDrawing) return;
            const currentX = e.clientX;
            const currentY = e.clientY;
            const x = Math.min(startX, currentX);
            const y = Math.min(startY, currentY);
            const width = Math.abs(startX - currentX);
            const height = Math.abs(startY - currentY);
            const box = getSelectionBox();
            box.style.left = x + 'px';
            box.style.top = y + 'px';
            box.style.width = width + 'px';
            box.style.height = height + 'px';
        });

        document.addEventListener('mouseup', (e) => {
            if (!isDrawing) return;
            isDrawing = false;
            const box = getSelectionBox();
            const rect = box.getBoundingClientRect();
            box.style.display = 'none';
            const isSingleClick = rect.width < 8 && rect.height < 8;
            const elements = document.querySelectorAll(
                '.btn, .btn-sci, .btn-sci-excess, .btn-op, .screen'
            );
            elements.forEach(el => {
                const elRect = el.getBoundingClientRect();
                const intersects = !(
                    elRect.right < rect.left ||
                    elRect.left > rect.right ||
                    elRect.bottom < rect.top ||
                    elRect.top > rect.bottom
                );
                if (intersects || (isSingleClick && el === e.target)) {
                    const rawId = (el.id || '').trim();
                    const elementId = rawId ? rawId.replace(/^btn-/, '') : (el.innerText || '').trim();
                    window.parent.postMessage({
                        type: 'annotation',
                        elementId: elementId,
                        action: selectionType,
                    }, '*');
                }
            });
            setTimeout(() => {
                window.parent.postMessage({ type: 'selection_updated' }, '*');
            }, 100);
        });

        document.addEventListener('click', (e) => {
            const isActiveWorkspace = window.location.search.includes('active=true');
            if (!isActiveWorkspace) {
                e.preventDefault();
                e.stopPropagation();
                const currentFile = window.location.pathname.split('/').pop();
                window.parent.postMessage({ type: 'promote', altSrc: currentFile }, '*');
            }
        }, true);

        window.addEventListener('message', (e) => {
            if (e.data && e.data.type === 'sync') {
                const annotations = e.data.annotations;
                const elements = document.querySelectorAll(
                    '.btn, .btn-sci, .btn-sci-excess, .btn-op, .screen'
                );
                elements.forEach(el => {
                    const rawId = (el.id || '').trim();
                    const elementId = rawId ? rawId.replace(/^btn-/, '') : (el.innerText || '').trim();
                    const match = annotations.find(a => a.id === elementId);
                    if (match) {
                        if (match.type === 'KEEP') {
                            el.style.outline = '3px solid #2ed573';
                            el.style.outlineOffset = '-3px';
                            el.style.boxShadow = '0 0 12px rgba(46, 213, 115, 0.4)';
                        } else {
                            el.style.outline = '3px solid #ff4757';
                            el.style.outlineOffset = '-3px';
                            el.style.boxShadow = '0 0 12px rgba(255, 71, 87, 0.4)';
                        }
                    } else {
                        el.style.outline = 'none';
                        el.style.boxShadow = 'none';
                    }
                });
            }
        });
    </script>
"""

CALCULATOR_RUNTIME_SCRIPT = """
    <script>
        (function () {
            function calcButtonTarget(node) {
                return node && node.closest
                    ? node.closest('.btn, .btn-sci, .btn-sci-excess, .btn-op')
                    : null;
            }

            const screen = document.getElementById('screen');
            if (!screen) return;

            const ATOMIC = {
                H: 1.008, He: 4.003, Li: 6.94, C: 12.011, N: 14.007, O: 15.999,
                F: 18.998, Na: 22.99, Mg: 24.305, P: 30.974, S: 32.06, Cl: 35.45,
                K: 39.098, Ca: 40.078, Fe: 55.845, Cu: 63.546, Zn: 65.38,
            };

            let expr = String(screen.textContent || '0').trim();
            const isActive = () => window.location.search.includes('active=true');

            function render() {
                screen.textContent = expr || '0';
            }

            function molarMass(formula) {
                let i = 0;
                let total = 0;
                const raw = formula.replace(/\\s+/g, '');
                while (i < raw.length) {
                    if (!/[A-Z]/.test(raw[i])) return null;
                    let sym = raw[i++];
                    if (i < raw.length && /[a-z]/.test(raw[i])) sym += raw[i++];
                    let digits = '';
                    while (i < raw.length && /\\d/.test(raw[i])) digits += raw[i++];
                    const count = digits ? parseInt(digits, 10) : 1;
                    if (!ATOMIC[sym]) return null;
                    total += ATOMIC[sym] * count;
                }
                return total > 0 ? total : null;
            }

            function safeMathEval(input) {
                const sanitized = input.replace(/\\s+/g, '');
                if (!/^[0-9+\\-*/().]+$/.test(sanitized)) return null;
                try {
                    // eslint-disable-next-line no-new-func
                    const value = Function('"use strict"; return (' + sanitized + ')')();
                    return Number.isFinite(value) ? value : null;
                } catch (_) {
                    return null;
                }
            }

            function tokenFromButton(btn) {
                const id = (btn.id || '').toLowerCase();
                const text = (btn.innerText || '').trim();
                if (/^btn-([0-9])$/.test(id)) return id.slice(-1);
                if (id === 'btn-0' || text === '0') return '0';
                if (id === 'btn-dot' || text === '.') return '.';
                if (id === 'btn-add' || text === '+') return '+';
                if (id === 'btn-sub' || text === '-') return '-';
                if (id === 'btn-mul' || text === '*') return '*';
                if (id === 'btn-div' || text === '/') return '/';
                if (id === 'btn-eq' || text === '=') return '=';
                if (id === 'btn-clr' || id === 'btn-clear' || text === 'C') return 'C';
                if (text.length <= 3 && /^[A-Z][a-z]?$/.test(text)) return text;
                if (text.length <= 6) return text;
                return text;
            }

            function onCalcPress(token) {
                if (token === 'C') {
                    expr = '0';
                    render();
                    return;
                }
                if (token === '=') {
                    const mass = molarMass(expr);
                    if (mass != null) {
                        expr = expr + ': ' + mass.toFixed(2) + ' g/mol';
                        render();
                        return;
                    }
                    const math = safeMathEval(expr);
                    if (math != null) {
                        expr = String(math);
                        render();
                        return;
                    }
                    render();
                    return;
                }
                if (expr === '0' && token !== '.' && !'+-*/'.includes(token)) {
                    expr = token;
                } else {
                    expr += token;
                }
                render();
            }

            document.addEventListener('click', (e) => {
                if (!isActive()) return;
                const btn = calcButtonTarget(e.target);
                if (!btn) return;
                e.stopPropagation();
                e.preventDefault();
                onCalcPress(tokenFromButton(btn));
            }, true);

            render();
        })();
    </script>
"""

_SCRIPT_TAG_RE = re.compile(r"<script\b[^>]*>[\s\S]*?</script>", re.IGNORECASE)
_BTN_DIV_RE = re.compile(
    r'<div\b([^>]*\bclass="[^"]*\bbtn[^"]*"[^>]*)>([^<]*)</div>',
    re.IGNORECASE,
)


def _delete_match_keys(element_id: str) -> set[str]:
    raw = (element_id or "").strip()
    if not raw:
        return set()
    keys = {raw, raw.lower()}
    if raw.lower().startswith("btn-"):
        keys.add(raw[4:])
        keys.add(raw[4:].lower())
    else:
        keys.add(f"btn-{raw}")
        keys.add(f"btn-{raw.lower()}")
    return keys


def apply_spatial_deletes_to_html(html: str, delete_ids: list[str]) -> tuple[str, list[str]]:
    """
    Remove only annotated DELETE controls from calculator HTML (no LLM rewrite).

    Matches .btn / .btn-sci / .btn-sci-excess / .btn-op by id or visible label (e.g. Mod → btn-Mod).
    """
    if not html or not delete_ids:
        return html, []

    delete_keys: set[str] = set()
    for element_id in delete_ids:
        delete_keys |= _delete_match_keys(str(element_id))

    removed: list[str] = []

    def _replacer(match: re.Match[str]) -> str:
        attrs, label = match.group(1), match.group(2).strip()
        id_match = re.search(r'\bid="([^"]*)"', attrs, re.IGNORECASE)
        el_id = id_match.group(1) if id_match else ""
        candidates = _delete_match_keys(el_id) | _delete_match_keys(label)
        if delete_keys.intersection(candidates):
            removed.append(label or el_id or "unknown")
            return ""
        return match.group(0)

    patched = _BTN_DIV_RE.sub(_replacer, html)
    return patched, removed


def finalize_cinema_html(html: str, *, inject: str | None = None) -> str:
    """Strip LLM scripts (often truncated) and append canonical shield + calculator runtime."""
    if not html or "<!DOCTYPE" not in html.upper()[:80]:
        return html

    cleaned = _SCRIPT_TAG_RE.sub("", html)
    bundle = inject if inject is not None else (SHIELD_SCRIPT + CALCULATOR_RUNTIME_SCRIPT)

    lower = cleaned.lower()
    if "</body>" in lower:
        idx = lower.rfind("</body>")
        return cleaned[:idx] + bundle + cleaned[idx:]
    if "</html>" in lower:
        idx = lower.rfind("</html>")
        return cleaned[:idx] + bundle + cleaned[idx:]
    return cleaned.rstrip() + bundle + "\n</body>\n</html>\n"


def write_cinema_inject_files(cinema_dir: Path) -> None:
    cinema_dir.mkdir(parents=True, exist_ok=True)
    (cinema_dir / "_inject_shield.html").write_text(SHIELD_SCRIPT, encoding="utf-8")
    (cinema_dir / "_inject_runtime.html").write_text(CALCULATOR_RUNTIME_SCRIPT, encoding="utf-8")


def repair_cinema_html_files(cinema_dir: Path) -> int:
    """Re-apply canonical scripts to existing stage/alt HTML (fixes truncated LLM output)."""
    write_cinema_inject_files(cinema_dir)
    repaired = 0
    for path in sorted(cinema_dir.glob("*.html")):
        if path.name.startswith("_inject") or path.name == "cinema_player.html":
            continue
        text = path.read_text(encoding="utf-8")
        if "<!DOCTYPE" not in text.upper()[:80]:
            continue
        path.write_text(finalize_cinema_html(text), encoding="utf-8")
        repaired += 1
    return repaired
