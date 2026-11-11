"""Physics regression tests for the wave tank (simulation.py): bounded sources, slit phase, open and absorbing walls.

Run: python -m pytest -q tests/test_physics.py
"""
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sim_setup import create_simulation  # noqa: E402


def run_frames(sim, frames):
    peak = 0.0
    for _ in range(frames):
        sim.step(0.05)
        peak = max(peak, float(np.abs(sim.tank.field()).max()))
    return peak


@pytest.mark.parametrize("boundary", ["reflective", "absorbing", "open"])
@pytest.mark.parametrize("config", [{'bottom': 2}, {'bottom': 1, 'top': 1, 'left': 1, 'right': 1}])
def test_slit_sources_stay_bounded(config, boundary):
    """Slits are prescribed oscillations of amplitude A: the field must not build up to many times A
    (sources used to be added every step, so |u| reached 10^3-10^4 for A = 10)."""
    sim = create_simulation(config, resolution=60)
    sim.tank.set_boundary_type(boundary)
    a = max(s.amplitude for s in sim.tank.slits)
    assert run_frames(sim, 300) < 5 * a


def test_points_packets_and_standing_wave_stay_bounded():
    sim = create_simulation({}, resolution=60)
    t = sim.tank
    t.add_interference_point((14, 6), 1.5, 1.2)
    t.add_wave_packet((6, 14), 1.5, 1.0, 3.0, 2.0, (0.8, -0.6))
    t.set_standing_wave_mode(3)
    assert run_frames(sim, 300) < 5 * 1.5 + 0.5


def test_colour_range_follows_source_amplitude():
    sim = create_simulation({'bottom': 2}, resolution=40)
    assert sim.tank.colour_range() == 10
    sim.tank.slits[0].amplitude = 14
    assert sim.tank.colour_range() == 14
    assert create_simulation({}, resolution=40).tank.colour_range() == 1
