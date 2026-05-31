#!/usr/bin/env python3
"""
Nexu Pactown Ecosystem Runner
Loads and launches the composed api and web services under Pactown.
"""

import os
import sys
import time
import subprocess
from pathlib import Path

DIR = Path(__file__).resolve().parent

def main():
    print("=== Step 1: Validating Pactown Configuration ===")
    yaml_path = DIR / "pactown.yaml"
    
    if not yaml_path.exists():
        print(f"Error: {yaml_path} does not exist.")
        sys.exit(1)
        
    print(f"Found ecosystem config: {yaml_path}")
    
    print("\n=== Step 2: Starting Pactown Ecosystem ===")
    # Run pactown up in the background
    cmd = f"uv run pactown up {yaml_path}"
    print(f"Executing: {cmd}")
    
    # We start it as a background process so we can query health checks!
    proc = subprocess.Popen(
        cmd,
        shell=True,
        cwd=DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for the services to bootstrap their .venv and start
    print("Bootstrapping sandboxes and installing packages...")
    import socket
    
    max_wait = 45
    ready = False
    for i in range(max_wait):
        time.sleep(1)
        # Check if ports 9001 and 9002 are open
        try:
            with socket.create_connection(("127.0.0.1", 9001), timeout=0.5):
                with socket.create_connection(("127.0.0.1", 9002), timeout=0.5):
                    print(f"Both services started in {i+1} seconds!")
                    ready = True
                    break
        except OSError:
            if (i + 1) % 5 == 0:
                print(f"Waiting for services to boot ({i+1}/{max_wait}s)...")
                
    if not ready:
        print("Warning: Services did not start in time. Querying health anyway...")
    
    print("\n=== Step 3: Querying Service Discovery and Health Checks ===")
    import requests
    
    try:
        # Check API health
        api_res = requests.get("http://localhost:9001/health", timeout=2).json()
        print(f"API Backend Health: {api_res}")
        
        # Check Web UI health/response
        web_res = requests.get("http://localhost:9002/", timeout=2).text
        print("\nWeb Frontend Response Surface Preview:")
        print("-" * 50)
        print("\n".join(web_res.strip().splitlines()[-10:])) # print trailing HTML
        print("-" * 50)
        
        print("\n=== [SUCCESS] Pactown Ecosystem Composed successfully! ===")
    except Exception as e:
        print(f"\nConnection error: {e}")
        print("Pactown startup logs:")
        # Read any stdout
        try:
            out, err = proc.communicate(timeout=2)
            print(out)
            print(err)
        except Exception:
            pass
    finally:
        print("\n=== Step 4: Shutting down Ecosystem cleanly ===")
        proc.terminate()
        proc.wait()
        # Clean down services
        subprocess.run(f"uv run pactown down {yaml_path}", shell=True, cwd=DIR)
        print("All processes stopped.")

if __name__ == "__main__":
    main()
