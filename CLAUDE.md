# Claude collaboration notes for `interference_simulation`

George's global preferences (`~/.claude/CLAUDE.md`) apply: files under 500 lines, many small modules,
`INTERFACE.md` as the navigation map, `SESSION_LOG.md` for progress.

@INTERFACE.md

- The browser engine `web/static/wave_engine.js` is a line-by-line port of `simulation.py`. After changing
  `simulation.py`, `sim_setup.py` or `web/reference.py`, update the JS port and run
  `python scripts/make_js_fixtures.py`, then `python -m pytest -q tests`.
- The desktop GUI and the web app share `sim_setup.py`; keep it free of PyQt5.
