from __future__ import annotations

import json
from pathlib import Path
from .paths import capsule_dir

def generate_cinema_player(root: Path, name: str) -> Path:
    """
    Natively generates the Interactive Cinema Player for a capsule.
    Employs the gorgeous vertical stacked options layout:
    - Left part: Large Active Workspace (Window 1)
    - Middle part: Vertically stacked Options A, B, C (Windows 2-4) that dynamically expand on hover
    - Right part: Controls, logs, and prompt boxes
    """
    base = capsule_dir(root, name)
    cinema_dir = base / "cinema"
    cinema_dir.mkdir(parents=True, exist_ok=True)
    
    # Combined shield and communication script to inject into every child iframe
    shield_script = """
    <script>
        // Combined unified contextmenu listener to prevent starvation
        document.addEventListener('contextmenu', (e) => {
            e.preventDefault();
            e.stopPropagation();
            
            const btn = e.target.closest('.btn, .btn-sci, .btn-sci-excess, .screen');
            if (btn) {
                const elementId = btn.innerText.trim() || btn.id;
                window.parent.postMessage({
                    type: 'annotation',
                    elementId: elementId,
                    action: 'DELETE'
                }, '*');
            }
        }, true);

        // Send left clicks directly to parent using postMessage (bypasses file:// sandbox)
        document.addEventListener('click', (e) => {
            // Securely determine active workspace status via location search
            const isActiveWorkspace = window.location.search.includes('active=true');
            
            if (isActiveWorkspace) {
                const btn = e.target.closest('.btn, .btn-sci, .btn-sci-excess, .screen');
                if (btn) {
                    e.preventDefault();
                    e.stopPropagation();
                    const elementId = btn.innerText.trim() || btn.id;
                    window.parent.postMessage({
                        type: 'annotation',
                        elementId: elementId,
                        action: 'KEEP'
                    }, '*');
                }
            } else {
                // Clicking anywhere in alternative options promotes it!
                e.preventDefault();
                e.stopPropagation();
                const currentFile = window.location.pathname.split('/').pop();
                window.parent.postMessage({
                    type: 'promote',
                    altSrc: currentFile
                }, '*');
            }
        }, true);

        // Receive highlights sync from parent
        window.addEventListener('message', (e) => {
            if (e.data && e.data.type === 'sync') {
                const annotations = e.data.annotations;
                const elements = document.querySelectorAll('.btn, .btn-sci, .btn-sci-excess, .screen');
                elements.forEach(el => {
                    const elementId = el.innerText.trim() || el.id;
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

    # 1. Simple baseline calculator (stage0.html)
    simple_calc = f"""<!DOCTYPE html>
