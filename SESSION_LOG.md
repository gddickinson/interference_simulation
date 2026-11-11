# Session log

## 2026-11-11 — Web interface and static GitHub Pages site (branch `web-interface`)

- **Bug fixes (own commits, regression tests in `tests/test_simulation.py`)**:
  - *No slits → NaN field*: `Tank.update_distance_map` divided an all-inf map by inf; now the map is zero (no
    distance decay) when there are no slits.
  - *Open boundaries ignored obstacles*: the obstacle mask was skipped for `open`; obstacles now block waves in all
    three modes.
- **Refactor**: `create_simulation` moved from `main.py` to the new Qt-free `sim_setup.py` (unchanged), together with
  the slider specs (`CONTROL_SPECS`), boundary/standing-mode choices and random ranges; `main.py` builds its sliders
  from it (same ranges/defaults; checked offscreen: 15 sliders, add/step/toggle work).
- **JS port** `web/static/wave_engine.js` of `Tank`/`Simulation`: matches the Python fields to <= 3e-15 relative
  (6 fixture cases at 41x41, all boundary types, slit params, depth, decay, time scale, obstacles, packets, points,
  standing mode) and on the Cross-check page (6 set-ups, 100x100, 12 frames, <= 1e-14 relative). The seismic colour
  map equals matplotlib's to 1e-12.
- **Pages**: Home (live tank), Tank (all desktop controls + slit-count prompt, examples, grid size, auto colour range,
  click-to-place, PNG), Examples, Cross-check, About.
- **Tests**: `python -m pytest -q tests` (3 simulation + 19 web incl. node engine test); screenshots smoke test ok on
  the static build and on `run_web.py`; no phone-width overflow.
- **For George** (not changed — behaviour unclear or would change results beyond a bug):
  - Sources (slits, packets, points, standing mode) are *added* to u every FDTD step, so |u| reaches 10^3–10^4 and the
    fixed ±1 colour range shows mostly the sign of u.
  - The slit source phase uses the absolute x coordinate, sin(2π(f t − x/λ)), so slits at different x are not in
    phase (e.g. the two default bottom slits differ by 2π·Δx/λ), and along a bottom/top slit the phase varies.
  - `open` edges: the stencil never updates the outer ring (u stays 0 there), so open edges reflect; after the
    obstacle fix `open` behaves almost exactly like `reflective`. A transparent boundary would need e.g. a Mur
    absorbing condition.
  - `absorbing` damps the 10 outer cells after the sources are added, so wall slits are nearly silent in that mode.
  - Time Scale only scales the source clock (propagation per step is unchanged).
  - `Slit.direction` (hard-coded tank size 20) is never used; wave-packet directions are not normalised.
  - README says c = √(gh); the code uses c = 10·√depth.
- Not pushed (lead reviews first).

### Fix: standing-wave selector after Reset
`Tank.reset` clears the standing-wave mode, but the desktop selector kept showing the old mode (choosing the same
mode again then did nothing). `SimulationGUI.reset_simulation` now sets the selector back to "None".
Regression test: `tests/test_gui.py` (offscreen PyQt5).

### Fix: README claims the code doesn't match
Corrected the clone URL, Time Scale (scales the source clock, not the whole simulation), wave speed (c = 10·√h, not
√(gh)), open boundaries (walls still reflect), Reset (obstacles stay), and how slits, wave packets and standing waves
are driven (added every step).

## 2026-11-11 (later) — Physics fixes approved by George (Python and JS engines kept matching)

### Fix 1: sources are prescribed oscillations (bounded field)
Slits and interference points now *set* their cells to A·sin(...) (hard sources, ripple-tank dipper) instead of adding
to u every step; wave packets blend the prescribed travelling sinusoid in with their Gaussian weight; the standing-wave
mode is superposed on the displayed field (`Tank.field()`), not accumulated. Max |u| now stays at the source amplitude
(10 for default slits; was 10^3–10^4). Plot colour range is ± the largest source amplitude (`Tank.colour_range()`,
used by `Tank.plot` and the GUI); the web keeps an "auto" option. Tests: `tests/test_physics.py` (bounded over 300
frames for all boundaries, points/packets/standing, colour range) and a node check.

### Fix 2: slits on one wall are in phase
The slit phase used the absolute x coordinate, so the two default bottom slits differed by 2π·Δx/λ and the phase
varied along bottom/top openings. The phase now uses the distance from the wall along the incoming plane wave's
direction (into the tank), so all slits on a wall are in phase. The unused `Slit.direction` (hard-coded tank size
20) was removed. Tests: `test_slits_on_one_wall_are_in_phase` + node check.

### Fix 3: open walls are transparent
The FDTD stencil never updated the outer ring, so "open" walls reflected like fixed ones. They now use the first-order
Mur (Engquist–Majda) absorbing condition (`Tank.apply_mur`). A Gaussian pulse in an empty tank keeps 0.04 % of its
energy after t = 3 with open walls (99.6 % with reflective; was 99.6 % with open too). Tests:
`test_open_walls_do_not_reflect` + node check.
