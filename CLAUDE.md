# Notes for Claude

Capstone project: a live, GitHub-linked dashboard telling the Education City student story (applied → enrolled → studying → graduated → outcomes) from QF Student Data Collection files.

- **Current status:** `docs/ROADMAP.md`. **Past decisions:** `docs/DECISIONS.md`. Read both before starting work.
- **Working style:** one phase and one small step at a time. Explain the goal, build it, show how to check the result, and wait for the owner's go-ahead before the next phase. Tick the ROADMAP checklist as items finish.
- **Rules:** never edit files in `data/raw/` (D-003). The repository and the app are public for now by the owner's choice (D-045): never change their visibility without asking. Keep library versions pinned (D-004).
- **Build all tables:** `.venv/bin/python -m pipeline.build` (stops without writing if a person is needed, then runs the tests). **Run the app:** `.venv/bin/python -m streamlit run app.py`
- **GitHub rebuilds on every push** (`.github/workflows/build.yml`, D-044) and commits the rebuilt tables to `main`: `git pull` before starting work.
- **Reading processed CSVs:** use `keep_default_na=False` for text columns (pandas otherwise turns "N/A" into missing).
