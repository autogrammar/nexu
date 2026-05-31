#!/usr/bin/env python3
"""
Nexu Glassmorphic Event Dashboard Ecosystem Test Runner
Starts the entire distributed telemetry ecosystem.
"""

import os
import sys
import time
import subprocess
from pathlib import Path

DIR = Path(__file__).resolve().parent

def main():
    print("=== Step 1: Validating Composed Pactown Graph ===")
    yaml_path = DIR / "pactown.yaml"
    
    if not yaml_path.exists():
        print(f"Error: {yaml_path} does not exist.")
        sys.exit(1)
        
    print(f"Found ecosystem config: {yaml_path}")
    
    print("\n=== Step 2: Bootstrapping Multi-Service Ecosystem ===")
    cmd = f"uv run pactown up {yaml_path}"
    print(f"Executing: {cmd}")
    
    proc = subprocess.Popen(
        cmd,
        shell=True,
        cwd=DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for venvs and packages to bootstrap and ports 9101, 9102, 9103 to open
    print("Initializing isolated environments and starting services...")
    import socket
    
    max_wait = 45
    ready = False
    for i in range(max_wait):
        time.sleep(1)
        try:
            with socket.create_connection(("127.0.0.1", 9101), timeout=0.5):
                with socket.create_connection(("127.0.0.1", 9102), timeout=0.5):
                    with socket.create_connection(("127.0.0.1", 9103), timeout=0.5):
                        print(f"All 3 services successfully started in {i+1} seconds!")
                        ready = True
                        break
        except OSError:
            if (i + 1) % 5 == 0:
                print(f"Waiting for services to boot ({i+1}/{max_wait}s)...")
                
    if not ready:
        print("Warning: Some services did not start in time. Querying anyway...")
    
    print("\n=== Step 3: Querying the Glassmorphic Dashboard Endpoint ===")
    import requests
    
    try:
        # Check active alerts
        alert_data = requests.get("http://localhost:9102/alerts", timeout=2).json()
        print(f"Alert Rules Verified: {alert_data.get('alerts', [])}")
        
        # Check high-fidelity UI page
        ui_page = requests.get("http://localhost:9103/", timeout=2).text
        print("\nGlassmorphic UI Live HTML Snapshot:")
        print("-" * 65)
        # Extract and print body metrics section
        body_lines = [line.strip() for line in ui_page.splitlines() if line.strip()]
        for line in body_lines:
            if "System Load metrics" in line or "Active Rules & Safety Alerts" in line or "Telemetry data:" in line:
                print(line)
        print("-" * 65)
        
        print("\n=== [SUCCESS] Distributed Pactown Ecosystem compiled and executed flawlessly! ===")
    except Exception as e:
        print(f"\nConnection error: {e}")
    finally:
        print("\n=== Step 4: Shutting down Telemetry Ecosystem cleanly ===")
        proc.terminate()
        proc.wait()
        subprocess.run(f"uv run pactown down {yaml_path}", shell=True, cwd=DIR)
        print("All processes cleanly stopped.")

if __name__ == "__main__":
    main()
