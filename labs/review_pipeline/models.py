"""Datenmodell der Review-Pipeline.

Alles, was zwischen Agenten, Tasks und Flow-Schritten fließt, ist hier als
Pydantic-Modell festgelegt. Die Modelle dienen dreifach: als Schema für die
strukturierte Modellausgabe (`output_pydantic`), als Prüfgrundlage für den
Guardrail und als Flow-State, den jeder Schritt lesen und schreiben kann.
"""
from typing import Literal

from pydantic import BaseModel, Field

Severity = Literal["critical", "major", "minor", "info"]
Category = Literal["correctness", "security", "style", "tests"]
Verdict = Literal["approve", "request_changes", "comment"]

# Reihenfolge für Sortierung und Verdict-Regel (kleiner = schwerer).
SEVERITY_RANK: dict[str, int] = {"critical": 0, "major": 1, "minor": 2, "info": 3}


class Finding(BaseModel):
    """Ein einzelner Befund mit Datei-/Zeilenbezug."""

    file: str = Field(description="Pfad relativ zur Repo-Wurzel, exakt wie in der Liste der geänderten Dateien")
    line: int | None = Field(default=None, description="Zeilennummer in der neuen Fassung der Datei, sonst null")
    severity: Severity
    category: Category
    message: str = Field(description="Was ist das Problem, konkret und belegbar am Diff")
    suggestion: str | None = Field(default=None, description="Konkreter Vorschlag zur Behebung, sonst null")


class ReviewResult(BaseModel):
    """Ausgabe eines einzelnen Reviewers."""

    findings: list[Finding] = Field(default_factory=list)
    summary: str = Field(description="Ein bis zwei Sätze: Gesamteindruck aus Sicht dieses Reviewers")


class MergedReview(BaseModel):
    """Zusammengeführtes Ergebnis des Lead Reviewers."""

    findings: list[Finding] = Field(default_factory=list)
    summary: str
    verdict: Verdict


class ContextResult(BaseModel):
    """Kontext eines Pull Requests: geänderte Dateien und Diff."""

    changed_files: list[str] = Field(default_factory=list)
    diff: str = ""


class ReviewState(BaseModel):
    """Flow-State: wird per `kickoff(inputs=...)` befüllt und von jedem Schritt fortgeschrieben."""

    repo_dir: str = ""
    base: str = "main"
    head: str = ""
    pr_number: int | None = None
    diff: str = ""
    changed_files: list[str] = Field(default_factory=list)
    reviews: dict[str, ReviewResult] = Field(default_factory=dict)
    merged: MergedReview | None = None
    posted: bool = False
