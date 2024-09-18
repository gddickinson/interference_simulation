import numpy as np
import matplotlib.pyplot as plt

class Slit:
    def __init__(self, position, width, amplitude, frequency, wavelength):
        self.position = position
        self.width = width
        self.amplitude = amplitude
        self.frequency = frequency
        self.wavelength = wavelength
        # Determine direction based on position
        x, y = position
        if x == 0:  # Left side
            self.direction = (1, 0)
        elif x == 20:  # Right side
            self.direction = (-1, 0)
        elif y == 0:  # Bottom side
            self.direction = (0, 1)
        elif y == 20:  # Top side
            self.direction = (0, -1)
        else:
            self.direction = (0, 1)  # Default to upward if not on an edge

class Obstacle:
    def __init__(self, position, radius):
        self.position = position
        self.radius = radius
        self.boundary_type = "reflective"  # Can be "reflective", "absorbing", or "open"


class Tank:
    def __init__(self, width, height, resolution, slits, depth=1.0, decay_factor=0.999):
        self.width = width
        self.height = height
        self.resolution = resolution
        self.slits = slits
        self.obstacles = []
        self.depth = depth
        self.decay_factor = decay_factor
        self.boundary_type = "reflective"

        self.dx = width / (resolution - 1)
        self.dy = height / (resolution - 1)
        self.c = 10 * np.sqrt(self.depth)  # Wave speed depends on depth
        self.dt = 0.05 * min(self.dx, self.dy) / self.c

        self.x = np.linspace(0, width, resolution)
        self.y = np.linspace(0, height, resolution)
        self.X, self.Y = np.meshgrid(self.x, self.y)

        self.u = np.zeros((resolution, resolution))
        self.u_prev = np.zeros((resolution, resolution))

        self.boundary = np.ones((resolution, resolution))
        self.update_boundary()

        # Create distance map from slits
        self.distance_map = np.ones((resolution, resolution)) * np.inf
        self.update_distance_map()

        self.wave_packets = []
        self.interference_points = []
        self.standing_wave_mode = None

    def update_distance_map(self):
        self.distance_map.fill(np.inf)
        for slit in self.slits:
            x, y = slit.position
            slit_distances = np.sqrt((self.X - x)**2 + (self.Y - y)**2)
            self.distance_map = np.minimum(self.distance_map, slit_distances)
        # Normalize distance map
        self.distance_map /= np.max(self.distance_map)

    def update_boundary(self):
        self.boundary.fill(1)
        # Set tank boundaries
        self.boundary[0, :] = 0
        self.boundary[-1, :] = 0
        self.boundary[:, 0] = 0
        self.boundary[:, -1] = 0

        # Set obstacles
        for obstacle in self.obstacles:
            mask = (self.X - obstacle.position[0])**2 + (self.Y - obstacle.position[1])**2 <= obstacle.radius**2
            self.boundary[mask] = 0

    def update(self, time):
        # FDTD update with depth consideration
        laplacian = (
            (self.u[1:-1, 2:] + self.u[1:-1, :-2] - 2 * self.u[1:-1, 1:-1]) / self.dx**2 +
            (self.u[2:, 1:-1] + self.u[:-2, 1:-1] - 2 * self.u[1:-1, 1:-1]) / self.dy**2
        )

        u_next = (2 * self.u[1:-1, 1:-1] - self.u_prev[1:-1, 1:-1] +
                  self.c**2 * self.dt**2 * laplacian)

        # Apply distance-based decay factor
        decay = 1 - (1 - self.decay_factor) * self.distance_map[1:-1, 1:-1]
        u_next *= decay

        # Apply boundary conditions
        if self.boundary_type == "reflective":
            u_next *= self.boundary[1:-1, 1:-1]
        elif self.boundary_type == "absorbing":
            # Only apply obstacle boundaries, allow waves to be absorbed at edges
            obstacle_mask = self.boundary[1:-1, 1:-1].copy()
            obstacle_mask[0, :] = 1
            obstacle_mask[-1, :] = 1
            obstacle_mask[:, 0] = 1
            obstacle_mask[:, -1] = 1
            u_next *= obstacle_mask
        # For "open" boundaries, we don't apply any additional conditions here

        self.u_prev = self.u.copy()
        self.u[1:-1, 1:-1] = u_next

        # Generate new waves at slits
        for slit in self.slits:
            x, y = slit.position
            x_idx, y_idx = int(x / self.dx), int(y / self.dy)
            slit_width = max(1, int(slit.width / self.dx))

            if x_idx == 0:  # Left side
                x_range = slice(0, 3)
                y_range = slice(max(0, y_idx - slit_width//2), min(self.resolution, y_idx + slit_width//2 + 1))
            elif x_idx == self.resolution - 1:  # Right side
                x_range = slice(self.resolution - 3, self.resolution)
                y_range = slice(max(0, y_idx - slit_width//2), min(self.resolution, y_idx + slit_width//2 + 1))
            elif y_idx == 0:  # Bottom side
                x_range = slice(max(0, x_idx - slit_width//2), min(self.resolution, x_idx + slit_width//2 + 1))
                y_range = slice(0, 3)
            elif y_idx == self.resolution - 1:  # Top side
                x_range = slice(max(0, x_idx - slit_width//2), min(self.resolution, x_idx + slit_width//2 + 1))
                y_range = slice(self.resolution - 3, self.resolution)
            else:
                continue  # Skip if slit is not on the edge

            slit_wave = slit.amplitude * np.sin(2 * np.pi * (slit.frequency * time - self.X[y_range, x_range] / slit.wavelength))
            self.u[y_range, x_range] += slit_wave

        # Generate wave packets
        for packet in self.wave_packets:
            x, y = packet['position']
            amplitude = packet['amplitude']
            frequency = packet['frequency']
            wavelength = packet['wavelength']
            width = packet['width']
            direction = packet['direction']

            x_range = slice(max(0, int((x - width) / self.dx)), min(self.resolution, int((x + width) / self.dx)))
            y_range = slice(max(0, int((y - width) / self.dy)), min(self.resolution, int((y + width) / self.dy)))

            distance = (self.X[y_range, x_range] - x) * direction[0] + (self.Y[y_range, x_range] - y) * direction[1]
            gaussian = np.exp(-(distance**2) / (2 * width**2))
            packet_wave = amplitude * np.sin(2 * np.pi * (frequency * time - distance / wavelength)) * gaussian

            self.u[y_range, x_range] += packet_wave

        # Generate interference points
        for point in self.interference_points:
            x, y = point['position']
            amplitude = point['amplitude']
            frequency = point['frequency']
            x_idx, y_idx = int(x / self.dx), int(y / self.dy)
            self.u[y_idx, x_idx] += amplitude * np.sin(2 * np.pi * frequency * time)

        # Generate standing wave
        if self.standing_wave_mode is not None:
            mode = self.standing_wave_mode
            amplitude = 0.5  # Adjust as needed
            standing_wave = amplitude * np.sin(mode * np.pi * self.X / self.width) * np.sin(2 * np.pi * time)
            self.u += standing_wave

        # Handle boundary conditions
        if self.boundary_type == "open":
            # Do nothing, allowing waves to pass through edges unaffected
            pass
        elif self.boundary_type == "absorbing":
            # Gradual absorption at edges
            edge_width = 10
            edge_factor = np.linspace(0, 1, edge_width)[:, np.newaxis]

            self.u[:edge_width, :] *= edge_factor
            self.u[-edge_width:, :] *= edge_factor[::-1]
            self.u[:, :edge_width] *= edge_factor.T
            self.u[:, -edge_width:] *= edge_factor[::-1].T


    def add_obstacle(self, obstacle):
        self.obstacles.append(obstacle)
        self.update_boundary()

    def set_boundary_type(self, boundary_type):
        if boundary_type in ["reflective", "absorbing", "open"]:
            self.boundary_type = boundary_type
        else:
            raise ValueError("Invalid boundary type. Choose 'reflective', 'absorbing', or 'open'.")

    def set_depth(self, depth):
        self.depth = depth
        self.c = 10 * np.sqrt(self.depth)  # Update wave speed
        self.dt = 0.05 * min(self.dx, self.dy) / self.c  # Update time step

    def set_decay_factor(self, decay_factor):
        self.decay_factor = decay_factor

    def add_wave_packet(self, position, amplitude, frequency, wavelength, width, direction):
        self.wave_packets.append({
            'position': position,
            'amplitude': amplitude,
            'frequency': frequency,
            'wavelength': wavelength,
            'width': width,
            'direction': direction
        })

    def add_interference_point(self, position, amplitude, frequency):
        self.interference_points.append({
            'position': position,
            'amplitude': amplitude,
            'frequency': frequency
        })

    def set_standing_wave_mode(self, mode):
        self.standing_wave_mode = mode

    def reset(self):
        self.u.fill(0)
        self.u_prev.fill(0)
        self.update_boundary()
        self.update_distance_map()
        self.wave_packets.clear()
        self.interference_points.clear()
        self.standing_wave_mode = None

    def plot(self, ax):
        vmin, vmax = -1, 1  # Fixed scale for better contrast
        im = ax.imshow(self.u, cmap='seismic', animated=True,
                       extent=[0, self.width, 0, self.height],
                       vmin=vmin, vmax=vmax, origin='lower')
        # Add markers for slits
        for slit in self.slits:
            ax.plot(slit.position[0], slit.position[1], 'ko', markersize=5)
        # Add circles for obstacles
        for obstacle in self.obstacles:
            circle = plt.Circle(obstacle.position, obstacle.radius, color='black', fill=False)
            ax.add_artist(circle)
        ax.set_xlim(0, self.width)
        ax.set_ylim(0, self.height)
        return im
class Simulation:
    def __init__(self, tank):
        self.tank = tank
        self.time = 0
        self.time_scale = 1

    def step(self, dt):
        steps = max(1, int(dt / self.tank.dt))
        for _ in range(steps):
            self.time += self.tank.dt * self.time_scale
            self.tank.update(self.time)

    def set_time_scale(self, scale):
        self.time_scale = scale

    def reset(self):
        self.time = 0
        self.tank.reset()
