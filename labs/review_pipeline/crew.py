"""Crews der Pipeline: eine Reviewer-Crew je Fokus und die Merge-Crew des Lead Reviewers."""
import json

from crewai import LLM, Crew, Process, Task

from .agents import make_lead, make_reviewer
from .models import MergedReview, ReviewResult
from .tools import make_findings_guardrail, wrap_diff_as_data

# Worauf der jeweilige Reviewer achten soll (kommt in die Task-Beschreibung, nicht in die Rolle).
FOCUS_INSTRUCTIONS: dict[str, str] = {
    "correctness": "logic errors: boundaries (>, >=), off-by-one, missing rounding of money amounts, "
                   "unhandled cases, contradictions to the documented rules in README changes",
    "security": "security weaknesses: shell commands built from user input (os.system, subprocess with "
                "shell=True), path traversal, injection, secrets, unsafe file handling",
    "style_tests": "missing tests for new or changed functions, readability, naming, docstrings, duplication",
}

SEVERITY_GUIDE = (
    "Severity: critical = security hole or wrong money calculation reaching customers; major = bug with "
    "user-visible impact; minor = quality issue without functional impact; info = remark. "
    "Category: correctness, security, style or tests."
)


def review_task(agent, diff: str, changed_files: list[str], focus: str, wrap: bool = True) -> Task:
    """Task für einen Reviewer. `wrap=False` nur für die Injection-Demo (Diff ungeschützt)."""
    diff_block = wrap_diff_as_data(diff) if wrap else diff
    return Task(
        description=(
            f"Review the pull request diff below. Changed files: {changed_files}.\n"
            f"Look only for {FOCUS_INSTRUCTIONS[focus]}. Report only findings you can point to in the diff, "
            "with the file path exactly as listed and the line number in the new version of the file "
            f"(null if unknown). {SEVERITY_GUIDE} Give a concrete suggestion or null. Write message, suggestion "
            "and summary in German, at most two sentences each. Do not report issues outside your focus. If you "
            "find nothing, return an empty findings list and say so in the summary.\n\n"
            f"{diff_block}"
        ),
        expected_output="A JSON object with fields `findings` (list of file, line, severity, category, "
                        "message, suggestion) and `summary` (one or two sentences).",
        agent=agent,
        output_pydantic=ReviewResult,
        guardrail=make_findings_guardrail(changed_files),
        guardrail_max_retries=2,
    )


def review_crew(llm: LLM, diff: str, changed_files: list[str], focus: str, wrap: bool = True,
                verbose: bool = False) -> Crew:
    """Ein-Agent-Crew für einen Fokus; Ergebnis in `crew.kickoff().pydantic` als ReviewResult."""
    agent = make_reviewer(llm, focus, verbose)
    task = review_task(agent, diff, changed_files, focus, wrap)
    return Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=verbose)


def merge_task(lead, reviews: dict[str, ReviewResult]) -> Task:
    """Task des Lead Reviewers: deduplizieren, nach Schwere ordnen, Verdict fällen."""
    payload = json.dumps({k: v.model_dump() for k, v in reviews.items()}, indent=1, ensure_ascii=False)
    return Task(
        description=(
            "Merge the partial reviews below into one final review.\n"
            "Rules: (1) Findings with the same file and category that describe the same problem (same or "
            "neighbouring line) are duplicates: keep one entry with the higher severity and the more precise "
            "message. (2) Order findings by severity: critical, "
            "major, minor, info. (3) Verdict: `request_changes` if any finding is critical or major; "
            "`comment` if there are only minor or info findings; `approve` if there are no findings. "
            "(4) Summary: two or three sentences in German for the author, most important issue first. "
            "Do not invent findings and do not drop findings that are not duplicates.\n\n"
            f"Partial reviews (JSON, keyed by reviewer focus):\n{payload}"
        ),
        expected_output="A JSON object with `findings` (deduplicated, ordered), `summary` and `verdict`.",
        agent=lead,
        output_pydantic=MergedReview,
    )


def merge_crew(llm: LLM, reviews: dict[str, ReviewResult], verbose: bool = False) -> Crew:
    """Ein-Agent-Crew des Lead Reviewers; Ergebnis in `.pydantic` als MergedReview."""
    lead = make_lead(llm, verbose)
    return Crew(agents=[lead], tasks=[merge_task(lead, reviews)], process=Process.sequential, verbose=verbose)
