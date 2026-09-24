"""Ersatz-MCP-Server (stdio) mit denselben vier Git-Werkzeugen wie labs/mcp_git_server.py.

Wird nur genutzt, wenn der Server aus Lab 2 fehlt. Repository aus REVIEW_REPO_DIR.
Start: python _fallback_mcp_server.py (der MCP-Host startet ihn als Kindprozess).
"""
import os
import subprocess
from pathlib import Path

from mcp.server.fastmcp import FastMCP

REPO_DIR = Path(os.environ.get("REVIEW_REPO_DIR", Path(__file__).resolve().parent.parent / "demo-repo-local")).resolve()
mcp = FastMCP("git-review", instructions="Lesender Zugriff auf ein lokales Git-Repository.", log_level="WARNING")


def _git(*args: str) -> str:
    """git ausführen; Fehler als Text zurückgeben, damit das Modell sie lesen kann."""
    r = subprocess.run(["git", *args], cwd=REPO_DIR, capture_output=True, text=True, timeout=30)
    return r.stdout if r.returncode == 0 else f"FEHLER (git {' '.join(args)}): {r.stderr.strip()}"


def _ok(*refs: str) -> str | None:
    """Refs und Pfade dürfen nicht wie git-Optionen aussehen oder das Repo verlassen."""
    for r in refs:
        if not r or r.startswith("-") or ".." in Path(r).parts or any(c.isspace() for c in r):
            return f"FEHLER: unzulässiger Wert {r!r}."
    return None


@mcp.tool()
def list_changed_files(base: str, head: str) -> list[str]:
    """Listet die Dateien, die sich auf `head` gegenüber dem gemeinsamen Vorfahren mit `base` geändert haben."""
    if fehler := _ok(base, head):
        return [fehler]
    return [z for z in _git("diff", "--name-only", f"{base}...{head}").splitlines() if z]


@mcp.tool()
def get_diff(base: str, head: str, path: str | None = None) -> str:
    """Liefert den Unified Diff von `base...head`, optional nur für die Datei `path`."""
    if fehler := _ok(base, head, *([path] if path else [])):
        return fehler
    return _git("diff", f"{base}...{head}", *(["--", path] if path else [])) or "(kein Unterschied)"


@mcp.tool()
def get_file(path: str, ref: str = "HEAD") -> str:
    """Liefert den Inhalt der Datei `path` im Stand `ref`."""
    return _ok(path, ref) or _git("show", f"{ref}:{path}")


@mcp.tool()
def get_log(n: int = 10) -> str:
    """Liefert die letzten `n` Commits als Einzeiler."""
    return _git("log", "--all", "--oneline", "--decorate", f"-n{max(1, min(int(n), 100))}")


if __name__ == "__main__":
    mcp.run()