<html>
<head>
    <title>Simple Calculator</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600&display=swap" rel="stylesheet">
    <style>
        html, body {{
            height: 100%;
            width: 100%;
            margin: 0;
            overflow: hidden;
            background: #0f172a;
            color: #fff;
            font-family: 'Outfit', sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
        }}
        .calc-body {{
            background: #1e293b;
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 16px;
            padding: 15px;
            
            width: 90%;
            height: 90%;
            max-width: 70vh;
            max-height: 120vw;
            aspect-ratio: 3/4;
            
            box-shadow: 0 10px 25px rgba(0,0,0,0.3);
            display: flex;
            flex-direction: column;
            box-sizing: border-box;
        }}
        .screen {{
            background: #0f172a;
            color: #38bdf8;
            font-size: calc(12px + 2vh);
            text-align: right;
            padding: 10px;
            border-radius: 8px;
            margin-bottom: 10px;
            border: 1px solid rgba(255,255,255,0.05);
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            grid-auto-rows: 1fr;
            gap: 8px;
            flex: 1;
        }}
        .btn {{
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.08);
            color: #fff;
            font-size: calc(10px + 1.2vh);
            font-weight: 600;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            user-select: none;
            transition: all 0.15s ease;
        }}
        .btn-op {{ background: #e67e22; color: #fff; }}
    </style>
</head>
<body>
    <div class="calc-body">
        <div class="screen" id="screen">12.5</div>
        <div class="grid">
            <div class="btn" id="btn-7">7</div><div class="btn" id="btn-8">8</div><div class="btn" id="btn-9">9</div><div class="btn btn-op" id="btn-div">/</div>
            <div class="btn" id="btn-4">4</div><div class="btn" id="btn-5">5</div><div class="btn" id="btn-6">6</div><div class="btn btn-op" id="btn-mul">*</div>
            <div class="btn" id="btn-1">1</div><div class="btn" id="btn-2">2</div><div class="btn" id="btn-3">3</div><div class="btn btn-op" id="btn-sub">-</div>
            <div class="btn" id="btn-0">0</div><div class="btn" id="btn-dot">.</div><div class="btn btn-op" id="btn-eq" style="background:#2ecc71;">=</div><div class="btn btn-op" id="btn-add">+</div>
        </div>
    </div>
    {shield_script}
</body>
</html>"""
    (cinema_dir / "stage0.html").write_text(simple_calc, encoding="utf-8")

    # 2. Minimalist scientific (alt_a.html)
    alt_a = f"""<!DOCTYPE html>
<html>
<head>
    <title>Option A: Minimalist Scientific</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600&display=swap" rel="stylesheet">
    <style>
        html, body {{
            height: 100%;
            width: 100%;
            margin: 0;
            overflow: hidden;
            background: #0f172a;
            color: #fff;
            font-family: 'Outfit', sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
        }}
        .calc-body {{
            background: #1e293b;
            border-radius: 12px;
            padding: 15px;
            
            width: 90%;
            height: 90%;
            max-width: 70vh;
            max-height: 120vw;
            aspect-ratio: 3/4;
            
            display: flex;
            flex-direction: column;
            box-sizing: border-box;
        }}
        .screen {{ background: #0f172a; color: #2ecc71; font-size: calc(10px + 2vh); text-align: right; padding: 10px; border-radius: 6px; margin-bottom: 10px; }}
        .grid {{ display: grid; grid-template-columns: repeat(4, 1fr); grid-auto-rows: 1fr; gap: 8px; flex: 1; }}
        .btn {{
            background: rgba(255,255,255,0.05);
            color: #fff;
            font-size: calc(8px + 1vh);
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            user-select: none;
            transition: all 0.15s ease;
        }}
        .btn-sci {{ background: #38bdf8; color: #0f172a; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="calc-body">
        <div class="screen" id="screen">12.5</div>
        <div class="grid">
            <div class="btn btn-sci" id="btn-pow2">x²</div><div class="btn btn-sci" id="btn-sqrt">√</div><div class="btn" id="btn-clear" style="grid-column: span 2; background: #e67e22;">C</div>
            <div class="btn" id="btn-7">7</div><div class="btn" id="btn-8">8</div><div class="btn" id="btn-9">9</div><div class="btn" id="btn-div" style="background:#e67e22;">/</div>
            <div class="btn" id="btn-4">4</div><div class="btn" id="btn-5">5</div><div class="btn" id="btn-6">6</div><div class="btn" id="btn-mul" style="background:#e67e22;">*</div>
            <div class="btn" id="btn-1">1</div><div class="btn" id="btn-2">2</div><div class="btn" id="btn-3">3</div><div class="btn" id="btn-sub" style="background:#e67e22;">-</div>
        </div>
    </div>
    {shield_script}
</body>
</html>"""
    (cinema_dir / "alt_a.html").write_text(alt_a, encoding="utf-8")

    # 3. Standard scientific (alt_b.html)
    alt_b = f"""<!DOCTYPE html>
<html>
<head>
    <title>Option B: Standard Scientific</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600&display=swap" rel="stylesheet">
    <style>
        html, body {{
            height: 100%;
            width: 100%;
            margin: 0;
            overflow: hidden;
            background: #0f172a;
            color: #fff;
            font-family: 'Outfit', sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
        }}
        .calc-body {{
            background: #1e293b;
            border-radius: 12px;
            padding: 15px;
            
            width: 90%;
            height: 90%;
            max-width: 70vh;
            max-height: 120vw;
            aspect-ratio: 3/4;
            
            display: flex;
            flex-direction: column;
            box-sizing: border-box;
        }}
        .screen {{ background: #0f172a; color: #2ecc71; font-size: calc(10px + 2vh); text-align: right; padding: 10px; border-radius: 6px; margin-bottom: 10px; }}
        .grid {{ display: grid; grid-template-columns: repeat(4, 1fr); grid-auto-rows: 1fr; gap: 8px; flex: 1; }}
        .btn {{
            background: rgba(255,255,255,0.05);
            color: #fff;
            font-size: calc(8px + 1vh);
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            user-select: none;
            transition: all 0.15s ease;
        }}
        .btn-sci {{ background: #38bdf8; color: #0f172a; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="calc-body">
        <div class="screen" id="screen">12.5</div>
        <div class="grid">
            <div class="btn btn-sci" id="btn-sin">sin</div><div class="btn btn-sci" id="btn-cos">cos</div><div class="btn btn-sci" id="btn-tan">tan</div><div class="btn btn-sci" id="btn-ln">ln</div>
            <div class="btn" id="btn-7">7</div><div class="btn" id="btn-8">8</div><div class="btn" id="btn-9">9</div><div class="btn" id="btn-div" style="background:#e67e22;">/</div>
            <div class="btn" id="btn-4">4</div><div class="btn" id="btn-5">5</div><div class="btn" id="btn-6">6</div><div class="btn" id="btn-mul" style="background:#e67e22;">*</div>
            <div class="btn" id="btn-1">1</div><div class="btn" id="btn-2">2</div><div class="btn" id="btn-3">3</div><div class="btn" id="btn-sub" style="background:#e67e22;">-</div>
        </div>
    </div>
    {shield_script}
</body>
</html>"""
    (cinema_dir / "alt_b.html").write_text(alt_b, encoding="utf-8")

    # 4. Expanded scientific (alt_c.html)
    alt_c = f"""<!DOCTYPE html>
<html>
<head>
    <title>Option C: Expanded Scientific (Many Buttons)</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600&display=swap" rel="stylesheet">
    <style>
        html, body {{
            height: 100%;
            width: 100%;
            margin: 0;
            overflow: hidden;
            background: #090d16;
            color: #fff;
            font-family: 'Outfit', sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
        }}
        .calc-body {{
            background: #1e293b;
            border-radius: 12px;
            padding: 12px;
            border: 1px solid rgba(255,255,255,0.1);
            
            width: 90%;
            height: 90%;
            max-width: 75vh;
            max-height: 115vw;
            aspect-ratio: 4/5;
            
            display: flex;
            flex-direction: column;
            box-sizing: border-box;
        }}
        .screen {{ background: #0f172a; color: #38bdf8; font-size: calc(8px + 1.8vh); text-align: right; padding: 8px; border-radius: 6px; margin-bottom: 8px; }}
        .grid {{ display: grid; grid-template-columns: repeat(5, 1fr); grid-auto-rows: 1fr; gap: 6px; flex: 1; }}
        .btn {{
            background: rgba(255,255,255,0.05);
            color: #fff;
            font-size: calc(6px + 0.9vh);
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            user-select: none;
            transition: all 0.15s ease;
        }}
        .btn-sci {{ background: #38bdf8; color: #0f172a; font-weight: bold; }}
        .btn-sci-excess {{ background: #818cf8; color: #fff; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="calc-body">
        <div class="screen" id="screen">12.5</div>
        <div class="grid">
            <div class="btn btn-sci" id="btn-sin">sin</div>
            <div class="btn btn-sci" id="btn-cos">cos</div>
            <div class="btn btn-sci" id="btn-tan">tan</div>
            <div class="btn btn-sci" id="btn-log">log</div>
            <div class="btn btn-sci" id="btn-ln">ln</div>
            
            <div class="btn btn-sci-excess" id="btn-EXP">EXP</div>
            <div class="btn btn-sci-excess" id="btn-Mod">Mod</div>
            <div class="btn btn-sci-excess" id="btn-deg">deg</div>
            <div class="btn btn-sci-excess" id="btn-rad">rad</div>
            <div class="btn btn-sci-excess" id="btn-pi">π</div>
            
            <div class="btn" id="btn-7">7</div><div class="btn" id="btn-8">8</div><div class="btn" id="btn-9">9</div><div class="btn" id="btn-div" style="background:#e67e22;">/</div><div class="btn" id="btn-clear" style="background:#e67e22;">C</div>
            <div class="btn" id="btn-4">4</div><div class="btn" id="btn-5">5</div><div class="btn" id="btn-6">6</div><div class="btn" id="btn-mul" style="background:#e67e22;">*</div><div class="btn" id="btn-lp" style="background:#e67e22;">(</div>
            <div class="btn" id="btn-1">1</div><div class="btn" id="btn-2">2</div><div class="btn" id="btn-3">3</div><div class="btn" id="btn-sub" style="background:#e67e22;">-</div><div class="btn" id="btn-rp" style="background:#e67e22;">)</div>
        </div>
    </div>
    {shield_script}
</body>
</html>"""
    (cinema_dir / "alt_c.html").write_text(alt_c, encoding="utf-8")

    # Make stage1.html and stage2.html hold intermediate evolution phases
    (cinema_dir / "stage1.html").write_text(alt_b, encoding="utf-8")
    (cinema_dir / "stage2.html").write_text(alt_c, encoding="utf-8")

    # Generate the cinema_player.html containing the interactive terminal and buttons
    player_path = cinema_dir / "cinema_player.html"
    
    player_html = """<!DOCTYPE html>
<html>
<head>
    <title>Nexu Multi-Option Cinema Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600&family=JetBrains+Mono&display=swap" rel="stylesheet">
    <style>
        body {
            margin: 0;
            background: #05070c;
            color: #f1f5f9;
            font-family: 'Outfit', sans-serif;
            display: flex;
            flex-direction: column;
            height: 100vh;
            overflow: hidden;
        }
        .header {
            background: rgba(15, 23, 42, 0.6);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid rgba(255,255,255,0.08);
            padding: 12px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            z-index: 10;
        }
        .header h1 {
            margin: 0;
            font-size: 1.4rem;
            color: #38bdf8;
            font-weight: 600;
        }
        .controls {
            display: flex;
            gap: 10px;
            align-items: center;
        }
        .btn {
            padding: 8px 14px;
            border-radius: 6px;
            font-weight: 600;
            cursor: pointer;
            border: none;
            transition: all 0.2s;
            font-size: 0.85rem;
        }
        .btn-stage { background: #334155; color: #fff; }
        .btn-stage.active { background: #38bdf8; color: #0f172a; }
        .btn-action { background: #2ed573; color: #fff; }
        
        .main-container {
            display: flex;
            flex: 1;
            overflow: hidden;
            background: #090d16;
        }
        
        /* Left Column: Active Workspace (Window 1) */
        .active-column {
            flex: 1;
            display: flex;
            flex-direction: column;
            padding: 15px;
            overflow: hidden;
        }
        
        /* Middle Column: Stacked Options A, B, C (Windows 2-4) */
        .options-column {
            width: 320px;
            display: flex;
            flex-direction: column;
            gap: 12px;
            padding: 15px;
            border-left: 1px solid rgba(255,255,255,0.08);
            border-right: 1px solid rgba(255,255,255,0.08);
            background: rgba(2, 6, 23, 0.4);
            overflow: hidden;
        }
        
        .panel {
            background: #020617;
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 12px;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            position: relative;
            cursor: pointer;
        }
        
        /* Left main panel style */
        .active-panel {
            flex: 1;
            border: 2px solid #38bdf8;
            box-shadow: 0 0 20px rgba(56, 189, 248, 0.1);
            cursor: default;
        }
        
        /* Middle panel stacked dynamic expansion */
        .option-panel {
            flex: 1;
            height: 0;
            transition: all 0.4s cubic-bezier(0.25, 1, 0.5, 1);
        }
        .option-panel:hover {
            flex: 2; /* dynamically grow while other panels shrink */
            border-color: #818cf8;
            box-shadow: 0 0 15px rgba(129, 140, 248, 0.2);
        }
        
        .panel-header {
            background: rgba(15,23,42,0.8);
            padding: 8px 12px;
            font-size: 0.75rem;
            font-weight: 600;
            color: #94a3b8;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid rgba(255,255,255,0.05);
            z-index: 200;
        }
        .panel-body {
            flex: 1;
            position: relative;
            overflow: hidden;
            transition: transform 0.4s cubic-bezier(0.25, 1, 0.5, 1);
            transform-origin: center center;
        }
        
        .option-panel:hover .panel-body {
            transform: scale(1.08);
        }
        
        iframe {
            width: 100%;
            height: 100%;
            border: none;
            background: transparent;
            pointer-events: auto;
        }
        
        /* Right Column: Chat & Feedback Controls */
        .side-panel {
            width: 380px;
            background: #05070c;
            display: flex;
            flex-direction: column;
            padding: 15px;
            overflow-y: auto;
        }
        .side-header {
            color: #94a3b8;
            font-size: 0.75rem;
            margin-bottom: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
            border-bottom: 1px solid rgba(255,255,255,0.05);
            padding-bottom: 6px;
            font-family: 'JetBrains+Mono', monospace;
        }
        
        /* Interactive Chat & Action Logs */
        .chat-logs {
            background: rgba(0,0,0,0.3);
            border: 1px solid rgba(255,255,255,0.05);
            border-radius: 8px;
            padding: 10px;
            font-size: 0.8rem;
            line-height: 1.4;
            max-height: 150px;
            overflow-y: auto;
            margin-bottom: 15px;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        .chat-msg {
            padding: 6px 10px;
            border-radius: 6px;
            font-size: 0.8rem;
        }
        .chat-msg.user {
            background: rgba(56, 189, 248, 0.1);
            color: #38bdf8;
            border-left: 3px solid #38bdf8;
            align-self: flex-start;
        }
        .chat-msg.system {
            background: rgba(46, 213, 115, 0.1);
            color: #2ed573;
            border-left: 3px solid #2ed573;
            align-self: flex-start;
        }
        
        .feedback-list {
            flex: 1;
            overflow-y: auto;
            margin-bottom: 15px;
        }
        .feedback-item {
            background: rgba(255,255,255,0.02);
            border: 1px solid rgba(255,255,255,0.05);
            border-radius: 6px;
            padding: 8px 12px;
            margin-bottom: 8px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.85rem;
        }
        .feedback-tag {
            font-weight: 600;
            font-size: 0.75rem;
            padding: 1px 5px;
            border-radius: 3px;
        }
        .feedback-tag.keep { background: rgba(46, 213, 115, 0.15); color: #2ed573; }
        .feedback-tag.redesign { background: rgba(255, 71, 87, 0.15); color: #ff4757; }
        
        .prompt-box {
            background: rgba(56, 189, 248, 0.05);
            border: 1px solid rgba(56, 189, 248, 0.15);
            border-radius: 6px;
            padding: 10px;
            font-size: 0.8rem;
            color: #38bdf8;
            font-family: 'JetBrains+Mono', monospace;
            white-space: pre-wrap;
            max-height: 120px;
            overflow-y: auto;
        }
        
        .promote-indicator {
            color: #818cf8;
            font-size: 0.7rem;
            background: rgba(129, 140, 248, 0.1);
            padding: 2px 6px;
            border-radius: 4px;
            font-weight: normal;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🎬 Nexu Multi-Option Cinema Dashboard</h1>
        <div class="controls">
            <button class="btn btn-stage active" onclick="switchStage(0)">S0: Simple Baseline</button>
            <button class="btn btn-stage" onclick="switchStage(1)">S1: Mid scientific</button>
            <button class="btn btn-stage" onclick="switchStage(2)">S2: Evolved</button>
        </div>
    </div>
    
    <div class="main-container">
        <!-- 1. Left Column: Active Workspace -->
        <div class="active-column">
            <div class="panel active-panel">
                <div class="panel-header" style="color: #38bdf8;">
                    <span>🔵 1. ACTIVE WORKSPACE</span>
                    <span style="font-size: 0.65rem;">[🖱️ Left Click = KEEP | 🖱️ Right Click = REDESIGN/DELETE]</span>
                </div>
                <div class="panel-body">
                    <iframe id="active-frame" name="active-frame" src="stage0.html?active=true"></iframe>
                </div>
            </div>
        </div>
        
        <!-- 2. Middle Column: Stacked Alternative Options -->
        <div class="options-column">
            <!-- Option A -->
            <div class="panel option-panel" onclick="promoteAlt('alt_a.html', 'Option A')">
                <div class="panel-header">
                    <span>⚡ OPTION A (Minimalist)</span>
                    <span class="promote-indicator">🖱️ Click</span>
                </div>
                <div class="panel-body">
                    <iframe id="alt-a-frame" name="alt-a-frame" src="alt_a.html"></iframe>
                </div>
            </div>
            
            <!-- Option B -->
            <div class="panel option-panel" onclick="promoteAlt('alt_b.html', 'Option B')">
                <div class="panel-header">
                    <span>⚡ OPTION B (Standard)</span>
                    <span class="promote-indicator">🖱️ Click</span>
                </div>
                <div class="panel-body">
                    <iframe id="alt-b-frame" name="alt-b-frame" src="alt_b.html"></iframe>
                </div>
            </div>
            
            <!-- Option C -->
            <div class="panel option-panel" onclick="promoteAlt('alt_c.html', 'Option C')">
                <div class="panel-header">
                    <span>⚡ OPTION C (Expanded)</span>
                    <span class="promote-indicator">🖱️ Click</span>
                </div>
                <div class="panel-body">
                    <iframe id="alt-c-frame" name="alt-c-frame" src="alt_c.html"></iframe>
                </div>
            </div>
        </div>
        
        <!-- 3. Right Column: Chat & Settings -->
        <div class="side-panel">
            <div class="side-header">💬 Live Chat & Automated Logs</div>
            <div class="chat-logs" id="chat-logs">
                <div class="chat-msg user"><strong>User:</strong> "wdrożenie kalkulatora naukowego na bazie aktualnego"</div>
            </div>
            
            <div class="side-header">📝 Visual Feedback list</div>
            <div class="feedback-list" id="feedback-list">
                <div style="color: #64748b; font-size: 0.85rem; text-align: center; margin-top: 40px;">
                    Left-click or Right-click elements directly in Active Workspace to annotate!
                </div>
            </div>
            
            <div class="side-header">🤖 Evolving Spatial Prompt</div>
            <div class="prompt-box" id="prompt-box">
Click anywhere on Options A-C to instantly promote them to Active Workspace!
            </div>
            
            <button class="btn btn-action" style="margin-top: 15px; width: 100%;" onclick="submitEcosystemFeedback()">
                🚀 Accept Iteration & Generate Prompt
            </button>
        </div>
    </div>

    <script>
        let activeStage = 0;
        let annotations = [];

        // Globally block context menu popup on the parent dashboard page
        document.addEventListener('contextmenu', (e) => {
            e.preventDefault();
            e.stopPropagation();
        }, true);

        // Ultimate cross-origin postMessage listener
        window.addEventListener('message', (e) => {
            if (!e.data) return;
            
            if (e.data.type === 'annotation') {
                handleAnnotation(e.data.elementId, e.data.action);
            }
            
            if (e.data.type === 'promote') {
                const label = e.data.altSrc.includes('alt_a') ? 'Option A (Minimalist)' :
                              e.data.altSrc.includes('alt_b') ? 'Option B (Standard)' : 'Option C (Expanded)';
                promoteAlt(e.data.altSrc, label);
            }
        });

        function addChatLog(sender, text) {
            const container = document.getElementById('chat-logs');
            const msg = document.createElement('div');
            msg.className = 'chat-msg ' + sender;
            msg.innerHTML = sender === 'user' ? `<strong>User:</strong> ${text}` : `<strong>System:</strong> ${text}`;
            container.appendChild(msg);
            container.scrollTop = container.scrollHeight;
        }

        function switchStage(stageNum) {
            activeStage = stageNum;
            document.querySelectorAll('.btn-stage').forEach((btn, idx) => {
                if(idx === stageNum) btn.classList.add('active');
                else btn.classList.remove('active');
            });
            
            const activeFrame = document.getElementById('active-frame');
            activeFrame.src = 'stage' + stageNum + '.html?active=true';
            addChatLog('system', '🔄 Loaded stage S' + stageNum + ' template.');
        }

        function handleAnnotation(elementId, type) {
            const existingIdx = annotations.findIndex(a => a.id === elementId);
            if (existingIdx >= 0) {
                annotations.splice(existingIdx, 1);
            }

            annotations.push({ id: elementId, type: type });

            // Post annotation log
            if (type === 'KEEP') {
                addChatLog('system', `✓ Element <strong>${elementId}</strong> accepted.`);
            } else {
                addChatLog('system', `✗ Element <strong>${elementId}</strong> marked for redesign.`);
            }

            // Sync visual highlights to ALL active child iframes using postMessage
            syncAllIframeVisuals();
            updateFeedbackList();
        }

        function syncAllIframeVisuals() {
            document.querySelectorAll('iframe').forEach(iframe => {
                if (iframe.contentWindow) {
                    iframe.contentWindow.postMessage({
                        type: 'sync',
                        annotations: annotations
                    }, '*');
                }
            });
        }

        // Periodically run visual highlight synchronizations to catch new iframe content loads
        setInterval(syncAllIframeVisuals, 200);

        function updateFeedbackList() {
            const list = document.getElementById('feedback-list');
            list.innerHTML = '';
            
            if (annotations.length === 0) {
                list.innerHTML = `<div style="color: #64748b; font-size: 0.85rem; text-align: center; margin-top: 40px;">No elements marked yet.</div>`;
                return;
            }

            annotations.forEach(a => {
                const item = document.createElement('div');
                item.className = 'feedback-item';
                item.style.borderLeft = a.type === 'KEEP' ? '4px solid #2ed573' : '4px solid #ff4757';
                
                const label = document.createElement('span');
                label.innerText = a.id;
                
                const tag = document.createElement('span');
                tag.className = 'feedback-tag ' + (a.type === 'KEEP' ? 'keep' : 'redesign');
                tag.innerText = a.type;

                item.appendChild(label);
                item.appendChild(tag);
                list.appendChild(item);
            });
            
            updatePromptBox();
        }

        function updatePromptBox() {
            const box = document.getElementById('prompt-box');
            const deletes = annotations.filter(a => a.type === 'DELETE').map(a => a.id);
            const keeps = annotations.filter(a => a.type === 'KEEP').map(a => a.id);
            
            let promptText = `### SPATIAL FEEDBACK COMPILED\\n\\n`;
            if (keeps.length > 0) {
                promptText += `✓ RETAIN:\\n`;
                keeps.forEach(k => promptText += `  - Keep function: #${k}\\n`);
            }
            if (deletes.length > 0) {
                promptText += `\\n✗ DELETE / REDESIGN:\\n`;
                deletes.forEach(d => promptText += `  - Delete button: #${d}\\n`);
            }
            box.innerText = promptText;
        }

        function promoteAlt(altSrc, optName) {
            const activeFrame = document.getElementById('active-frame');
            activeFrame.src = altSrc.split('?')[0] + '?active=true';
            
            addChatLog('system', `🌟 Promoted <strong>${optName}</strong> to Active Workspace.`);
        }

        function submitEcosystemFeedback() {
            if (annotations.length === 0) {
                alert('Please annotate elements first (Left click to keep, Right click to delete).');
                return;
            }
            addChatLog('system', '🚀 Refactored capsule dispatched to LLM pipeline!');
            alert('🚀 Prompt dispatched to Nexu LLM Pipeline: Redrawing calculator with requested buttons deleted!');
        }
    </script>
</body>
</html>"""

    player_path.write_text(player_html, encoding="utf-8")
    
    # Automatically open in browser tab using a robust fallback chain for Linux
    try:
        url = f"file://{player_path.absolute()}"
        opened_via_system = False
        import subprocess
        for cmd in [['xdg-open', str(player_path.absolute())],
                    ['sensible-browser', url],
                    ['firefox', url],
                    ['google-chrome', url]]:
            try:
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                opened_via_system = True
                break
            except Exception:
                continue
        
        if not opened_via_system:
            import webbrowser
            webbrowser.open(url)
    except Exception:
        pass
        
    return player_path
