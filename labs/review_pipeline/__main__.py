"""Pipeline als Skript: python -m review_pipeline --head feature/rabatt-staffel [--pr 3] [--no-mcp] [--no-human]"""
import argparse
import os

from .flow import CodeReviewFlow


def main() -> None:
    p = argparse.ArgumentParser(description="CrewAI Code-Review-Pipeline")
    p.add_argument("--repo-dir", default=os.environ.get("REVIEW_REPO_DIR", ""), help="Git-Repository (Default: labs/demo-repo-local)")
    p.add_argument("--base", default="main")
    p.add_argument("--head", required=True, help="Branch oder Commit mit den Änderungen")
    p.add_argument("--pr", type=int, default=None, help="PR-Nummer; mit GITHUB_TOKEN und GITHUB_REPO wird der Review gepostet")
    p.add_argument("--no-mcp", action="store_true", help="Kontext direkt über git statt über den MCP-Server holen")
    p.add_argument("--no-human", action="store_true", help="Freigabe-Gate überspringen, weiter wie approved (sonst Konsole; Default rejected)")
    p.add_argument("--no-wrap", action="store_true", help="Diff ohne Schutzbegrenzer übergeben (nur für die Injection-Demo)")
    p.add_argument("--verbose", action="store_true")
    a = p.parse_args()

    flow = CodeReviewFlow(use_mcp=not a.no_mcp, no_human=a.no_human or None,
                          wrap_diff=not a.no_wrap, verbose=a.verbose)
    flow.kickoff(inputs={"repo_dir": a.repo_dir, "base": a.base, "head": a.head, "pr_number": a.pr})
    s = flow.state
    print(f"\nVerdict: {s.merged.verdict if s.merged else '-'} | Befunde: {len(s.merged.findings) if s.merged else 0} "
          f"| auf GitHub gepostet: {s.posted}")


if __name__ == "__main__":
    main()
