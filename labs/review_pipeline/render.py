"""Rendert ein MergedReview als Markdown (Datei, Kommentar auf GitHub, Anzeige im Freigabeschritt)."""
from .models import SEVERITY_RANK, MergedReview

VERDICT_LABEL = {"approve": "Approve", "request_changes": "Request changes", "comment": "Comment"}


def _cell(text: str | None) -> str:
    """Zellinhalt tabellentauglich machen: Pipes maskieren, Zeilenumbrüche entfernen."""
    return (text or "").replace("|", "\\|").replace("\n", " ").strip() or "-"


def to_markdown(merged: MergedReview) -> str:
    """Tabelle der Befunde, dann Zusammenfassung und Verdict."""
    lines = ["## Automatisches Code-Review", "", "| Datei | Zeile | Schwere | Kategorie | Befund | Vorschlag |",
             "|---|---|---|---|---|---|"]
    findings = sorted(merged.findings, key=lambda f: (SEVERITY_RANK.get(f.severity, 9), f.file, f.line or 0))
    for f in findings:
        lines.append(f"| `{_cell(f.file)}` | {f.line if f.line is not None else '-'} | {f.severity} | "
                     f"{f.category} | {_cell(f.message)} | {_cell(f.suggestion)} |")
    if not findings:
        lines.append("| - | - | - | - | keine Befunde | - |")
    lines += ["", "**Zusammenfassung:** " + merged.summary.strip(), "",
              f"**Verdict:** {VERDICT_LABEL.get(merged.verdict, merged.verdict)} (`{merged.verdict}`)", ""]
    return "\n".join(lines)
