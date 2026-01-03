"""Tests ensuring API layer does not call providers directly."""

from __future__ import annotations

import ast
from pathlib import Path


def _find_provider_imports(module_path: Path) -> list[str]:
    contents = module_path.read_text(encoding="utf-8")
    tree = ast.parse(contents, filename=str(module_path))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "app.providers" or alias.name.startswith("app.providers."):
                    imports.append(alias.name)
        if isinstance(node, ast.ImportFrom):
            if node.module and (
                node.module == "app.providers" or node.module.startswith("app.providers.")
            ):
                imports.append(node.module)
    return imports


def test_api_routes_do_not_import_providers_directly() -> None:
    api_dir = Path("app/api")
    provider_imports: dict[str, list[str]] = {}
    for module_path in api_dir.glob("*.py"):
        found = _find_provider_imports(module_path)
        if found:
            provider_imports[str(module_path)] = found

    assert provider_imports == {}, f"Direct provider imports found: {provider_imports}"
