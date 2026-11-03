# Notes for Claude

Capstone project: a live, GitHub-linked dashboard telling the Education City student story (applied → enrolled → studying → graduated → outcomes) from QF Student Data Collection files.

- **Current status:** `docs/ROADMAP.md`. **Past decisions:** `docs/DECISIONS.md`. Read both before starting work.
- **Working style:** one phase and one small step at a time. Explain the goal, build it, show how to check the result, and wait for the owner's go-ahead before the next phase. Tick the ROADMAP checklist as items finish.
- **Rules:** never edit files in `data/raw/` (D-003). The repository must stay private (D-001). Keep library versions pinned (D-004).
- **Run:** `.venv/bin/python -m streamlit run app.py`
