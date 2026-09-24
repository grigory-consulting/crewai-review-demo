"""Review-Kommentar auf einen echten Pull Request stellen (GitHub REST, nur mit Token)."""
import os

import httpx

# Verdict der Pipeline -> Ereignistyp der GitHub-API
# Kein Auto-Approve: "approve" wird als COMMENT gepostet, die Freigabe bleibt beim Menschen.
EVENT_FOR_VERDICT = {"approve": "COMMENT", "request_changes": "REQUEST_CHANGES", "comment": "COMMENT"}


def post_review(repo: str, pr_number: int, verdict: str, body: str, token: str | None = None) -> dict:
    """POST /repos/{repo}/pulls/{n}/reviews. Ohne Token wird nichts gesendet (RuntimeError).

    Benötigter Token-Scope (fine-grained): Pull requests: Read and write auf dem Zielrepo.
    """
    token = token or os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN fehlt: es wird nichts gesendet.")
    r = httpx.post(
        f"https://api.github.com/repos/{repo}/pulls/{pr_number}/reviews",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
                 "X-GitHub-Api-Version": "2022-11-28"},
        json={"event": EVENT_FOR_VERDICT[verdict], "body": body},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()
