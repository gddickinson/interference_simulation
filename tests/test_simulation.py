"""Regression tests for the wave-tank model in simulation.py (and the Qt-free set-up in sim_setup.py).

Run: python -m pytest -q tests/test_simulation.py
"""
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from simulation import Simulation, Tank  # noqa: E402


def test_no_slits_field_stays_finite():
    """A tank with no slits (the desktop prompt allows 0 on every side) used to divide inf by inf in the distance
    map, so the first step turned the whole field into NaN."""
    tank = Tank(20, 20, 60, [])
    tank.add_interference_point((10, 10), 1.0, 1.0)
    sim = Simulation(tank)
    sim.step(0.05)
    assert np.isfinite(tank.distance_map).all()
    assert np.isfinite(tank.u).all() and np.abs(tank.u).max() > 0
