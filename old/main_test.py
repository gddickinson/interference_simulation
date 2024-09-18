#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Aug 18 15:06:49 2024

@author: george
"""

import sys
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QSlider, QLabel
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from tank import Tank, Simulation
from wave_slit import Wave, Slit


class SimulationGUI(QMainWindow):
    def __init__(self, simulation):
        super().__init__()
        self.simulation = simulation
        self.is_running = False  # Flag to track if simulation is running
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Wave Interference Simulation')
        self.setGeometry(100, 100, 800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Matplotlib figure
        self.figure = Figure(figsize=(5, 5))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        # Controls
        controls_layout = QHBoxLayout()
        layout.addLayout(controls_layout)

        # Viscosity slider
        viscosity_layout = QVBoxLayout()
        viscosity_layout.addWidget(QLabel('Viscosity'))
        self.viscosity_slider = QSlider(Qt.Horizontal)
        self.viscosity_slider.setRange(0, 100)
        self.viscosity_slider.setValue(int(self.simulation.tank.viscosity * 100))
        self.viscosity_slider.valueChanged.connect(self.update_viscosity)
        viscosity_layout.addWidget(self.viscosity_slider)
        controls_layout.addLayout(viscosity_layout)

        # Depth slider
        depth_layout = QVBoxLayout()
        depth_layout.addWidget(QLabel('Depth'))
        self.depth_slider = QSlider(Qt.Horizontal)
        self.depth_slider.setRange(1, 100)
        self.depth_slider.setValue(int(self.simulation.tank.depth * 10))
        self.depth_slider.valueChanged.connect(self.update_depth)
        depth_layout.addWidget(self.depth_slider)
        controls_layout.addLayout(depth_layout)

        # Start/Stop button
        self.start_stop_button = QPushButton('Start')
        self.start_stop_button.clicked.connect(self.toggle_simulation)
        controls_layout.addWidget(self.start_stop_button)

        self.ax = self.figure.add_subplot(111)
        self.im = self.simulation.tank.plot(self.ax)
        self.figure.colorbar(self.im)
        self.timer = self.canvas.new_timer(interval=50)
        self.timer.add_callback(self.update_plot)

    def update_viscosity(self):
        self.simulation.tank.viscosity = self.viscosity_slider.value() / 100

    def update_depth(self):
        self.simulation.tank.depth = self.depth_slider.value() / 10

    def toggle_simulation(self):
        if self.is_running:
            self.timer.stop()
            self.start_stop_button.setText('Start')
            self.is_running = False
        else:
            self.timer.start()
            self.start_stop_button.setText('Stop')
            self.is_running = True

    def update_plot(self):
        self.simulation.step(0.05)
        self.im.set_array(self.simulation.tank.Z)
        self.canvas.draw()

if __name__ == '__main__':
    app = QApplication(sys.argv)

    radius = 10
    resolution = 200
    slits = [
        Slit((-radius, 0), 0.5),
        Slit((radius, 0), 0.5),
    ]
    slits[0].set_wave(Wave(amplitude=1, wavelength=5, frequency=0.5))
    slits[1].set_wave(Wave(amplitude=1, wavelength=5, frequency=0.5, phase=np.pi))

    tank = Tank(radius, resolution, slits, viscosity=0.01)
    simulation = Simulation(tank)

    gui = SimulationGUI(simulation)
    gui.show()
    sys.exit(app.exec_())
