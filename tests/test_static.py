"""Static guarantees that are cheap to check and expensive to regress."""

from __future__ import annotations

import ast
import pathlib
import unittest

PACKAGE = pathlib.Path(__file__).resolve().parent.parent / "dgknlabs"
FORBIDDEN_PREFIXES = (
    "socket",
    "http",
    "urllib",
    "requests",
    "ftplib",
    "smtplib",
    "telnetlib",
    "asyncio",
    "aiohttp",
    "webbrowser",
)


class StaticGuarantees(unittest.TestCase):
    def _module_imports(self) -> dict[str, set[str]]:
        imports: dict[str, set[str]] = {}
        for path in sorted(PACKAGE.glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            names: set[str] = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    names.update(alias.name for alias in node.names)
                elif (
                    isinstance(node, ast.ImportFrom)
                    and node.module
                    and node.level == 0
                ):
                    names.add(node.module)
            imports[path.name] = names
        return imports

    def test_no_network_modules_are_imported(self) -> None:
        for module, imports in self._module_imports().items():
            for name in imports:
                for prefix in FORBIDDEN_PREFIXES:
                    self.assertFalse(
                        name == prefix or name.startswith(prefix + "."),
                        f"{module} importiert Netzwerkmodul {name}",
                    )

    def test_no_file_io_in_runtime_package(self) -> None:
        for path in sorted(PACKAGE.glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    self.assertNotEqual(
                        node.func.id, "open",
                        f"{path.name} öffnet Dateien im Laufzeitcode",
                    )

    def test_package_has_no_third_party_imports(self) -> None:
        allowed = {
            "__future__", "ctypes", "math", "os", "re", "secrets", "string",
            "sys", "tkinter", "traceback", "typing", "dataclasses",
        }
        for module, imports in self._module_imports().items():
            for name in imports:
                root = name.split(".")[0]
                if root in {"dgknlabs"}:
                    continue
                self.assertIn(root, allowed,
                              f"{module} importiert Abhängigkeit {name}")

    def test_readme_documents_security_limits(self) -> None:
        readme = (PACKAGE.parent / "README.md").read_text(encoding="utf-8")
        for keyword in ("Offline", "Entropie", "Zwischenablage", "Lizenz"):
            self.assertIn(keyword, readme)


if __name__ == "__main__":
    unittest.main(verbosity=2)
