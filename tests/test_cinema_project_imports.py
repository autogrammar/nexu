import base64
import zipfile
from pathlib import Path

from nexu.cinema_project_imports import import_zip_project, list_imported_projects


def test_import_zip_project_creates_markpact_migration_and_options(tmp_path: Path):
    archive = tmp_path / "demo.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("demo/package.json", '{"scripts":{"dev":"vite"}}')
        zf.writestr("demo/src/App.jsx", "export default function App(){return <h1>Demo</h1>}")

    cinema = tmp_path / "cinema"
    cinema.mkdir()
    payload = base64.b64encode(archive.read_bytes()).decode("ascii")

    result = import_zip_project(cinema, "demo.zip", payload)

    assert result["status"] == "project_imported"
    assert result["project"]["kind"] == "imported"
    assert "markpact_path" in result["project"]
    markpact = Path(result["project"]["markpact_path"])
    assert markpact.exists()
    text = markpact.read_text(encoding="utf-8")
    assert "markpact:file path=nexu-import-meta.json" in text
    assert "markpact:run" in text
    assert "src/App.jsx" in text
    assert "Markpact migration" in (cinema / "stage0.html").read_text(encoding="utf-8")
    assert "Markpact migration" in (cinema / "alt_a.html").read_text(encoding="utf-8")

    catalog = list_imported_projects(cinema)
    assert catalog[0]["id"] == result["project"]["id"]
    assert catalog[0]["kind"] == "imported"
