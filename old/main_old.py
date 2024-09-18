import sys
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
                             QWidget, QPushButton, QSlider, QLabel, QScrollArea)
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from simulation import Wave, Slit, Tank, Simulation

class SimulationGUI(QMainWindow):
    def __init__(self, simulation):
        super().__init__()
        self.simulation = simulation
        self.is_running = False
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Wave Interference Simulation')
        self.setGeometry(100, 100, 1000, 800)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Left side: Matplotlib figure
        figure_layout = QVBoxLayout()
        self.figure = Figure(figsize=(5, 5))
        self.canvas = FigureCanvas(self.figure)
        figure_layout.addWidget(self.canvas)
        main_layout.addLayout(figure_layout, 2)

        # Right side: Controls
        controls_layout = QVBoxLayout()
        controls_widget = QWidget()
        controls_widget.setLayout(controls_layout)
        scroll = QScrollArea()
        scroll.setWidget(controls_widget)
        scroll.setWidgetResizable(True)
        main_layout.addWidget(scroll, 1)

        # Slit controls
        controls_layout.addWidget(QLabel('Slit Controls'))
        self.slit_controls = []
        for i, slit in enumerate(self.simulation.tank.slits):
            slit_layout = QVBoxLayout()
            slit_layout.addWidget(QLabel(f'Slit {i+1}'))
            amplitude_slider = self.create_slider(f'Amplitude', 0, 200, int(slit.wave.amplitude * 100),
                                                  lambda value, s=slit: self.update_slit_amplitude(s, value))
            slit_layout.addWidget(amplitude_slider)
            wavelength_slider = self.create_slider(f'Wavelength', 1, 200, int(slit.wave.wavelength * 10),
                                                   lambda value, s=slit: self.update_slit_wavelength(s, value))
            slit_layout.addWidget(wavelength_slider)
            frequency_slider = self.create_slider(f'Frequency', 1, 200, int(slit.wave.frequency * 100),
                                                  lambda value, s=slit: self.update_slit_frequency(s, value))
            slit_layout.addWidget(frequency_slider)
            controls_layout.addLayout(slit_layout)
            self.slit_controls.append((amplitude_slider, wavelength_slider, frequency_slider))

        # Start/Stop button
        self.start_stop_button = QPushButton('Start')
        self.start_stop_button.clicked.connect(self.toggle_simulation)
        controls_layout.addWidget(self.start_stop_button)

        self.ax = self.figure.add_subplot(111)
        self.im = self.simulation.tank.plot(self.ax)
        self.figure.colorbar(self.im)
        self.timer = self.canvas.new_timer(interval=50)
        self.timer.add_callback(self.update_plot)

    def create_slider(self, name, min_val, max_val, default_val, callback):
        slider_layout = QVBoxLayout()
        slider_layout.addWidget(QLabel(name))
        slider = QSlider(Qt.Horizontal)
        slider.setRange(min_val, max_val)
        slider.setValue(default_val)
        slider.valueChanged.connect(callback)
        slider_layout.addWidget(slider)
        container = QWidget()
        container.setLayout(slider_layout)
        return container

    def update_slit_amplitude(self, slit, value):
        slit.wave.amplitude = value / 100

    def update_slit_wavelength(self, slit, value):
        slit.wave.wavelength = value / 10

    def update_slit_frequency(self, slit, value):
        slit.wave.frequency = value / 100

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

def create_simulation(num_slits):
    radius = 10
    resolution = 200
    slits = []
    for i in range(num_slits):
        angle = 2 * np.pi * i / num_slits
        x = radius * np.cos(angle)
        y = radius * np.sin(angle)
        slits.append(Slit((x, y), 0.5))

    tank = Tank(radius, resolution, slits)
    return Simulation(tank)

if __name__ == '__main__':
    app = QApplication(sys.argv)

    num_slits = int(input("Enter the number of slits: "))
    simulation = create_simulation(num_slits)

    gui = SimulationGUI(simulation)
    gui.show()
    sys.exit(app.exec_())
