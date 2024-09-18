import numpy as np

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
    def __init__(self, position, width):
        self.position = position  # (x, y) tuple
        self.width = width
        self.wave = Wave(1, 5, 0.5)  # Default wave

    def set_wave(self, wave):
        self.wave = wave

    def generate_wave(self, distance, time):
        return self.wave.value_at(distance, time)

class Tank:
    def __init__(self, radius, resolution, slits):
        self.radius = radius
        self.resolution = resolution
        self.slits = slits

        self.x = np.linspace(-radius, radius, resolution)
        self.y = np.linspace(-radius, radius, resolution)
        self.X, self.Y = np.meshgrid(self.x, self.y)
        self.Z = np.zeros((resolution, resolution))

    def update(self, time):
        self.Z.fill(0)
        for slit in self.slits:
            distances = np.sqrt((self.X - slit.position[0])**2 + (self.Y - slit.position[1])**2)
            self.Z += slit.generate_wave(distances, time)

        # Apply circular mask
        mask = self.X**2 + self.Y**2 <= self.radius**2
        self.Z *= mask

    def plot(self, ax):
        im = ax.imshow(self.Z, cmap='coolwarm', animated=True,
                       extent=[-self.radius, self.radius, -self.radius, self.radius],
                       vmin=-2, vmax=2)  # Set fixed color scale
        # Add markers for slits
        for slit in self.slits:
            ax.plot(slit.position[0], slit.position[1], 'ko', markersize=10)
        return im

class Simulation:
    def __init__(self, tank):
        self.tank = tank
        self.time = 0

    def step(self, dt):
        self.time += dt
        self.tank.update(self.time)
