#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Aug 18 15:03:17 2024

@author: george
"""

import numpy as np
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Wave:
    def __init__(self, amplitude, wavelength, frequency, phase=0):
        self.amplitude = amplitude
        self.wavelength = wavelength
        self.frequency = frequency
        self.phase = phase

    def value_at(self, distance, time):
        k = 2 * np.pi / self.wavelength
        omega = 2 * np.pi * self.frequency
        return self.amplitude * np.sin(k * distance - omega * time + self.phase)

class Slit:
    def __init__(self, position, width, is_open=True):
        self.position = position  # (x, y) tuple
        self.width = width
        self.is_open = is_open
        self.wave = None

    def set_wave(self, wave):
        self.wave = wave

    def generate_wave(self, distance, time):
        if self.is_open and self.wave:
            return self.wave.value_at(distance, time)
        return 0

def test_wave():
    wave = Wave(1, 2, 1)
    assert np.isclose(wave.value_at(0, 0), 0)
    assert np.isclose(wave.value_at(0.5, 0), 1)
    logging.info("Wave test passed")

def test_slit():
    slit = Slit((0, 0), 1)
    wave = Wave(1, 2, 1)
    slit.set_wave(wave)
    assert np.isclose(slit.generate_wave(0, 0), 0)
    assert np.isclose(slit.generate_wave(0.5, 0), 1)
    slit.is_open = False
    assert np.isclose(slit.generate_wave(0.5, 0), 0)
    logging.info("Slit test passed")

if __name__ == "__main__":
    test_wave()
    test_slit()
