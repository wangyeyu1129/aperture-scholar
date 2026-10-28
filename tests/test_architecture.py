import ast
from pathlib import Path


def test_dependency_direction():
    root = Path(__file__).resolve().parents[1] / "src" / "aperture_scholar"
    for layer in ("domain", "application"):
        for path in (root / layer).glob("*.py"):
            for node in ast.walk(ast.parse(path.read_text())):
                modules = []
                if isinstance(node, ast.Import):
                    modules = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom):
                    modules = [node.module or ""]
                for module in modules:
                    assert not module.startswith(
                        (
                            "httpx",
                            "sqlite3",
                            "aperture_scholar.infrastructure",
                            "aperture_scholar.research",
                        )
                    ), path
                    if layer == "domain":
                        assert not module.startswith(
                            ("aperture_scholar.application", "aperture_scholar.config")
                        ), path
