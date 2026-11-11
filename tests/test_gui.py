"""Offscreen tests of the PyQt5 desktop GUI (main.py). Skipped when PyQt5 is not installed.

Run: python -m pytest -q tests/test_gui.py
"""
import os
import sys
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PyQt5.QtWidgets")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PyQt5.QtWidgets import QApplication, QSlider  # noqa: E402

import main  # noqa: E402

APP = QApplication.instance() or QApplication([])


def make_gui(config=None):
    return main.SimulationGUI(main.create_simulation(config or {'bottom': 2}))


def test_sliders_use_shared_specs():
    gui = make_gui()
    sliders = gui.findChildren(QSlider)
    assert len(sliders) == 3 + 4 * 2
    assert [(s.minimum(), s.maximum(), s.value()) for s in sliders[:3]] == [(1, 200, 100), (1, 100, 10), (900, 1000, 999)]


def test_reset_clears_standing_wave_selector():
    """Reset sets the tank's standing-wave mode to None; the selector used to keep showing the old mode."""
    gui = make_gui()
    gui.standing_wave_combo.setCurrentText("3")
    assert gui.simulation.tank.standing_wave_mode == 3
    gui.reset_simulation()
    assert gui.simulation.tank.standing_wave_mode is None
    assert gui.standing_wave_combo.currentText() == "None"
