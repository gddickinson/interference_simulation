"""Regression tests for the wave-tank model in simulation.py (and the Qt-free set-up in sim_setup.py).

Run: python -m pytest -q tests/test_simulation.py
"""
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from simulation import Obstacle, Simulation, Slit, Tank  # noqa: E402
from sim_setup import create_simulation  # noqa: E402


def test_no_slits_field_stays_finite():
    """A tank with no slits (the desktop prompt allows 0 on every side) used to divide inf by inf in the distance
    map, so the first step turned the whole field into NaN."""
    tank = Tank(20, 20, 60, [])
    tank.add_interference_point((10, 10), 1.0, 1.0)
    sim = Simulation(tank)
    sim.step(0.05)
    assert np.isfinite(tank.distance_map).all()
    assert np.isfinite(tank.u).all() and np.abs(tank.u).max() > 0


def test_obstacles_block_waves_with_open_boundaries():
    """Obstacles are regions where u = 0; with 'open' boundaries the obstacle mask used to be skipped entirely."""
    tank = Tank(20, 20, 60, [Slit((10, 0), 0.5, 10, 1, 2)])
    sim = Simulation(tank)
    tank.add_obstacle(Obstacle((10, 6), 2.0))
    inside = (tank.X - 10) ** 2 + (tank.Y - 6) ** 2 <= 2.0 ** 2
    for boundary in ("reflective", "absorbing", "open"):
        sim.reset()
        tank.set_boundary_type(boundary)
        for _ in range(20):
            sim.step(0.05)
        assert np.abs(tank.u).max() > 0
        assert np.abs(tank.u[inside]).max() == 0, boundary


def test_create_simulation_places_slits_evenly():
    """sim_setup.create_simulation (moved out of main.py) builds the same tank as before."""
    sim = create_simulation({'bottom': 2, 'left': 1})
    assert [s.position for s in sim.tank.slits] == [(20 / 3, 0), (40 / 3, 0), (0, 10.0)]
    assert sim.tank.resolution == 200 and sim.tank.boundary_type == "reflective"
    assert all((s.width, s.amplitude, s.frequency, s.wavelength) == (0.5, 10, 1, 2) for s in sim.tank.slits)
