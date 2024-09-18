import sys
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
                             QWidget, QPushButton, QSlider, QLabel, QScrollArea, QCheckBox,
                             QComboBox)
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from simulation import Slit, Obstacle, Tank, Simulation



class SimulationGUI(QMainWindow):
    def __init__(self, simulation):
        super().__init__()
        self.simulation = simulation
        self.is_running = False
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Wave Interference Simulation')
        self.setGeometry(100, 100, 1200, 800)

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

        # Global controls
        controls_layout.addWidget(QLabel('Global Controls'))
        self.time_scale_slider = self.create_slider('Time Scale', 1, 200, 100, self.update_time_scale)
        controls_layout.addWidget(self.time_scale_slider)

        # Depth slider
        self.depth_slider = self.create_slider('Depth', 1, 100, int(self.simulation.tank.depth * 10),
                                               self.update_depth)
        controls_layout.addWidget(self.depth_slider)

        # Decay factor slider
        self.decay_slider = self.create_slider('Wave Decay', 900, 1000, int(self.simulation.tank.decay_factor * 1000),
                                               self.update_decay_factor)
        controls_layout.addWidget(self.decay_slider)

        # Boundary type selection
        self.boundary_combo = QComboBox()
        self.boundary_combo.addItems(["Reflective", "Absorbing", "Open"])
        self.boundary_combo.currentTextChanged.connect(self.change_boundary_type)
        controls_layout.addWidget(QLabel("Boundary Type:"))
        controls_layout.addWidget(self.boundary_combo)

        # Standing wave mode selector
        self.standing_wave_combo = QComboBox()
        self.standing_wave_combo.addItems(["None", "1", "2", "3", "4", "5"])
        self.standing_wave_combo.currentTextChanged.connect(self.change_standing_wave_mode)
        controls_layout.addWidget(QLabel("Standing Wave Mode:"))
        controls_layout.addWidget(self.standing_wave_combo)

        # Slit controls
        controls_layout.addWidget(QLabel('Slit Controls'))
        self.slit_controls = []
        for i, slit in enumerate(self.simulation.tank.slits):
            slit_layout = QVBoxLayout()
            slit_layout.addWidget(QLabel(f'Slit {i+1}'))
            amplitude_slider = self.create_slider(f'Amplitude', 0, 200, int(slit.amplitude * 10),
                                                  lambda value, s=slit: self.update_slit_amplitude(s, value))
            slit_layout.addWidget(amplitude_slider)
            wavelength_slider = self.create_slider(f'Wavelength', 1, 200, int(slit.wavelength * 10),
                                                   lambda value, s=slit: self.update_slit_wavelength(s, value))
            slit_layout.addWidget(wavelength_slider)
            frequency_slider = self.create_slider(f'Frequency', 1, 200, int(slit.frequency * 100),
                                                  lambda value, s=slit: self.update_slit_frequency(s, value))
            slit_layout.addWidget(frequency_slider)
            width_slider = self.create_slider(f'Width', 1, 100, int(slit.width * 100),
                                              lambda value, s=slit: self.update_slit_width(s, value))
            slit_layout.addWidget(width_slider)
            controls_layout.addLayout(slit_layout)
            self.slit_controls.append((amplitude_slider, wavelength_slider, frequency_slider, width_slider))

        # Buttons
        button_layout = QHBoxLayout()
        self.start_stop_button = QPushButton('Start')
        self.start_stop_button.clicked.connect(self.toggle_simulation)
        button_layout.addWidget(self.start_stop_button)

        self.reset_button = QPushButton('Reset')
        self.reset_button.clicked.connect(self.reset_simulation)
        button_layout.addWidget(self.reset_button)

        self.add_obstacle_button = QPushButton('Add Obstacle')
        self.add_obstacle_button.clicked.connect(self.add_obstacle)
        button_layout.addWidget(self.add_obstacle_button)

        self.add_wave_packet_button = QPushButton('Add Wave Packet')
        self.add_wave_packet_button.clicked.connect(self.add_wave_packet)
        button_layout.addWidget(self.add_wave_packet_button)

        self.add_interference_point_button = QPushButton('Add Interference Point')
        self.add_interference_point_button.clicked.connect(self.add_interference_point)
        button_layout.addWidget(self.add_interference_point_button)

        controls_layout.addLayout(button_layout)

        self.ax = self.figure.add_subplot(111)
        self.im = self.simulation.tank.plot(self.ax)
        self.ax.set_title('Wave Interference Simulation')
        self.ax.set_xlabel('X')
        self.ax.set_ylabel('Y')
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

    def update_time_scale(self, value):
        self.simulation.set_time_scale(value / 100)

    def update_depth(self, value):
        depth = value / 10
        self.simulation.tank.set_depth(depth)
        print(f"Updated tank depth to {depth}")

    def update_decay_factor(self, value):
        decay_factor = value / 1000
        self.simulation.tank.set_decay_factor(decay_factor)
        print(f"Updated wave decay factor to {decay_factor}")

    def change_boundary_type(self, boundary_type):
        self.simulation.tank.set_boundary_type(boundary_type.lower())
        print(f"Changed boundary type to {boundary_type}")
        self.update_plot()

    def change_standing_wave_mode(self, mode):
        if mode == "None":
            self.simulation.tank.set_standing_wave_mode(None)
        else:
            self.simulation.tank.set_standing_wave_mode(int(mode))
        print(f"Changed standing wave mode to {mode}")

    def update_slit_amplitude(self, slit, value):
        slit.amplitude = value / 10
        print(f"Updated slit amplitude to {slit.amplitude}")

    def update_slit_wavelength(self, slit, value):
        slit.wavelength = value / 10
        print(f"Updated slit wavelength to {slit.wavelength}")

    def update_slit_frequency(self, slit, value):
        slit.frequency = value / 100
        print(f"Updated slit frequency to {slit.frequency}")

    def update_slit_width(self, slit, value):
        slit.width = value / 100
        print(f"Updated slit width to {slit.width}")

    def toggle_simulation(self):
        if self.is_running:
            self.timer.stop()
            self.start_stop_button.setText('Start')
            self.is_running = False
        else:
            self.timer.start()
            self.start_stop_button.setText('Stop')
            self.is_running = True

    def reset_simulation(self):
        self.simulation.reset()
        self.update_plot()

    def add_obstacle(self):
        x = np.random.uniform(0, self.simulation.tank.width)
        y = np.random.uniform(0, self.simulation.tank.height)
        radius = np.random.uniform(0.5, 2)
        obstacle = Obstacle((x, y), radius)
        self.simulation.tank.add_obstacle(obstacle)
        self.update_plot()
        print(f"Added obstacle at ({x:.2f}, {y:.2f}) with radius {radius:.2f}")

    def add_wave_packet(self):
        x = np.random.uniform(0, self.simulation.tank.width)
        y = np.random.uniform(0, self.simulation.tank.height)
        amplitude = np.random.uniform(0.5, 2)
        frequency = np.random.uniform(0.5, 2)
        wavelength = np.random.uniform(1, 5)
        width = np.random.uniform(1, 3)
        direction = (np.random.uniform(-1, 1), np.random.uniform(-1, 1))
        self.simulation.tank.add_wave_packet((x, y), amplitude, frequency, wavelength, width, direction)
        print(f"Added wave packet at ({x:.2f}, {y:.2f})")

    def add_interference_point(self):
        x = np.random.uniform(0, self.simulation.tank.width)
        y = np.random.uniform(0, self.simulation.tank.height)
        amplitude = np.random.uniform(0.5, 2)
        frequency = np.random.uniform(0.5, 2)
        self.simulation.tank.add_interference_point((x, y), amplitude, frequency)
        print(f"Added interference point at ({x:.2f}, {y:.2f})")

    def update_plot(self):
        self.simulation.step(0.05)
        self.im.set_array(self.simulation.tank.u)
        self.im.set_clim(vmin=-1, vmax=1)  # Fixed color scaling
        self.canvas.draw()

