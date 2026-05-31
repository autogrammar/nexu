from __future__ import annotations

import subprocess
import sys
from importlib.resources import files
from pathlib import Path
from socket import AF_INET, SOCK_STREAM, socket
from string import Template

from .config import load_config, load_env_files

_SERVER_TEMPLATE = "templates/cinema/server.py.tmpl"


def _template_text() -> str:
    return files("nexu").joinpath(_SERVER_TEMPLATE).read_text(encoding="utf-8")


def _render_server_script(
    root: Path,
    name: str,
    llm_config: object,
    cinema_config: object,
    python_executable: str,
) -> str:
    return Template(_template_text()).substitute(
        WORKSPACE_PATH=repr(str(root.absolute())),
        CAPSULE_NAME=repr(name),
        PYTHON_EXECUTABLE_RAW=python_executable,
        PYTHON_EXECUTABLE=repr(python_executable),
        ALLOW_NETWORK_CALLS=repr(llm_config.allow_network_calls),
        API_KEY_ENV=repr(llm_config.api_key_env),
        DEFAULT_MODEL=repr(llm_config.model),
        CINEMA_MARKPACT_CONTEXT_CHARS=repr(int(cinema_config.markpact_context_chars)),
        CINEMA_MARKPACT_CONTEXT_MODE=repr(str(cinema_config.markpact_context_mode)),
        CINEMA_HTML_CONTEXT_CHARS=repr(int(cinema_config.html_context_chars)),
        CINEMA_MAX_TOKENS=repr(int(cinema_config.max_tokens)),
        CINEMA_OPTION_GENERATION_MODE=repr(str(cinema_config.option_generation_mode)),
        CINEMA_LLM_TRACE_KEEP=repr(int(cinema_config.llm_trace_keep)),
    )


def _litellm_available(python_executable: str) -> bool:
    return (
        subprocess.run(
            [python_executable, "-c", "import litellm"],
            capture_output=True,
        ).returncode
        == 0
    )


def _try_spawn_on_port(directory: Path, port: int, python_executable: str) -> bool:
    with socket(AF_INET, SOCK_STREAM) as probe:
        try:
            probe.bind(("127.0.0.1", port))
        except OSError:
            return False

    subprocess.Popen(
        [python_executable, str(directory / "server.py"), str(port)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    return True


def _available_port(directory: Path, python_executable: str) -> int:
    for port in range(8080, 8095):
        if _try_spawn_on_port(directory, port, python_executable):
            return port

    with socket(AF_INET, SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        fallback_port = int(probe.getsockname()[1])

    if _try_spawn_on_port(directory, fallback_port, python_executable):
        return fallback_port

    raise RuntimeError("Unable to start cinema HTTP server: no free local port available")


def start_persistent_http_server(directory: Path, root: Path, name: str) -> int:
    """Start a persistent custom background HTTP server for Cinema."""
    load_env_files(root)
    config = load_config(root)

    if not _litellm_available(sys.executable):
        raise RuntimeError(
            "Cinema live iteration requires litellm. From the nexu repo run: uv sync"
        )

    server_script = _render_server_script(
        root,
        name,
        config.llm,
        config.cinema,
        sys.executable,
    )
    (directory / "server.py").write_text(server_script, encoding="utf-8")
    return _available_port(directory, sys.executable)


def _open_browser(url: str) -> None:
    for command in (
        ["xdg-open", url],
        ["sensible-browser", url],
        ["firefox", url],
        ["google-chrome", url],
    ):
        try:
            subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return
        except Exception:
            continue

    import webbrowser

    webbrowser.open(url)


def start_cinema_player_server(
    cinema_dir: Path,
    root: Path,
    name: str,
    *,
    open_browser: bool = True,
) -> str:
    from .cinema import sync_cinema_templates

    sync_cinema_templates(cinema_dir, root, name)
    port = start_persistent_http_server(cinema_dir, root, name)
    url = f"http://127.0.0.1:{port}/cinema_player.html"
    print(f"🎬 Live HTTP Server started for Nexu: {url}")

    if open_browser:
        _open_browser(url)

    return url
