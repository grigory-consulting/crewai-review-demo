# KI-Agenten und Multi-Agenten-Systeme mit CrewAI

Kursmaterial zur eintägigen Fortbildung: Architektur von KI-Agenten, Tool-Calling mit dem Model Context Protocol (MCP) und der Aufbau einer Multi-Agenten-Pipeline für automatisiertes Code-Review auf GitHub mit CrewAI.

## Inhalt

| Ordner / Datei | Inhalt |
|---|---|
| `agenda.md` | Zeitplan, Voraussetzungen, LLM-Zugang |
| `slides/ki-agenten.md` | Folien (Obsidian Slides Extended, Design in `slides/ki-agenten.css`) |
| `slides/figs/` | Diagramme aus den Folien (PNG, SVG) |
| `labs/` | Notebooks zu den Übungsblöcken (`*_student.ipynb` ohne Lösungen), MCP-Server `mcp_git_server.py`, Paket `review_pipeline/`, `make_demo_repo.py` für das lokale Übungsrepository |
| `LABS.md` | Übungsübersicht |
| `demo/` | Übungsprojekt (Warenkorb); die Pull Requests dieses Repos sind die Eingaben für die Review-Pipeline |
| `requirements.txt`, `pyproject.toml` | Python-Umgebung |

## Einrichtung

Python 3.10 bis 3.13 (CrewAI verlangt mindestens 3.10 und weniger als 3.14), `uv`, Git, VS Code.

```bash
git clone https://github.com/grigory-consulting/crewai-review-demo.git
cd crewai-review-demo
uv venv --python 3.12 .venv
uv pip install -r requirements.txt
cp labs/.env.example labs/.env      # LLM_BASE_URL, LLM_API_KEY, LLM_MODEL, GITHUB_TOKEN
```

Der Kurs läuft gegen die OpenAI-API (`gpt-4.1`); der Schlüssel kommt in `labs/.env`. Ein lokales Modell über LM Studio oder Ollama läuft mit demselben Code, nur die drei `LLM_*`-Variablen ändern sich.

## Folien ansehen

Die Folien sind eine Markdown-Datei für das Obsidian-Plugin Slides Extended. Alternativ lässt sich `slides/ki-agenten.md` in jedem Markdown-Viewer lesen; die Diagramme liegen als PNG in `slides/figs/`.
