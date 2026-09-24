"""MCP-Server (stdio), der lesende Git-Operationen als Werkzeuge bereitstellt.

Der Server läuft als Kindprozess des MCP-Hosts (Lab 2: erst das MCP-Client-SDK,
dann ein CrewAI-Agent) und spricht über stdin/stdout JSON-RPC. Das Repository,
auf dem gearbeitet wird, kommt aus der Umgebungsvariable REVIEW_REPO_DIR
(Default: labs/demo-repo-local neben dieser Datei).

Regeln, die hier bewusst vorgeführt werden:
- Jede Funktion mit @mcp.tool() wird ein Werkzeug; Docstring = Beschreibung,
  Typannotationen = JSON-Schema der Parameter. Beides sieht das Modell.
- Fehler kommen als Text zurück, nicht als Exception: das Modell soll lesen,
  was schiefging, statt dass der Agentenlauf abbricht.
- Eingaben werden geprüft (kein "..", keine absoluten Pfade, keine Refs, die
  wie git-Optionen aussehen), weil Werkzeugparameter vom Modell stammen.
"""
import os
import subprocess
from pathlib import Path

from mcp.server.fastmcp import FastMCP

REPO_DIR = Path(os.environ.get("REVIEW_REPO_DIR", Path(__file__).resolve().parent / "demo-repo-local")).resolve()
MAX_DIFF_CHARS = 20_000

mcp = FastMCP("git-review", instructions="Lesender Zugriff auf ein lokales Git-Repository für Code-Reviews.", log_level="WARNING")


def _git(*args: str) -> str:
    """Führt `git <args>` im Repository aus. Liefert stdout oder eine Fehlermeldung als Text."""
    if not (REPO_DIR / ".git").exists():
        return f"FEHLER: {REPO_DIR} ist kein Git-Repository (REVIEW_REPO_DIR prüfen)."
    try:
        r = subprocess.run(["git", *args], cwd=REPO_DIR, capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired) as e:
        return f"FEHLER: git konnte nicht ausgeführt werden: {e}"
    if r.returncode != 0:
        return f"FEHLER (git {' '.join(args)}): {r.stderr.strip()}"
    return r.stdout


def _pruefe_pfad(path: str) -> str | None:
    """Liefert eine Fehlermeldung, wenn der Pfad das Repository verlassen könnte."""
    if not path or path.startswith(("/", "-")) or ".." in Path(path).parts:
        return f"FEHLER: unzulässiger Pfad {path!r} (nur relative Pfade innerhalb des Repos)."
    return None


def _pruefe_ref(ref: str) -> str | None:
    """Refs dürfen nicht wie git-Optionen aussehen (z. B. '--output=...')."""
    if not ref or ref.startswith("-") or any(c.isspace() for c in ref):
        return f"FEHLER: unzulässige Referenz {ref!r}."
    return None


@mcp.tool()
def list_changed_files(base: str, head: str) -> str:
    """Listet die Dateien, die sich auf `head` gegenüber dem gemeinsamen Vorfahren mit `base` geändert haben (wie ein Pull Request), eine Datei je Zeile."""
    for ref in (base, head):
        if fehler := _pruefe_ref(ref):
            return fehler
    # Bewusst ein String statt list[str]: CrewAI 1.15 reicht nur content[0] eines Werkzeugergebnisses
    # an das Modell durch; bei einer Liste käme nur die erste Datei an.
    out = _git("diff", "--name-only", f"{base}...{head}")
    return out.strip() or f"(keine geänderten Dateien: {head} gegenüber {base})"


@mcp.tool()
def get_diff(base: str, head: str, path: str | None = None) -> str:
    """Liefert den Unified Diff von `base...head`, optional nur für eine Datei `path`. Lange Diffs werden gekürzt."""
    for ref in (base, head):
        if fehler := _pruefe_ref(ref):
            return fehler
    args = ["diff", f"{base}...{head}"]
    if path and path.strip().lower() not in ("null", "none"):  # manche Modelle senden "null" als Text
        if fehler := _pruefe_pfad(path):
            return fehler
        args += ["--", path]
    out = _git(*args)
    if len(out) > MAX_DIFF_CHARS:
        out = out[:MAX_DIFF_CHARS] + f"\n[... gekürzt: Diff hatte {len(out)} Zeichen, Limit {MAX_DIFF_CHARS}]"
    return out or f"(kein Unterschied: {head} enthält keine Änderungen gegenüber {base}; sind base und head vertauscht?)"


@mcp.tool()
def get_file(path: str, ref: str = "HEAD") -> str:
    """Liefert den vollständigen Inhalt der Datei `path` im Stand `ref` (Branch, Tag oder Commit)."""
    if fehler := _pruefe_pfad(path) or _pruefe_ref(ref):
        return fehler
    return _git("show", f"{ref}:{path}")


@mcp.tool()
def get_log(n: int = 10) -> str:
    """Liefert die letzten `n` Commits aller Branches als Einzeiler (Hash, Branch-Markierung, Betreff)."""
    n = max(1, min(int(n), 100))
    return _git("log", "--all", "--oneline", "--decorate", f"-n{n}")


@mcp.resource("repo://info")
def repo_info() -> str:
    """Resource statt Tool: statischer Kontext (Branch, letzter Commit), den der Host lesen kann, ohne dass das Modell ein Werkzeug aufruft."""
    branch = _git("rev-parse", "--abbrev-ref", "HEAD").strip()
    letzter = _git("log", "-1", "--format=%h %an %ad: %s", "--date=short").strip()
    return f"Repository: {REPO_DIR}\nBranch: {branch}\nLetzter Commit: {letzter}"


if __name__ == "__main__":
    mcp.run()  # Transport stdio: der Host startet diesen Prozess und spricht über stdin/stdout
