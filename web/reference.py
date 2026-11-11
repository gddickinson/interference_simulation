"""Run the repo's Python wave tank (simulation.py via sim_setup.create_simulation) for the web interface.

- EXAMPLE_SETUPS: quick-start configurations offered by the web app (slit counts per side plus the same kinds of
  elements the desktop GUI can add). They are examples chosen for the web page, not presets from the desktop app.
- build(setup): a Simulation configured from a setup dict; web/static/wave_engine.js buildSetup() mirrors it.
- run(setup, frames, resolution): build and advance `frames` desktop frames (Simulation.step(0.05) each).
- seismic_lut(): matplotlib's 'seismic' colormap (the desktop plot's cmap) as 256 RGB triples.
- fixture(): reference numbers for the node tests (tests/fixtures/wave_reference.json).
"""
import numpy as np

from sim_setup import create_simulation
from simulation import Obstacle

FRAME_DT = 0.05  # SimulationGUI.update_plot calls simulation.step(0.05) every 50 ms timer tick

EXAMPLE_SETUPS = [
    {'slug': 'double-slit', 'name': 'Two sources (bottom)', 'slits': {'bottom': 2},
     'note': 'Two slits on the bottom edge: a two-source interference pattern.'},
    {'slug': 'single-obstacle', 'name': 'One source and an obstacle', 'slits': {'bottom': 1},
     'obstacles': [[10, 8, 1.5]], 'note': 'A circular obstacle in front of a single slit casts a shadow.'},
    {'slug': 'facing', 'name': 'Facing sources', 'slits': {'left': 1, 'right': 1},
     'note': 'Slits on opposite walls send waves towards each other.'},
    {'slug': 'four-sides', 'name': 'One slit per side (open)', 'slits': {'bottom': 1, 'top': 1, 'left': 1, 'right': 1},
     'boundary': 'open', 'note': 'A slit in the middle of every wall, with open boundaries.'},
    {'slug': 'standing', 'name': 'Standing-wave mode 3', 'slits': {'bottom': 1}, 'standing': 3, 'depth': 2.5,
     'note': 'Standing-wave mode 3 on top of one slit, in deeper water (depth 2.5).'},
    {'slug': 'packets-points', 'name': 'Packet and point sources', 'slits': {}, 'boundary': 'absorbing',
     'packets': [[6, 14, 1.5, 1.0, 3.0, 2.0, 0.8, -0.6]], 'points': [[14, 6, 1.5, 1.2], [14, 14, 1.0, 0.7]],
     'note': 'No slits: one wave packet and two interference points with absorbing edges.'},
]


def build(setup, resolution=None):
    """Simulation from a setup dict. Keys (all optional except slits): slits {side: count}, depth, decay_factor,
    time_scale, boundary, standing (mode or None), obstacles [[x, y, r]], packets [[x, y, amplitude, frequency,
    wavelength, width, dx, dy]], points [[x, y, amplitude, frequency]], slit_params {amplitude, frequency, ...}."""
    kw = {} if resolution is None else {'resolution': resolution}
    sim = create_simulation(dict(setup.get('slits', {})), depth=setup.get('depth', 1.0),
                            decay_factor=setup.get('decay_factor', 0.999), **kw)
    tank = sim.tank
    for slit in tank.slits:
        for k, v in setup.get('slit_params', {}).items():
            setattr(slit, k, v)
    tank.set_boundary_type(setup.get('boundary', 'reflective'))
    sim.set_time_scale(setup.get('time_scale', 1))
    tank.set_standing_wave_mode(setup.get('standing'))
    for x, y, r in setup.get('obstacles', []):
        tank.add_obstacle(Obstacle((x, y), r))
    for x, y, a, f, wl, w, ddx, ddy in setup.get('packets', []):
        tank.add_wave_packet((x, y), a, f, wl, w, (ddx, ddy))
    for x, y, a, f in setup.get('points', []):
        tank.add_interference_point((x, y), a, f)
    return sim


def run(setup, frames, resolution=None):
    sim = build(setup, resolution)
    for _ in range(frames):
        sim.step(FRAME_DT)
    return sim


def seismic_lut():
    from matplotlib import colormaps
    return colormaps['seismic'](np.linspace(0, 1, 256))[:, :3].tolist()


# --- node-test fixture --------------------------------------------------------------------------------------------
FIXTURE_RES = 41
FIXTURE_CASES = [
    dict(EXAMPLE_SETUPS[0], frames=3),
    dict(EXAMPLE_SETUPS[1], frames=3, boundary='open'),
    dict(EXAMPLE_SETUPS[2], frames=2, boundary='absorbing'),
    dict(EXAMPLE_SETUPS[3], frames=2, boundary='reflective', depth=0.4, time_scale=1.7, decay_factor=0.95,
         slit_params={'amplitude': 3.5, 'wavelength': 1.3, 'frequency': 0.6, 'width': 0.9}),
    dict(EXAMPLE_SETUPS[4], frames=2),
    dict(EXAMPLE_SETUPS[5], frames=3),
]


def fixture():
    cases = []
    for c in FIXTURE_CASES:
        sim = run(c, c['frames'], FIXTURE_RES)
        t = sim.tank
        cases.append({'setup': c, 'time': sim.time, 'dt': t.dt, 'c': t.c, 'steps': int(FRAME_DT / t.dt),
                      'distance_sum': float(t.distance_map.sum()), 'distance_row7': t.distance_map[7].tolist(),
                      'boundary_zeros': int((t.boundary == 0).sum()), 'u': t.u.ravel().tolist(),
                      'u_prev_sum': float(t.u_prev.sum())})
    return {'resolution': FIXTURE_RES, 'x': np.linspace(0, 20, FIXTURE_RES).tolist(), 'cases': cases,
            'seismic': seismic_lut()}
