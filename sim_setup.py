"""Qt-free set-up shared by the desktop GUI (main.py) and the web interface (web/app.py).

- create_simulation(slit_config, ...): builds the 20 x 20 tank with evenly spaced slits on each side (moved here
  unchanged from main.py so the web app can import it without PyQt5).
- CONTROL_SPECS: the desktop sliders (integer range, default, scale) so both front ends use the same ranges.
- BOUNDARY_TYPES, STANDING_WAVE_MODES, SIDES: the choices offered by the desktop GUI.
- RANDOM_RANGES: the uniform ranges main.py draws from for "Add Obstacle / Wave Packet / Interference Point".
"""
from simulation import Slit, Tank, Simulation

SIDES = ['bottom', 'top', 'left', 'right']
BOUNDARY_TYPES = ["Reflective", "Absorbing", "Open"]
STANDING_WAVE_MODES = ["None", "1", "2", "3", "4", "5"]

# Slider specs: key -> (label, min, max, scale). The physical value is slider_value / scale; the default slider
# position is int(value * scale) of the current tank/slit value (as in SimulationGUI.initUI).
CONTROL_SPECS = {
    'time_scale': ('Time Scale', 1, 200, 100),
    'depth': ('Depth', 1, 100, 10),
    'decay_factor': ('Wave Decay', 900, 1000, 1000),
    'amplitude': ('Amplitude', 0, 200, 10),
    'wavelength': ('Wavelength', 1, 200, 10),
    'frequency': ('Frequency', 1, 200, 100),
    'width': ('Width', 1, 100, 100),
}
GLOBAL_CONTROLS = ['time_scale', 'depth', 'decay_factor']
SLIT_CONTROLS = ['amplitude', 'wavelength', 'frequency', 'width']

TANK_SIZE = (20, 20)
RESOLUTION = 200
SLIT_DEFAULTS = dict(width=0.5, amplitude=10, frequency=1, wavelength=2)

# Uniform ranges used by SimulationGUI.add_obstacle / add_wave_packet / add_interference_point.
RANDOM_RANGES = {
    'obstacle': {'radius': (0.5, 2)},
    'wave_packet': {'amplitude': (0.5, 2), 'frequency': (0.5, 2), 'wavelength': (1, 5), 'width': (1, 3),
                    'direction': (-1, 1)},
    'interference_point': {'amplitude': (0.5, 2), 'frequency': (0.5, 2)},
}


def slit_positions(slit_config, width=TANK_SIZE[0], height=TANK_SIZE[1]):
    """(x, y) of every slit for {side: count}, evenly spaced along each side, in the order create_simulation adds them."""
    out = []
    for side, num_slits in slit_config.items():
        for i in range(num_slits):
            if side == 'bottom':
                out.append((width * (i + 1) / (num_slits + 1), 0))
            elif side == 'top':
                out.append((width * (i + 1) / (num_slits + 1), height))
            elif side == 'left':
                out.append((0, height * (i + 1) / (num_slits + 1)))
            elif side == 'right':
                out.append((width, height * (i + 1) / (num_slits + 1)))
    return out


def create_simulation(slit_config, depth=1.0, decay_factor=0.999, resolution=RESOLUTION):
    width, height = TANK_SIZE
    slits = [Slit((x, y), **SLIT_DEFAULTS) for x, y in slit_positions(slit_config, width, height)]
    tank = Tank(width, height, resolution, slits, depth=depth, decay_factor=decay_factor)
    tank.set_boundary_type("reflective")  # Set default boundary type
    return Simulation(tank)
