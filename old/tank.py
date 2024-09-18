import matplotlib
matplotlib.use('Qt5Agg')

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
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

class Tank:
    def __init__(self, radius, resolution, slits, viscosity=0.1, depth=1):
        self.radius = radius
        self.resolution = resolution
        self.slits = slits
        self.viscosity = viscosity
        self.depth = depth

        self.x = np.linspace(-radius, radius, resolution)
        self.y = np.linspace(-radius, radius, resolution)
        self.X, self.Y = np.meshgrid(self.x, self.y)
        self.Z = np.zeros((resolution, resolution))

    def update(self, time):
        self.Z.fill(0)
        for slit in self.slits:
            if slit.is_open:
                distances = np.sqrt((self.X - slit.position[0])**2 + (self.Y - slit.position[1])**2)
                self.Z += slit.generate_wave(distances, time)

        # Apply circular mask
        mask = self.X**2 + self.Y**2 <= self.radius**2
        self.Z *= mask

        # Apply viscosity and depth effects (simplified)
        self.Z *= np.exp(-self.viscosity * time)
        self.Z *= np.sqrt(self.depth)

    def plot(self, ax):
        im = ax.imshow(self.Z, cmap='coolwarm', animated=True,
                       extent=[-self.radius, self.radius, -self.radius, self.radius],
                       vmin=-2, vmax=2)  # Set fixed color scale
        return im

class Simulation:
    def __init__(self, tank):
        self.tank = tank
        self.time = 0

    def step(self, dt):
        self.time += dt
        self.tank.update(self.time)

def create_animation(simulation, interval=50, frames=200):
    fig, ax = plt.subplots()
    im = simulation.tank.plot(ax)

    def update(frame):
        simulation.step(interval/1000)  # Convert interval to seconds
        im.set_array(simulation.tank.Z)
        return [im]

    try:
        anim = FuncAnimation(fig, update, frames=frames, interval=interval, blit=True)
        return anim, fig
    except Exception as e:
        logging.error(f"Error creating animation: {e}")
        return None, fig

if __name__ == "__main__":
    try:
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

        anim, fig = create_animation(simulation, interval=50, frames=200)
        if anim is not None:
            plt.colorbar(fig.gca().images[0])  # Add colorbar
            plt.show()
        else:
            logging.warning("Animation creation failed. Displaying static plot instead.")
            simulation.tank.plot(fig.gca())
            plt.colorbar(fig.gca().images[0])  # Add colorbar
            plt.show()
    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        plt.show()