def create_simulation(slit_config, depth=1.0, decay_factor=0.999):
    width, height = 20, 20
    resolution = 200
    slits = []

    for side, num_slits in slit_config.items():
        for i in range(num_slits):
            if side == 'bottom':
                x = width * (i + 1) / (num_slits + 1)
                y = 0
            elif side == 'top':
                x = width * (i + 1) / (num_slits + 1)
                y = height
            elif side == 'left':
                x = 0
                y = height * (i + 1) / (num_slits + 1)
            elif side == 'right':
                x = width
                y = height * (i + 1) / (num_slits + 1)

            slits.append(Slit((x, y), width=0.5, amplitude=10, frequency=1, wavelength=2))

    tank = Tank(width, height, resolution, slits, depth=depth, decay_factor=decay_factor)
    tank.set_boundary_type("reflective")  # Set default boundary type
    return Simulation(tank)

if __name__ == '__main__':
    app = QApplication(sys.argv)

    sides = ['bottom', 'top', 'left', 'right']
    slit_config = {}

    print("Enter the number of slits for each side (0 for no slits):")
    for side in sides:
        while True:
            try:
                num_slits = int(input(f"Number of slits on {side} side: "))
                if num_slits < 0:
                    print("Please enter a non-negative integer.")
                else:
                    slit_config[side] = num_slits
                    break
            except ValueError:
                print("Please enter a valid integer.")

    simulation = create_simulation(slit_config)

    gui = SimulationGUI(simulation)
    gui.show()
    sys.exit(app.exec_())
