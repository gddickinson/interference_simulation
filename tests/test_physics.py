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


@pytest.mark.parametrize("config", [{'bottom': 2}, {'bottom': 3}, {'left': 2}, {'top': 4}])
def test_slits_on_one_wall_are_in_phase(config):
    """Slits on the same wall are fed by the same plane wave, so they oscillate in phase. The phase used to be
    taken from the absolute x coordinate, so slits at different x had different phases."""
    sim = create_simulation(config, resolution=60)
    t = sim.tank
    for _ in range(3):
        sim.step(0.05)
        values = []
        for slit in t.slits:
            x, y = slit.position
            i = min(int(y / t.dy), t.resolution - 1)
            j = min(int(x / t.dx), t.resolution - 1)
            values.append(t.u[i, j])
        assert np.abs(t.u).max() > 0
        assert np.allclose(values, values[0], atol=1e-12), values


def wave_energy(t):
    """Discrete wave energy: sum of (du/dt)^2 + c^2 |grad u|^2 over the interior (per unit cell area)."""
    ut = (t.u - t.u_prev) / t.dt
    gx = (t.u[1:-1, 2:] - t.u[1:-1, :-2]) / (2 * t.dx)
    gy = (t.u[2:, 1:-1] - t.u[:-2, 1:-1]) / (2 * t.dy)
    return float((ut[1:-1, 1:-1] ** 2 + t.c ** 2 * (gx ** 2 + gy ** 2)).sum())


def pulse_energy_left(boundary, time=3.0):
    """A Gaussian pulse released in the middle of an empty tank (no sources, no decay): fraction of its energy still in
    the tank after `time` (it reaches the walls by t ~ 1 and the corners by ~1.4 at c = 10)."""
    from simulation import Simulation, Tank
    t = Tank(20, 20, 100, [], decay_factor=1.0)
    t.set_boundary_type(boundary)
    t.u[:] = np.exp(-((t.X - 10) ** 2 + (t.Y - 10) ** 2) / (2 * 0.8 ** 2))
    t.u_prev[:] = t.u
    sim = Simulation(t)
    sim.step(0.05)
    e0 = wave_energy(t)
    while sim.time < time:
        sim.step(0.05)
    return wave_energy(t) / e0


def test_open_walls_do_not_reflect():
    """'Open' walls must let waves leave: under 3 % of a pulse's energy may come back (they used to reflect fully)."""
    assert pulse_energy_left("reflective") > 0.5
    assert pulse_energy_left("open") < 0.03
