from __future__ import annotations

import json
from pathlib import Path
from .paths import capsule_dir

def start_persistent_http_server(directory: Path, root: Path, name: str) -> int:
    """Starts a persistent custom background HTTP server that logs transactions and runs iterations."""
    import socket
    import subprocess
    import sys
    
    server_script = f"""import http.server
import socketserver
import sys
import json
import csv
import mimetypes
import subprocess
from pathlib import Path
from datetime import datetime

# Force correct MIME types and UTF-8 charsets for clean encoding
mimetypes.add_type("text/html; charset=utf-8", ".html")
mimetypes.add_type("application/javascript; charset=utf-8", ".js")
mimetypes.add_type("text/css; charset=utf-8", ".css")

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
DIRECTORY = Path(__file__).parent.absolute()
LOG_CSV = DIRECTORY / "log.csv"

WORKSPACE_PATH = {repr(str(root.absolute()))}
CAPSULE_NAME = {repr(name)}
SYS_EXE = {repr(sys.executable)}

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIRECTORY), **kwargs)

    def do_POST(self):
        if self.path == '/log':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8', errors='replace'))
                timestamp = datetime.now().isoformat()
                action = data.get('action', 'unknown')
                details = data.get('details', '')
                
                # Append to CSV log using robust UTF-8 encoding
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
                self.wfile.write(json.dumps({{"status": "logged"}}).encode('utf-8'))
                return
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(str(e).encode('utf-8'))
                return
                
        elif self.path == '/iterate':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8', errors='replace'))
                prompt = data.get('prompt', '')
                current_stage = int(data.get('current_stage', 0))
                
                # Formulate spatial evolution goal
                goal = f"Evolution step. Spatial feedback: {{prompt}}"
                
                # Execute nexu capsule iterate command using same executable
                cmd = [
                    SYS_EXE, "-m", "nexu.cli", "capsule", "iterate", CAPSULE_NAME,
                    "--steps", "1",
                    "--goal", goal,
                    "--cinema",
                    "--path", WORKSPACE_PATH
                ]
                
                process = subprocess.run(cmd, capture_output=True, text=True)
                
                # Append iteration trigger to CSV log
                file_exists = LOG_CSV.exists()
                with open(LOG_CSV, mode='a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    if not file_exists:
                        writer.writerow(['timestamp', 'action', 'details'])
                    writer.writerow([datetime.now().isoformat(), 'ITERATION_TRIGGERED', f"Stage: {{current_stage}} | Result: {{process.returncode}}"])
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({{
                    "status": "success",
                    "new_stage": current_stage + 1,
                    "stdout": process.stdout,
                    "stderr": process.stderr
                }}).encode('utf-8'))
                return
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(str(e).encode('utf-8'))
                return
                
        super().do_POST()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(('127.0.0.1', PORT), CustomHTTPRequestHandler) as httpd:
    httpd.serve_forever()
"""
    (directory / "server.py").write_text(server_script, encoding="utf-8")

    # Find a free port in the range 8080-8095
    for port in range(8080, 8095):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('127.0.0.1', port))
                s.close()
                
                cmd = [
                    sys.executable, str(directory / "server.py"), str(port)
                ]
                # Spawn a completely detached process
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
                return port
            except OSError:
                continue
    return 8080

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
    
    # Combined marquee bounding box selection script to inject into every child iframe
    shield_script = """
    <script>
        console.log("[NEXU CHILD] IFrame loaded: " + window.location.pathname);

        // Dynamically inject marquee selection styles
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

        // Lazy initialize the selection box element
        function getSelectionBox() {
            if (!selectionBox) {
                selectionBox = document.createElement('div');
                selectionBox.className = 'selection-box';
                document.body.appendChild(selectionBox);
            }
            return selectionBox;
        }

        // Globally block context menu popup
        document.addEventListener('contextmenu', (e) => {
            e.preventDefault();
            e.stopPropagation();
        }, true);

        // Mouse Drag Bounding Box Multi-Selection Engine
        document.addEventListener('mousedown', (e) => {
            const isActiveWorkspace = window.location.search.includes('active=true');
            if (!isActiveWorkspace) return;

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
            const rect = box.getBoundingClientRect(); // Get viewport-relative rect first!
            box.style.display = 'none'; // Hide it after!

            const isSingleClick = rect.width < 8 && rect.height < 8;

            const elements = document.querySelectorAll('.btn, .btn-sci, .btn-sci-excess, .screen');
            elements.forEach(el => {
                const elRect = el.getBoundingClientRect();
                const intersects = !(elRect.right < rect.left || 
                                     elRect.left > rect.right || 
                                     elRect.bottom < rect.top || 
                                     elRect.top > rect.bottom);

                if (intersects || (isSingleClick && el === e.target)) {
                    const elementId = el.innerText.trim() || el.id;
                    window.parent.postMessage({
                        type: 'annotation',
                        elementId: elementId,
                        action: selectionType
                    }, '*');
                }
            });
        });

        // Handle iframe communication for promoting options
        document.addEventListener('click', (e) => {
            const isActiveWorkspace = window.location.search.includes('active=true');
            if (!isActiveWorkspace) {
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
            user-select: none;
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
            user-select: none;
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
            user-select: none;
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
            user-select: none;
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
        .btn-action:disabled { background: #1e293b; color: #64748b; cursor: not-allowed; }
        
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
                    <span style="font-size: 0.65rem;">[🖱️ Left Click & Drag = KEEP | 🖱️ Right Click & Drag = REDESIGN/DELETE]</span>
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
                    Left-click-drag or Right-click-drag directly in Window 1 to annotate multiple elements!
                </div>
            </div>
            
            <div class="side-header">🤖 Evolving Spatial Prompt</div>
            <div class="prompt-box" id="prompt-box">
Click anywhere on Options A-C to instantly promote them to Active Workspace!
            </div>
            
            <button class="btn btn-action" id="action-btn" style="margin-top: 15px; width: 100%;" onclick="runLiveIteration()">
                🚀 Run Live Iteration (DeepSeek)
            </button>
        </div>
    </div>

    <script>
        let activeStage = 0;
        let annotations = [];

        // Integrated logger function (Browser console + Server CSV logger endpoint)
        function logEvent(action, details) {
            console.log(`[NEXU SYSTEM] [${new Date().toISOString()}] Action: ${action} | Details: ${details}`);
            
            fetch('/log', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    action: action,
                    details: details
                })
            }).catch(err => console.error("[NEXU SYSTEM] Logger API unreachable:", err));
        }

        // Log page initialization
        logEvent('PAGE_LOAD', 'Cinema Player dashboard initialized');

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
            logEvent('SWITCH_STAGE', 'Switched Active Workspace stage to S' + stageNum);
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

            logEvent('ANNOTATE', `Element ID: ${elementId} | Type: ${type}`);

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
            logEvent('PROMOTE', `Option: ${optName} | Source: ${altSrc}`);
        }

        function runLiveIteration() {
            const promptBox = document.getElementById('prompt-box');
            const actionBtn = document.getElementById('action-btn');
            
            addChatLog('system', '🤖 <strong>LLM is evolving the code... Running next capsule iteration in background!</strong>');
            logEvent('ITERATION_STARTED', 'Ecosystem feedback iteration submitted to server.');
            
            actionBtn.disabled = true;
            actionBtn.innerText = '⏳ Evolving Code (DeepSeek)...';

            fetch('/iterate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    prompt: promptBox.innerText,
                    current_stage: activeStage
                })
            })
            .then(res => {
                if (!res.ok) throw new Error("Iteration failed");
                return res.json();
            })
            .then(data => {
                actionBtn.disabled = false;
                actionBtn.innerText = '🚀 Run Live Iteration (DeepSeek)';
                
                addChatLog('system', '🎯 <strong>Iteration successful! Evolved stage S' + data.new_stage + ' loaded live in Window 1!</strong>');
                logEvent('ITERATION_COMPLETED_LIVE', 'New evolution stage: S' + data.new_stage);
                
                // Live hot-reload Window 1 frame on the fly to show evolved calculator!
                const activeFrame = document.getElementById('active-frame');
                activeFrame.src = activeFrame.src; // Force fresh iframe reload!
            })
            .catch(err => {
                actionBtn.disabled = false;
                actionBtn.innerText = '🚀 Run Live Iteration (DeepSeek)';
                addChatLog('system', '❌ <strong>Error: Failed to process next live iteration on backend!</strong>');
                console.error(err);
            });
        }
    </script>
</body>
</html>"""

    player_path.write_text(player_html, encoding="utf-8")
    
    # Automatically open in browser tab using a robust fallback chain for Linux via HTTP server
    try:
        port = start_persistent_http_server(cinema_dir, root, name)
        url = f"http://127.0.0.1:{port}/cinema_player.html"
        print(f"🎬 Live HTTP Server started for Cinema Player: {url}")
        
        opened_via_system = False
        import subprocess
        for cmd in [['xdg-open', url],
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
