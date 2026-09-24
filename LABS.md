# Übungen

Alle Übungen laufen in Jupyter-Notebooks unter `labs/`. Die Fassung `*_student.ipynb` enthält die Aufgaben mit Code-Stubs; die Lösungen zeigt der Trainer nach jedem Block. Erwartete Ergebnisse stehen in `EXPECTED_RESULTS.md`. Voraussetzung: `labs/lab_0_setup_check.ipynb` meldet überall OK.

## Lab 1: Die ReAct-Schleife in reinem Python (`lab_1_react_loop.ipynb`, ca. 30 min)

Sie bauen die Schleife aus Gedanke, Aktion und Beobachtung ohne Framework gegen den OpenAI-kompatiblen Endpunkt.

1. Ein-Schuss-Aufruf ohne Werkzeuge: Was macht das Modell mit einer Frage, die eine Datei bräuchte?
2. Werkzeuge als Funktionen mit JSON-Schema definieren und einen `tool_calls`-Aufruf auswerten.
3. Die Schleife: Modell fragen, Werkzeuge ausführen, Beobachtungen anhängen, Abbruch bei finaler Antwort.
4. Stoppbedingungen und Fehler: Schrittlimit, fehlende Datei, unbekanntes Werkzeug, Pfad außerhalb des Datenordners, Token-Zähler.
5. Transfer: dieselbe Aufgabe mit einem CrewAI-Agenten in acht Zeilen; Vergleich der Aufrufe und Tokens.

## Lab 2: Eigener MCP-Server für Git (`lab_2_mcp_server.ipynb`, ca. 55 min)

Sie schreiben einen MCP-Server mit FastMCP, sprechen ihn erst ohne Modell an und hängen ihn dann mit Tool-Filter an einen CrewAI-Agenten. Server: `labs/mcp_git_server.py`, Übungsrepository: `labs/demo-repo-local/` (erzeugt von `labs/make_demo_repo.py`).

1. Server per stdio starten und mit dem MCP-Client-SDK die Werkzeugliste samt Schema abrufen; `list_changed_files` und die Resource `repo://info` aufrufen.
2. Eigenes Werkzeug `count_lines(path, ref)` ergänzen und in der Werkzeugliste sehen.
3. Server über `mcps=[MCPServerStdio(...)]` an einen Agenten hängen, Task: Änderungen des Branches `feature/rabatt-staffel` beschreiben.
4. Tool-Filter: `get_file` entfernen und beobachten, wie der Agent ohne das Werkzeug reagiert.
5. Prompt-Injection: Branch `feature/export-csv` zusammenfassen lassen, einmal naiv, einmal mit dem Diff als gekennzeichnete Daten; beide Ergebnisse festhalten.
6. Nur lesen: offizieller GitHub-MCP-Server per Docker und Tool-Filter.

## Lab 3: Erste Crew und Flow (`lab_3_first_crew.ipynb`, ca. 55 min)

Zwei Agenten (Analyst, Redakteur) erzeugen aus einem Diff eine Änderungszusammenfassung mit Pydantic-Ausgabe; danach läuft die Crew in einem Flow mit State und Verzweigung. Eingabe: `labs/data/diff_rabatt.patch` und `labs/data/diff_leer.patch`.

1. LLM und zwei Agenten mit kurzer, konkreter Rolle, Ziel und Hintergrund definieren.
2. Zwei Tasks mit `context` und `output_pydantic=ChangeSummary`; Crew sequentiell starten, `result.pydantic` und `token_usage` lesen.
3. Funktions-Guardrail an Task 2 (Pflichtfelder, Längen, kein Zeilenumbruch im Titel); einen Verstoß provozieren und das Retry-Verhalten beobachten.
4. Optional: hierarchischer Prozess mit `manager_llm`; Laufzeit und Tokens mit sequentiell vergleichen.
5. Flow: `@start` lädt den Diff, `@router` entscheidet zwischen `has_changes` und `empty`, der Listener ruft die Crew; zwei Läufe, `flow.plot()` ansehen.
6. Kurz: `@human_feedback` als Freigabeschritt mit `emit=["approved", "rejected"]`.

## Lab 4: Code-Review-Pipeline (`lab_4_code_review_pipeline.ipynb`, ca. 90 min)

Sie bauen die Pipeline aus dem Vortrag in sechs Schritten. Der Code liegt als Paket `labs/review_pipeline/`; Sie schreiben die zentralen Stellen selbst (Task-Beschreibungen, Guardrail, Merge-Regel, Flow-Verdrahtung) und importieren den Rest. Reihenfolge ist Bauordnung, jeder Schritt läuft für sich.

1. Datenmodell (`models.py`): `Finding`, `ReviewResult`, `MergedReview`, `ReviewState`; ein Finding von Hand bauen, Validierung eines falschen Schweregrads sehen.
2. Kontext holen (`tools.py`, `context.py`): erst direkt über git-Funktionen, dann über einen Agenten mit dem MCP-Server aus Lab 2; beide Ausgaben vergleichen.
3. Ein Reviewer als Crew (`agents.py`, `crew.py`): Korrektheits-Reviewer auf `feature/rabatt-staffel`, `ReviewResult` ansehen, Guardrail mit erfundenem Dateinamen prüfen.
4. Drei Reviewer parallel (`kickoff_async`, `asyncio.gather`): Laufzeit gegen sequentiell messen.
5. Lead Reviewer (`crew.py`, `render.py`): zusammenführen, deduplizieren, Urteil fällen, Markdown-Tabelle ausgeben.
6. Der Flow (`flow.py`): Kontext, Reviews, Merge, Freigabe-Gate, Veröffentlichung; Lauf gegen `feature/rabatt-staffel` (Bug) und `feature/export-csv` (Prompt-Injection), einmal mit und einmal ohne Diff-Kennzeichnung.
7. Nur lesen und optional: Review auf einen echten Pull Request posten (`github.py`, `python -m review_pipeline --pr N`), GitHub-Action als Trigger.
