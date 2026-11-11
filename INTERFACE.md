# Wave Interference Simulation -- Interface Map

## Project structure

| File | Purpose |
|------|---------|
| `main.py` | PyQt5 desktop GUI: `SimulationGUI` (matplotlib canvas, sliders, buttons); asks for slit counts at start-up |
| `simulation.py` | The model: `Slit`, `Obstacle`, `Tank` (FDTD wave tank: prescribed sources, decay, boundaries — `apply_mur`, `apply_sponge`, `slit_walls`; `field()` incl. standing wave, `source_amplitude()`, `colour_range()`, `plot`), `Simulation` (time stepping); constants `SIDES`, `SPONGE_WIDTH`, `SPONGE_RATE`, `COLOUR_PERCENTILE` |
| `sim_setup.py` | Qt-free set-up shared by GUI and web: `create_simulation()`, `slit_positions()`, `CONTROL_SPECS` (slider label/range/scale), `BOUNDARY_TYPES`, `STANDING_WAVE_MODES`, `SIDES`, `RANDOM_RANGES`, `SLIT_DEFAULTS` |
| `old/` | Earlier prototypes (kept for reference, not used) |
| `run_web.py` | Starts the web app (uvicorn, http://127.0.0.1:8230) |
| `requirements-web.txt` | Pinned web/test dependencies |
| `tests/test_simulation.py` | Regression tests for `simulation.py` / `sim_setup.py` |
| `tests/test_physics.py` | Physics regression tests: bounded sources, slit phase, open/absorbing walls, colour range |
| `tests/test_gui.py` | Offscreen PyQt5 tests of `main.py` (skipped without PyQt5) |
| `tests/test_web.py` | API, static build, fixture-is-current and node engine tests |
| `tests/fixtures/wave_reference.json` | Python reference numbers for the node test (`scripts/make_js_fixtures.py`) |

## Web interface (`web/`)

| File | Purpose |
|------|---------|
| `web/app.py` | FastAPI app: `/api/info`, `/api/controls`, `/api/setups`, `/api/colormap`, `/api/reference/{slug}`; `STATIC_ENDPOINTS` |
| `web/reference.py` | `EXAMPLE_SETUPS`, `build()` / `run()` (Python tank from a setup dict), `seismic_lut()`, `fixture()` |
| `web/static/index.html`, `style.css`, `core.js` | Shell, shared theme and router (web kit; `style.css`/`core.js` unchanged) |
| `web/static/style_app.css` | Blue/red accents and page styles |
| `web/static/main.js` | Registers lazy pages, starts the router |
| `web/static/static_api.js` | Answers `api()` from exported JSON on the static site |
| `web/static/wave_engine.js` | JS port of `simulation.py` + `sim_setup.create_simulation`: `Tank` (incl. `applyMur`, `applySponge`, `field`, `colourRange`), `Simulation`, `createSimulation()`, `buildSetup()`, `linspace()`, `percentileAbs()`, `roundHalfEven()` |
| `web/static/wave_engine.test.mjs` | Node test of the engine and colour map against the Python fixture |
| `web/static/wave_render.js` | `SEISMIC_LUT` (matplotlib seismic), `drawField()`, `lutIndex()` |
| `web/static/ui.js` | `loadSetup()`, `draw()`, `legend()`, `pacer()` (50 ms desktop pace), `decodeF64()` |
| `web/static/home.js` | `#/` hero with a live tank, counts, cards |
| `web/static/tank.js`, `tank_panel.js` | `#/tank` the simulator (loop, canvas, keyboard) and its control panel / `randomElement()` |
| `web/static/examples.js` | `#/examples` live thumbnails of every example set-up; `describe()` |
| `web/static/check.js` | `#/check` Python vs browser fields side by side |
| `web/static/about.js` | `#/about` model, controls, run instructions, credits |
| `scripts/build_static.py` | Exports the static site to `site/` |
| `scripts/screenshots.py` | Playwright smoke test and `docs/img/*.png` |
| `scripts/make_js_fixtures.py` | Writes `tests/fixtures/wave_reference.json` |
| `.github/workflows/pages.yml` | Builds and publishes the static site on push to main |

## Module connections

```
main.py -> sim_setup.py (create_simulation, CONTROL_SPECS, ...) -> simulation.py (Slit, Obstacle, Tank, Simulation)
run_web.py -> web/app.py -> sim_setup.py, web/reference.py -> simulation.py
web/static/main.js -> page modules -> ui.js, tank_panel.js, wave_render.js, wave_engine.js (JS port of simulation.py)
```
