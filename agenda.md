# KI-Agenten und Multi-Agenten-Systeme mit CrewAI

**Eintägige Inhouse-Fortbildung für das IT-Team** · Trainer: Dr.-Ing. Grigory Devadze

## Ziel

Sie verstehen, wie KI-Agenten aufgebaut sind (Modell, Werkzeuge, Schleife), wie Tool-Calling und das Model Context Protocol (MCP) funktionieren, und bauen mit CrewAI eine Multi-Agenten-Pipeline, die Pull Requests auf GitHub automatisch prüft und einen Review-Kommentar vorbereitet, den ein Mensch freigibt.

## Voraussetzungen

- Fundierte IT- und Programmiererfahrung, Python-Lesefähigkeit
- Erfahrung mit LLM-Chatbots im Alltag; keine Vorkenntnisse in Agentenentwicklung nötig
- Vorbereitetes Gerät (siehe „Vor dem Termin")

## Zeitplan

| Zeit | Block | Inhalt |
|---|---|---|
| 09:00 – 09:30 | Einrichtung | Umgebung prüfen, Kursrepo klonen, LLM-Endpunkt und GitHub-Zugang testen |
| 09:30 – 10:15 | Teil 1, Vortrag | Agenten verstehen: augmented LLM, ReAct-Schleife, Workflows gegen Agenten, Orchestrierungsmuster |
| 10:15 – 10:45 | Teil 1, Übung | Lab 1: ReAct-Schleife in reinem Python |
| 10:45 – 11:00 | Pause | |
| 11:00 – 11:35 | Teil 2, Vortrag | Tool-Calling und MCP: Function Calling, JSON-Schema, MCP-Architektur, Sicherheit |
| 11:35 – 12:30 | Teil 2, Übung | Lab 2: eigener MCP-Server, Einbindung in CrewAI, Tool-Filter, Prompt-Injection |
| 12:30 – 13:15 | Mittagspause | |
| 13:15 – 13:50 | Teil 3, Vortrag | CrewAI: Agent, Task, Crew, Prozesse, Flows, Guardrails, Human-in-the-Loop |
| 13:50 – 14:45 | Teil 3, Übung | Lab 3: erste Crew mit strukturierter Ausgabe, dann eingebettet in einen Flow |
| 14:45 – 15:00 | Pause | |
| 15:00 – 15:30 | Teil 4, Vortrag | Praxisfall: Architektur der Code-Review-Pipeline, Rollen, Datenmodell, Prompt-Injection im Diff |
| 15:30 – 17:00 | Teil 4, Übung | Lab 4: Review-Pipeline in sechs Schritten bauen und gegen zwei Pull Requests laufen lassen |
| 17:00 – 17:45 | Teil 5 | Betrieb, Grenzen, Sicherheit; Transfer auf eigene Vorhaben; Abschluss |

Die Zeiten sind Richtwerte. Übungen können je nach Tempo verlängert werden; Teil 5 lässt sich auf 30 Minuten kürzen.

## Vor dem Termin

- **Python 3.10 bis 3.13** (CrewAI verlangt mindestens 3.10 und weniger als 3.14; Python 3.14 funktioniert nicht)
- **uv** als Paketmanager, dann `uv tool install crewai`
- MCP-Unterstützung: `uv add mcp` im Projekt (oder über die requirements des Kursrepos)
- **Git** und ein **GitHub-Account**
- Kein eigener API-Schlüssel nötig: den OpenAI-Schlüssel für den Kurstag stellt der Trainer
- **VS Code** mit Python- und Jupyter-Erweiterung
- Test: `crewai version`, dann `crewai create crew demo && cd demo && crewai run`

## LLM-Zugang

Der Kurs läuft mit einem **Cloud-Modell** über die OpenAI-API (Standard `gpt-4.1`); den API-Schlüssel dafür bringt der Trainer mit; er wird am Kurstag in `labs/.env` eingetragen (Vorlage `labs/.env.example`) und nach dem Kurs deaktiviert. Ein lokales Modell über LM Studio oder Ollama zeigt der Trainer kurz als Alternative; derselbe Code läuft dann über drei geänderte Umgebungsvariablen (`LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`).

## Material

- Kursrepository: `https://github.com/grigory-consulting/crewai-review-demo` (Folien, Notebooks, MCP-Server, Übungsrepository)
- Übungen: `LABS.md`
