#!/usr/bin/env python3
"""Production entrypoint: sync cinema assets and run the cinema HTTP server."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def main() -> None:
    workspace = Path(os.environ.get("NEXU_WORKSPACE", "/workspace")).resolve()
    capsule = os.environ.get("NEXU_CAPSULE", "nexu").strip() or "nexu"
    port = int(os.environ.get("CINEMA_PORT", "8080"))
    bind_host = os.environ.get("CINEMA_BIND_HOST", "0.0.0.0")

    os.environ.setdefault("CINEMA_BIND_HOST", bind_host)

    from nexu.cinema import sync_cinema_templates
    from nexu.cinema_policy import cinema_dir_for
    from nexu.cinema_server import _render_server_script, _litellm_available
    from nexu.config import load_config, load_env_files

    if not workspace.is_dir():
        raise SystemExit(f"NEXU_WORKSPACE is not a directory: {workspace}")

    load_env_files(workspace)
    config = load_config(workspace)

    if not _litellm_available(sys.executable):
        raise SystemExit("litellm is required for cinema server (install nexu with dependencies)")

    cinema_dir = cinema_dir_for(workspace, capsule)
    cinema_dir.mkdir(parents=True, exist_ok=True)
    sync_cinema_templates(cinema_dir, workspace, capsule)

    script = _render_server_script(
        workspace,
        capsule,
        config.llm,
        config.cinema,
        sys.executable,
    )
    server_py = cinema_dir / "server.py"
    server_py.write_text(script, encoding="utf-8")
    server_py.chmod(0o755)

    os.chdir(cinema_dir)
    os.execv(sys.executable, [sys.executable, str(server_py), str(port)])


if __name__ == "__main__":
    main()
