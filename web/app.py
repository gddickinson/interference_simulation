"""FastAPI web app for the Wave Interference Simulation: serves the front end in static/ and the JSON API under /api.

Run with `python run_web.py` (http://127.0.0.1:8230, local only). `scripts/build_static.py` exports every path in
STATIC_ENDPOINTS to JSON for the GitHub Pages site, so keep that list in step with the GET routes below. The tank
itself runs in the browser (static/wave_engine.js, a port of simulation.py); the API serves the desktop app's control
specs and Python-computed reference fields for the cross-check page.
"""
import base64
from pathlib import Path

import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

import sim_setup
from web.reference import EXAMPLE_SETUPS, FRAME_DT, run, seismic_lut

STATIC = Path(__file__).resolve().parent / "static"
REFERENCE_RES = 100
REFERENCE_FRAMES = 12

app = FastAPI(title="Wave Interference Simulation")
app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC / "index.html")


@app.get("/api/info")
def info():
    """Project summary and counts for the home page (all taken from the Python code)."""
    return {
        "title": "Wave Interference Simulation",
        "description": "Interactive 2D simulation of wave interference, reflection, absorption and diffraction in a "
                       "tank, solved with the finite-difference time-domain (FDTD) method.",
        "boundary_types": len(sim_setup.BOUNDARY_TYPES),
        "standing_modes": len(sim_setup.STANDING_WAVE_MODES) - 1,
        "controls": len(sim_setup.CONTROL_SPECS),
        "resolution": sim_setup.RESOLUTION,
        "tank": list(sim_setup.TANK_SIZE),
        "setups": len(EXAMPLE_SETUPS),
    }


@app.get("/api/controls")
def controls():
    """The desktop GUI's choices and slider specs (sim_setup.py), so the web controls use the same ranges."""
    specs = {k: {"label": lab, "min": lo, "max": hi, "scale": sc} for k, (lab, lo, hi, sc) in sim_setup.CONTROL_SPECS.items()}
    return {
        "specs": specs, "global": sim_setup.GLOBAL_CONTROLS, "slit": sim_setup.SLIT_CONTROLS,
        "boundaries": sim_setup.BOUNDARY_TYPES, "standing_modes": sim_setup.STANDING_WAVE_MODES,
        "sides": sim_setup.SIDES, "tank": list(sim_setup.TANK_SIZE), "resolution": sim_setup.RESOLUTION,
        "slit_defaults": sim_setup.SLIT_DEFAULTS, "random_ranges": sim_setup.RANDOM_RANGES,
        "defaults": {"time_scale": 1, "depth": 1.0, "decay_factor": 0.999}, "frame_dt": FRAME_DT,
    }


@app.get("/api/setups")
def setups():
    """Example set-ups for the web page (slit counts per side plus elements the desktop app can add)."""
    return EXAMPLE_SETUPS


@app.get("/api/colormap")
def colormap():
    """matplotlib's 'seismic' colour map (Tank.plot) as 256 RGB triples in 0..1."""
    return seismic_lut()


@app.get("/api/reference/{slug}")
def reference(slug: str):
    """The Python tank (simulation.py) run for one example set-up: displayed field (Tank.field) after REFERENCE_FRAMES desktop frames at
    REFERENCE_RES x REFERENCE_RES, as little-endian float64 in base64 (row 0 = bottom)."""
    setup = next((s for s in EXAMPLE_SETUPS if s["slug"] == slug), None)
    if setup is None:
        raise HTTPException(404, f"unknown setup {slug}")
    sim = run(setup, REFERENCE_FRAMES, REFERENCE_RES)
    u = np.ascontiguousarray(sim.tank.field(), dtype="<f8")
    return {"slug": slug, "resolution": REFERENCE_RES, "frames": REFERENCE_FRAMES, "time": sim.time,
            "steps_per_frame": int(FRAME_DT / sim.tank.dt), "max_abs": float(np.abs(u).max()),
            "u_b64": base64.b64encode(u.tobytes()).decode()}


# GET paths (without the /api prefix) written to the static site as api/<path>.json.
STATIC_ENDPOINTS = ["/info", "/controls", "/setups", "/colormap"] + [f"/reference/{s['slug']}" for s in EXAMPLE_SETUPS]
