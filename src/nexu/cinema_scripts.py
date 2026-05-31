"""Canonical Cinema iframe scripts (annotation shield + calculator runtime)."""

from __future__ import annotations

import re
from pathlib import Path

SHIELD_SCRIPT = """
    <script>
        const NEXU_PARAMS = new URLSearchParams(window.location.search);
        function nexuParam(name, fallback) {
            const v = NEXU_PARAMS.get(name);
            return v !== null && v !== '' ? v : fallback;
        }
        function nexuBool(name, defaultVal) {
            const v = NEXU_PARAMS.get(name);
            if (v === null || v === '') return defaultVal;
            return v === '1' || v === 'true' || v === 'yes';
        }
        const NEXU_ROLE = nexuParam(
            'role',
            NEXU_PARAMS.get('active') === 'true' ? 'workspace' : 'option'
        );
        const NEXU_PANE = nexuParam('pane', '');
        const NEXU_MARK = nexuBool('mark', NEXU_ROLE === 'workspace');
        const NEXU_CALC = nexuBool('calc', false);
        const NEXU_STAGE = nexuParam('stage', '0');

        function isActiveWorkspace() {
            return NEXU_ROLE === 'workspace' || NEXU_PARAMS.get('active') === 'true';
        }
        function isMarkingEnabled() {
            return NEXU_MARK && isActiveWorkspace();
        }
        function nexuLog(event, detail) {
            const payload = {
                type: 'nexu_log',
                event: event,
                detail: detail || {},
                href: window.location.pathname + window.location.search,
                role: NEXU_ROLE,
                pane: NEXU_PANE,
                stage: NEXU_STAGE,
                mark: NEXU_MARK,
                calc: NEXU_CALC,
            };
            console.log('[NEXU IFRAME]', event, detail || '', window.location.search);
            try { window.parent.postMessage(payload, '*'); } catch (_) {}
        }

        window.__NEXU_REVIEW_MODE__ = nexuBool('review', NEXU_ROLE === 'workspace');

        const style = document.createElement('style');
        style.innerHTML = `
            .selection-box {
                position: fixed;
                border: 2px dashed #2ed573;
                background: rgba(46, 213, 115, 0.15);
                pointer-events: none;
                z-index: 99998;
                display: none;
                border-radius: 4px;
            }
            .selection-box.delete {
                border-color: #ff4757;
                background: rgba(255, 71, 87, 0.15);
            }
            .nexu-review-dock {
                position: fixed;
                left: 50%;
                bottom: 12px;
                transform: translateX(-50%);
                display: none;
                flex-direction: column;
                align-items: center;
                gap: 8px;
                z-index: 100000;
                font-family: 'Outfit', sans-serif;
                pointer-events: auto;
            }
            .nexu-review-dock.visible { display: flex; }
            .nexu-review-label {
                background: rgba(15, 23, 42, 0.92);
                color: #e2e8f0;
                padding: 6px 14px;
                border-radius: 20px;
                font-size: 13px;
                border: 1px solid rgba(255,255,255,0.12);
            }
            .nexu-review-actions {
                display: flex;
                gap: 16px;
                align-items: center;
            }
            .nexu-review-btn {
                width: 56px;
                height: 56px;
                border-radius: 50%;
                border: none;
                font-size: 26px;
                cursor: pointer;
                box-shadow: 0 4px 20px rgba(0,0,0,0.35);
                transition: transform 0.15s ease;
            }
            .nexu-review-btn:hover { transform: scale(1.08); }
            .nexu-review-btn.reject {
                background: linear-gradient(135deg, #ff6b81, #ff4757);
                color: #fff;
            }
            .nexu-review-btn.accept {
                background: linear-gradient(135deg, #2ed573, #26de81);
                color: #0f172a;
            }
            .nexu-review-hint {
                font-size: 10px;
                color: #94a3b8;
                text-align: center;
            }
            .btn.nexu-focus-pulse,
            button.nexu-focus-pulse {
                outline: 3px solid #38bdf8 !important;
                outline-offset: 2px !important;
                box-shadow: 0 0 16px rgba(56, 189, 248, 0.55) !important;
                z-index: 99990;
                position: relative;
            }
        `;
        document.head.appendChild(style);

        const SELECTOR = [
            '.btn',
            '.btn-sci',
            '.btn-sci-excess',
            '.btn-op',
            '.screen',
            '.grid > button',
            '.sci-grid > button',
        ].join(', ');
        let selectionBox = null;
        let isDrawing = false;
        let startX = 0, startY = 0;
        let selectionType = 'KEEP';
        let focusedEl = null;
        let focusedId = '';
        let annotatedIds = new Set();
        let swipeStartX = 0;

        const dock = document.createElement('div');
        dock.className = 'nexu-review-dock';
        dock.innerHTML = `
            <div class="nexu-review-label" id="nexu-review-label">Tap a control</div>
            <div class="nexu-review-actions">
                <button type="button" class="nexu-review-btn reject"
                    id="nexu-btn-reject" title="Remove">✗</button>
                <button type="button" class="nexu-review-btn accept"
                    id="nexu-btn-accept" title="Keep">✓</button>
            </div>
            <div class="nexu-review-hint">← remove · → keep · swipe on card</div>
        `;
        document.body.appendChild(dock);

        function calcButtonTarget(node) {
            return node && node.closest ? node.closest(SELECTOR) : null;
        }

        function elementIdFromEl(el) {
            const rawId = (el.id || '').trim();
            if (rawId) return rawId.replace(/^btn-/, '');
            const text = (el.innerText || '').trim();
            if (el.tagName === 'BUTTON' && text) return text;
            return text;
        }

        function allTargets() {
            return Array.from(document.querySelectorAll(SELECTOR));
        }

        nexuLog('iframe_boot', {
            review: window.__NEXU_REVIEW_MODE__,
            marking: isMarkingEnabled(),
            targets: allTargets().length,
        });

        function clearFocusPulse() {
            allTargets().forEach(el => el.classList.remove('nexu-focus-pulse'));
        }

        function setFocus(el) {
            clearFocusPulse();
            focusedEl = el;
            focusedId = elementIdFromEl(el);
            if (el) {
                el.classList.add('nexu-focus-pulse');
                const label = document.getElementById('nexu-review-label');
                if (label) label.textContent = '#' + focusedId;
            }
        }

        function updateDockVisibility() {
            if (!isMarkingEnabled() || !window.__NEXU_REVIEW_MODE__) {
                dock.classList.remove('visible');
                return;
            }
            dock.classList.add('visible');
        }

        function postAnnotation(action) {
            if (!focusedId) return;
            nexuLog('annotate', { elementId: focusedId, action: action, mode: 'review' });
            window.parent.postMessage({
                type: 'annotation',
                elementId: focusedId,
                action: action,
            }, '*');
            annotatedIds.add(focusedId);
            setTimeout(() => {
                window.parent.postMessage({ type: 'selection_updated' }, '*');
                advanceToNext();
            }, 80);
        }

        function advanceToNext() {
            const next = allTargets().find(el => !annotatedIds.has(elementIdFromEl(el)));
            if (next) {
                setFocus(next);
            } else {
                clearFocusPulse();
                focusedEl = null;
                focusedId = '';
                const label = document.getElementById('nexu-review-label');
                if (label) label.textContent = 'All reviewed ✓';
            }
        }

        document.getElementById('nexu-btn-accept').addEventListener('click', (e) => {
            e.stopPropagation();
            postAnnotation('KEEP');
        });
        document.getElementById('nexu-btn-reject').addEventListener('click', (e) => {
            e.stopPropagation();
            postAnnotation('DELETE');
        });

        function getSelectionBox() {
            if (!selectionBox) {
                selectionBox = document.createElement('div');
                selectionBox.className = 'selection-box';
                document.body.appendChild(selectionBox);
            }
            return selectionBox;
        }

        document.addEventListener('contextmenu', (e) => {
            e.preventDefault();
            e.stopPropagation();
        }, true);

        document.addEventListener('mousedown', (e) => {
            if (!isMarkingEnabled()) return;
            if (window.__NEXU_REVIEW_MODE__) {
                if (e.target.closest('.nexu-review-dock')) return;
                const onBtn = calcButtonTarget(e.target);
                if (onBtn) {
                    e.preventDefault();
                    e.stopPropagation();
                    setFocus(onBtn);
                    swipeStartX = e.clientX;
                    nexuLog('review_focus', { elementId: focusedId });
                }
                return;
            }

            if (e.button === 0) selectionType = 'KEEP';
            else if (e.button === 2) selectionType = 'DELETE';
            else return;

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
            nexuLog('drag_start', { button: e.button, type: selectionType, x: startX, y: startY });
        });

        document.addEventListener('mousemove', (e) => {
            if (!isDrawing) return;
            const x = Math.min(startX, e.clientX);
            const y = Math.min(startY, e.clientY);
            const box = getSelectionBox();
            box.style.left = x + 'px';
            box.style.top = y + 'px';
            box.style.width = Math.abs(startX - e.clientX) + 'px';
            box.style.height = Math.abs(startY - e.clientY) + 'px';
        });

        document.addEventListener('mouseup', (e) => {
            if (window.__NEXU_REVIEW_MODE__ && isActiveWorkspace() && focusedEl) {
                const dx = e.clientX - swipeStartX;
                if (Math.abs(dx) > 48) {
                    postAnnotation(dx > 0 ? 'KEEP' : 'DELETE');
                    return;
                }
            }
            if (!isDrawing) return;
            isDrawing = false;
            const box = getSelectionBox();
            const rect = box.getBoundingClientRect();
            box.style.display = 'none';
            const isSingleClick = rect.width < 8 && rect.height < 8;
            allTargets().forEach(el => {
                const elRect = el.getBoundingClientRect();
                const intersects = !(
                    elRect.right < rect.left || elRect.left > rect.right ||
                    elRect.bottom < rect.top || elRect.top > rect.bottom
                );
                const hit = calcButtonTarget(e.target);
                if (intersects || (isSingleClick && hit === el)) {
                    const eid = elementIdFromEl(el);
                    nexuLog('annotate', { elementId: eid, action: selectionType, mode: 'drag' });
                    window.parent.postMessage({
                        type: 'annotation',
                        elementId: eid,
                        action: selectionType,
                    }, '*');
                }
            });
            setTimeout(() => window.parent.postMessage({ type: 'selection_updated' }, '*'), 100);
        });

        document.addEventListener('keydown', (e) => {
            if (!window.__NEXU_REVIEW_MODE__ || !isActiveWorkspace() || !focusedId) return;
            if (e.key === 'ArrowRight') { e.preventDefault(); postAnnotation('KEEP'); }
            if (e.key === 'ArrowLeft') { e.preventDefault(); postAnnotation('DELETE'); }
        });

        document.addEventListener('click', (e) => {
            if (isMarkingEnabled()) {
                if (window.__NEXU_REVIEW_MODE__ && calcButtonTarget(e.target)) {
                    e.preventDefault();
                    e.stopPropagation();
                }
                return;
            }
            if (!isActiveWorkspace()) {
                e.preventDefault();
                e.stopPropagation();
                const currentFile = window.location.pathname.split('/').pop();
                nexuLog('promote_click', { altSrc: currentFile, pane: NEXU_PANE });
                window.parent.postMessage({ type: 'promote', altSrc: currentFile }, '*');
                return;
            }
        }, true);

        function applyAnnotationStyles(annotations) {
            annotatedIds = new Set((annotations || []).map(a => a.id));
            allTargets().forEach(el => {
                const elementId = elementIdFromEl(el);
                const match = (annotations || []).find(a => a.id === elementId);
                if (match) {
                    if (match.type === 'KEEP') {
                        el.style.outline = '3px solid #2ed573';
                        el.style.boxShadow = '0 0 12px rgba(46, 213, 115, 0.4)';
                    } else {
                        el.style.outline = '3px solid #ff4757';
                        el.style.boxShadow = '0 0 12px rgba(255, 71, 87, 0.4)';
                    }
                } else {
                    el.style.outline = 'none';
                    el.style.boxShadow = 'none';
                }
            });
        }

        window.addEventListener('message', (e) => {
            if (!e.data) return;
            if (e.data.type === 'review_mode') {
                window.__NEXU_REVIEW_MODE__ = !!e.data.enabled;
                nexuLog('review_mode', { enabled: window.__NEXU_REVIEW_MODE__ });
                updateDockVisibility();
                if (window.__NEXU_REVIEW_MODE__ && isMarkingEnabled()) {
                    advanceToNext();
                }
                return;
            }
            if (e.data.type === 'sync') {
                applyAnnotationStyles(e.data.annotations);
                nexuLog('sync', { count: (e.data.annotations || []).length });
                if (window.__NEXU_REVIEW_MODE__ && isMarkingEnabled() && !focusedId) {
                    advanceToNext();
                }
            }
        });

        updateDockVisibility();
        if (isMarkingEnabled() && window.__NEXU_REVIEW_MODE__) {
            setTimeout(advanceToNext, 300);
        }
    </script>
"""

CALCULATOR_RUNTIME_SCRIPT = """
    <script>
        (function () {
            const calcParams = new URLSearchParams(window.location.search);
            if (calcParams.get('calc') !== '1') {
                console.log(
                    '[NEXU CALC] disabled — use ?calc=1 to enable keypad',
                    window.location.search
                );
                return;
            }
            console.log('[NEXU CALC] enabled', window.location.search);

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
                if (window.__NEXU_REVIEW_MODE__) return;
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
