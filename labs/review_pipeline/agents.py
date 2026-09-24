"""Agenten der Pipeline: drei spezialisierte Reviewer, ein Lead Reviewer, ein Kontext-Sammler.

Rollen und Ziele sind englisch, weil das Modell damit messbar präziser antwortet;
die Reviewer bekommen keine Werkzeuge, sie erhalten den Diff als Task-Eingabe.
"""
import json
import os
from pathlib import Path

from crewai import LLM, Agent
from crewai.llms.providers.openai.completion import OpenAICompletion
from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError

ENV_FILE = Path(__file__).resolve().parent.parent / ".env"  # labs/.env


class SchemaInPromptLLM(OpenAICompletion):
    """Für OpenAI-kompatible Endpunkte ohne `response_format: json_schema` (z. B. DeepSeek).

    CrewAI schickt bei `output_pydantic` das Schema nativ mit (`beta.chat.completions.parse`). Hier wandert
    das Schema stattdessen in den Prompt, und die Antwort wird mit Pydantic validiert (ein Wiederholungsversuch
    mit der Fehlermeldung). Nur der synchrone `call` ist überschrieben; `kickoff_async` nutzt genau den.
    """

    def call(self, messages, tools=None, callbacks=None, available_functions=None, from_task=None,
             from_agent=None, response_model: type[BaseModel] | None = None):
        if response_model is None:
            return super().call(messages, tools, callbacks, available_functions, from_task, from_agent)
        msgs = list(messages) if isinstance(messages, list) else [{"role": "user", "content": messages}]
        msgs.append({"role": "user", "content": "Answer with exactly one JSON object that matches this JSON schema. "
                     "No prose, no code fence.\n" + json.dumps(response_model.model_json_schema())})
        for _ in range(2):
            text = str(super().call(msgs, None, callbacks, available_functions, from_task, from_agent))
            try:
                return response_model.model_validate_json(text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip())
            except ValidationError as e:
                msgs += [{"role": "assistant", "content": text},
                         {"role": "user", "content": f"That was not valid: {e}. Answer again with only the JSON object."}]
        raise ValueError(f"Antwort passt nach zwei Versuchen nicht zu {response_model.__name__}: {text[:300]}")


REASONING_PREFIXES = ("gpt-5", "o1", "o3", "o4")  # lehnen temperature != 1 ab


def make_llm(temperature: float | None = 0.1) -> LLM:
    """LLM aus labs/.env bzw. Umgebungsvariablen (Default: OpenAI-API, gpt-4.1). Kein Netzzugriff beim Erzeugen.

    LLM_SCHEMA_IN_PROMPT=1 erzwingt SchemaInPromptLLM; "auto" (Default) wählt es für DeepSeek-Endpunkte.
    """
    load_dotenv(ENV_FILE, override=True)  # labs/.env schlägt Werte, die crewai beim Import aus anderen .env-Dateien lädt
    os.environ.setdefault("CREWAI_DISABLE_TELEMETRY", "true")
    os.environ.setdefault("OTEL_SDK_DISABLED", "true")
    model = os.environ.get("LLM_MODEL", "gpt-4.1")
    base_url = os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1")
    api_key = os.environ.get("LLM_API_KEY", "")
    if model.startswith(REASONING_PREFIXES):
        temperature = None  # Reasoning-Modelle akzeptieren nur den Standardwert
    modus = os.environ.get("LLM_SCHEMA_IN_PROMPT", "auto")
    if modus == "1" or (modus == "auto" and "deepseek" in base_url):
        return SchemaInPromptLLM(model=model, base_url=base_url, api_key=api_key, **({"temperature": temperature} if temperature is not None else {}))
    return LLM(model=f"openai/{model}", base_url=base_url, api_key=api_key, **({"temperature": temperature} if temperature is not None else {}))


# focus -> (role, goal, backstory). Kurz und präzise: lange Backstories bringen bei Reviews nichts.
REVIEWER_ROLES: dict[str, tuple[str, str, str]] = {
    "correctness": (
        "Correctness Reviewer",
        "Find logic errors in the diff: wrong boundaries and comparisons, off-by-one, missing rounding, "
        "unhandled cases, code that contradicts the documented business rules.",
        "Senior backend engineer who reads a diff line by line and checks every condition against the spec.",
    ),
    "security": (
        "Security Reviewer",
        "Find security weaknesses in the diff: shell or SQL injection, unvalidated user input used in "
        "paths or commands, path traversal, secrets in code, unsafe file handling.",
        "Application security engineer who assumes every external input is hostile.",
    ),
    "style_tests": (
        "Style and Tests Reviewer",
        "Check whether new or changed behaviour is covered by tests and whether the code is readable: "
        "naming, docstrings, duplicated logic, dead code.",
        "Pragmatic maintainer who insists that every new function ships with a test.",
    ),
}


def make_reviewer(llm: LLM, focus: str, verbose: bool = False) -> Agent:
    """Ein Reviewer für einen Fokus (correctness, security, style_tests)."""
    role, goal, backstory = REVIEWER_ROLES[focus]
    return Agent(role=role, goal=goal, backstory=backstory, llm=llm, verbose=verbose,
                 max_iter=2, allow_delegation=False)


def make_reviewers(llm: LLM, verbose: bool = False) -> dict[str, Agent]:
    """Alle drei Reviewer, Schlüssel = Fokus."""
    return {focus: make_reviewer(llm, focus, verbose) for focus in REVIEWER_ROLES}


def make_lead(llm: LLM, verbose: bool = False) -> Agent:
    """Lead Reviewer: führt die Einzelreviews zusammen und fällt das Urteil."""
    return Agent(
        role="Lead Reviewer",
        goal="Merge several partial reviews into one consistent review with a clear verdict.",
        backstory="Tech lead who removes duplicates, weighs severities and writes short, actionable summaries.",
        llm=llm, verbose=verbose, max_iter=2, allow_delegation=False,
    )


def make_context_agent(llm: LLM, tools: list | None = None, mcps: list | None = None, verbose: bool = False) -> Agent:
    """Kontext-Sammler: einziger Agent mit Werkzeugen (direkt per `tools` oder per `mcps`)."""
    return Agent(
        role="Context Collector",
        goal="Fetch the list of changed files and the diff of a pull request using the git tools.",
        backstory="Careful assistant who calls tools with exact arguments and reports results verbatim.",
        llm=llm, tools=tools or [], mcps=mcps, verbose=verbose, max_iter=4, allow_delegation=False,
    )
