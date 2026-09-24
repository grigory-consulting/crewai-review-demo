"""Kontext holen: geänderte Dateien und Diff, wahlweise direkt über git oder über einen MCP-Agenten.

Beim Agentenweg ruft ein Agent die Werkzeuge auf (per MCP oder direkt). Die exakten
Werkzeugausgaben greifen wir über den Event-Bus ab, statt sie vom Modell abschreiben zu
lassen: ein Diff, den das Modell "wiedergibt", ist nicht mehr der Diff, und das Abschreiben
kostet mehr Zeit als der ganze Review.
"""
import asyncio
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from crewai import LLM, Crew, Process, Task
from crewai.events.event_bus import crewai_event_bus
from crewai.events.types.mcp_events import MCPToolExecutionCompletedEvent
from crewai.events.types.tool_usage_events import ToolUsageFinishedEvent
from crewai.mcp import MCPServerStdio
from crewai.mcp.filters import create_static_tool_filter

from .agents import make_context_agent
from .models import ContextResult
from .tools import GIT_TOOLS, LABS_DIR, changed_files, diff

# Bevorzugt der Server aus Lab 2, sonst die gleichwertige Fassung aus diesem Paket.
MCP_SERVER = next(p for p in (LABS_DIR / "mcp_git_server.py", Path(__file__).with_name("_fallback_mcp_server.py")) if p.exists())


def kickoff_blocking(crew: Crew):
    """crew.kickoff(), auch aus einer Notebook-Zelle mit laufendem Event-Loop (dann in einem Thread)."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return crew.kickoff()
    with ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(crew.kickoff).result()


def fetch_context_direct(repo_dir: str, base: str, head: str) -> ContextResult:
    """Direkter Weg: zwei git-Aufrufe, kein Modell beteiligt."""
    return ContextResult(changed_files=changed_files(base, head, cwd=repo_dir), diff=diff(base, head, cwd=repo_dir))


def git_mcp_server(repo_dir: str) -> MCPServerStdio:
    """MCP-Server als Kindprozess; Tool-Filter lässt nur die zwei benötigten Werkzeuge durch."""
    return MCPServerStdio(
        command=sys.executable,
        args=[str(MCP_SERVER)],
        env={**os.environ, "REVIEW_REPO_DIR": str(repo_dir)},
        tool_filter=create_static_tool_filter(allowed_tool_names=["list_changed_files", "get_diff"]),
    )


def context_task(agent, base: str, head: str) -> Task:
    """Task des Kontext-Sammlers: erst Dateiliste, dann Diff. Die Antwort ist nur ein Satz;
    die eigentlichen Daten kommen aus den abgegriffenen Werkzeugausgaben."""
    return Task(
        description=(
            f"Call list_changed_files with base='{base}' and head='{head}', then call get_diff with the same "
            "base and head (no path). Then answer with one sentence naming the changed files and the number "
            "of lines of the diff. Do not repeat the diff text."
        ),
        expected_output="One sentence: the changed files and the number of diff lines.",
        agent=agent,
    )


def fetch_context_with_agent(llm: LLM, repo_dir: str, base: str, head: str, use_mcp: bool = True,
                             verbose: bool = False) -> ContextResult:
    """Agentenweg: Werkzeuge per MCP (`use_mcp=True`) oder direkt als @tool-Funktionen."""
    os.environ["REVIEW_REPO_DIR"] = str(repo_dir)  # für die @tool-Funktionen
    if use_mcp:
        agent = make_context_agent(llm, mcps=[git_mcp_server(repo_dir)], verbose=verbose)
    else:
        agent = make_context_agent(llm, tools=GIT_TOOLS, verbose=verbose)
    captured: dict[str, str] = {}

    def _merken_direkt(source, event: ToolUsageFinishedEvent) -> None:  # @tool-Funktionen
        captured[event.tool_name] = event.output if isinstance(event.output, str) else str(event.output)

    def _merken_mcp(source, event: MCPToolExecutionCompletedEvent) -> None:  # MCP: Original-Name des Werkzeugs
        r = event.result
        captured[event.tool_name] = r if isinstance(r, str) else "\n".join(getattr(c, "text", str(c)) for c in (r or []))

    crewai_event_bus.register_handler(ToolUsageFinishedEvent, _merken_direkt)
    crewai_event_bus.register_handler(MCPToolExecutionCompletedEvent, _merken_mcp)
    try:
        crew = Crew(agents=[agent], tasks=[context_task(agent, base, head)], process=Process.sequential, verbose=verbose)
        kickoff_blocking(crew)
    finally:
        crewai_event_bus.off(ToolUsageFinishedEvent, _merken_direkt)
        crewai_event_bus.off(MCPToolExecutionCompletedEvent, _merken_mcp)

    if "get_diff" not in captured:
        raise RuntimeError("Der Kontext-Agent hat get_diff nicht aufgerufen; kein Diff vorhanden.")
    # Dateiliste aus dem Diff ableiten: unabhängig davon, wie das Werkzeug die Liste serialisiert.
    files = re.findall(r"^diff --git a/(.+?) b/", captured["get_diff"], flags=re.M)
    return ContextResult(changed_files=files, diff=captured["get_diff"])
