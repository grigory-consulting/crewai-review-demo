"""Der Flow: deterministischer Rahmen um die autonomen Crews.

fetch_context -> run_reviews (3 Crews parallel) -> merge (Lead) -> Freigabe durch Menschen
-> publish (Markdown-Datei, optional GitHub) oder discard.
"""
import asyncio
import os
import re
from pathlib import Path

from crewai.flow.flow import Flow, listen, start
from crewai.flow.human_feedback import human_feedback

from .agents import make_llm
from .context import fetch_context_direct, fetch_context_with_agent
from .crew import merge_crew, review_crew
from .github import post_review
from .models import ReviewState
from .render import to_markdown
from .tools import LABS_DIR, ensure_repo

# Schalter: Kontext über den MCP-Server (True) oder direkt über git-Funktionen (False).
USE_MCP = os.environ.get("USE_MCP", "1") not in ("0", "false", "False")
# Schalter: Freigabe-Gate überspringen (nbconvert, CI, --no-human). Sonst entscheidet ein Mensch; Default ist rejected.
NO_HUMAN = os.environ.get("REVIEW_NO_HUMAN", "0") in ("1", "true", "True")
OUTPUT_DIR = LABS_DIR / "output"
FOCI = ("correctness", "security", "style_tests")
_HITL_LLM = make_llm()  # nur nötig, wenn der Mensch Freitext tippt (wird dann auf approved/rejected abgebildet)


class ReviewFeedbackProvider:
    """Freigabe von der Konsole. Mit `no_human` (Flag oder REVIEW_NO_HUMAN=1) wird das Gate übersprungen
    und der Flow läuft wie nach 'approved' weiter. Ohne stdin (nbconvert, CI) zählt der Default: rejected."""

    def request_feedback(self, context, flow) -> str:
        if getattr(flow, "no_human", False):
            print("[Freigabe-Gate übersprungen (no_human): weiter wie 'approved']")
            return "approved"
        print(context.method_output, "\n", context.message)
        try:
            return input("Ihr Feedback (Enter = ablehnen, 'ok' = freigeben): ").strip()
        except Exception:  # kein stdin: EOFError, StdinNotImplementedError im Kernel
            return ""


class CodeReviewFlow(Flow[ReviewState]):
    """Inputs per kickoff(inputs={"repo_dir", "base", "head", "pr_number"})."""

    def __init__(self, llm=None, use_mcp: bool | None = None, no_human: bool | None = None,
                 wrap_diff: bool = True, verbose: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.llm = llm or make_llm()
        self.use_mcp = USE_MCP if use_mcp is None else use_mcp
        self.no_human = NO_HUMAN if no_human is None else no_human  # True = Gate überspringen (wie approved)
        self.wrap_diff = wrap_diff
        self.verbose = verbose

    def _collapse_to_outcome(self, feedback: str, outcomes, llm) -> str:
        """Exakte Antworten ('approved', 'rejected') ohne LLM abbilden; nur Freitext geht ans Modell."""
        if feedback.strip().lower() in outcomes:
            return feedback.strip().lower()
        return super()._collapse_to_outcome(feedback, outcomes, llm)

    @start()
    def fetch_context(self):
        s = self.state
        s.repo_dir = str(ensure_repo(Path(s.repo_dir) if s.repo_dir else None))
        if self.use_mcp:
            ctx = fetch_context_with_agent(self.llm, s.repo_dir, s.base, s.head, use_mcp=True, verbose=self.verbose)
        else:
            ctx = fetch_context_direct(s.repo_dir, s.base, s.head)
        s.changed_files, s.diff = ctx.changed_files, ctx.diff
        if not s.diff.strip():
            raise ValueError(f"Kein Diff zwischen {s.base} und {s.head}.")
        return s.changed_files

    @listen(fetch_context)
    async def run_reviews(self, _):
        s = self.state
        crews = {f: review_crew(self.llm, s.diff, s.changed_files, f, wrap=self.wrap_diff, verbose=self.verbose)
                 for f in FOCI}
        outputs = await asyncio.gather(*(c.kickoff_async() for c in crews.values()))
        s.reviews = {f: out.pydantic for f, out in zip(crews, outputs)}
        return {f: len(r.findings) for f, r in s.reviews.items()}

    @listen(run_reviews)
    @human_feedback(message="Review freigeben? 'ok'/'approved' = freigeben; Enter oder 'nein' = ablehnen (sicherer Default).",
                    emit=["approved", "rejected"], llm=_HITL_LLM, default_outcome="rejected",
                    provider=ReviewFeedbackProvider())
    def merge(self, _):
        self.state.merged = merge_crew(self.llm, self.state.reviews, verbose=self.verbose).kickoff().pydantic
        return to_markdown(self.state.merged)  # das sieht der Mensch im Freigabeschritt

    @listen("approved")
    def publish(self, result):
        s = self.state
        OUTPUT_DIR.mkdir(exist_ok=True)
        out = OUTPUT_DIR / f"review_{re.sub(r'[^A-Za-z0-9_.-]+', '_', s.head)}.md"
        out.write_text(to_markdown(s.merged), encoding="utf-8")
        repo = os.environ.get("GITHUB_REPO")
        if os.environ.get("GITHUB_TOKEN") and repo and s.pr_number:
            post_review(repo, s.pr_number, s.merged.verdict, to_markdown(s.merged))
            s.posted = True
        return str(out)

    @listen("rejected")
    def discard(self, result):
        print(f"Review verworfen. Begründung: {result.feedback or '(keine)'}")
        return None
