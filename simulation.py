import numpy as np
import matplotlib.pyplot as plt

SIDES = ("left", "right", "bottom", "top")
SPONGE_CELLS = 10        # width of the absorbing layer ("absorbing" boundaries)
SPONGE_STRENGTH = 0.005   # damping per step at the wall (quadratic profile, zero at the inner edge)
COLOUR_PERCENTILE = 95    # Tank.colour_range: percentile of |u| that sets the plot's colour limit

class Slit:
    def __init__(self, position, width, amplitude, frequency, wavelength):
        self.position = position
        self.width = width
        self.amplitude = amplitude
        self.frequency = frequency
        self.wavelength = wavelength
        # The incoming wave's direction is fixed by the wall the slit sits on (see Tank.update)

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
        self.time = 0.0

    def update_distance_map(self):
        self.distance_map.fill(np.inf)
        for slit in self.slits:
            x, y = slit.position
            slit_distances = np.sqrt((self.X - x)**2 + (self.Y - y)**2)
            self.distance_map = np.minimum(self.distance_map, slit_distances)
        if not self.slits:
            # No slits: no distance-based decay (inf / inf used to make the whole field NaN)
            self.distance_map.fill(0)
            return
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
        else:
            # "absorbing" and "open": only apply obstacle boundaries (the walls get absorbing conditions below).
            # Obstacles must block waves in both modes.
            obstacle_mask = self.boundary[1:-1, 1:-1].copy()
            obstacle_mask[0, :] = 1
            obstacle_mask[-1, :] = 1
            obstacle_mask[:, 0] = 1
            obstacle_mask[:, -1] = 1
            u_next *= obstacle_mask

        self.u_prev = self.u.copy()
        self.u[1:-1, 1:-1] = u_next
        if self.boundary_type == "open":
            self.apply_mur(SIDES)
        elif self.boundary_type == "absorbing":
            # Graded sponge layer on the walls without slits (so it never damps a slit or the wave it sends into the
            # tank), plus the Mur condition on every wall. Applied before the sources are set.
            self.apply_sponge([side for side in SIDES if side not in self.slit_walls()])
            self.apply_mur(SIDES)

        # Generate new waves at slits
        for slit in self.slits:
            x, y = slit.position
            x_idx, y_idx = int(x / self.dx), int(y / self.dy)
            slit_width = max(1, int(slit.width / self.dx))

            if x_idx == 0:  # Left side
                x_range = slice(0, 3)
                y_range = slice(max(0, y_idx - slit_width//2), min(self.resolution, y_idx + slit_width//2 + 1))
                depth = self.X[y_range, x_range]  # distance into the tank along the wave's direction (+x)
            elif x_idx == self.resolution - 1:  # Right side
                x_range = slice(self.resolution - 3, self.resolution)
                y_range = slice(max(0, y_idx - slit_width//2), min(self.resolution, y_idx + slit_width//2 + 1))
                depth = self.width - self.X[y_range, x_range]  # (-x)
            elif y_idx == 0:  # Bottom side
                x_range = slice(max(0, x_idx - slit_width//2), min(self.resolution, x_idx + slit_width//2 + 1))
                y_range = slice(0, 3)
                depth = self.Y[y_range, x_range]  # (+y)
            elif y_idx == self.resolution - 1:  # Top side
                x_range = slice(max(0, x_idx - slit_width//2), min(self.resolution, x_idx + slit_width//2 + 1))
                y_range = slice(self.resolution - 3, self.resolution)
                depth = self.height - self.Y[y_range, x_range]  # (-y)
            else:
                continue  # Skip if slit is not on the edge

            # Prescribed (hard) source: the slit cells oscillate with amplitude A, as in a ripple tank's dipper. All
            # slits on a wall are fed by the same plane wave travelling into the tank, so the phase depends only on
            # the distance from the wall along that direction (slits on one wall are in phase).
            slit_wave = slit.amplitude * np.sin(2 * np.pi * (slit.frequency * time - depth / slit.wavelength))
            self.u[y_range, x_range] = slit_wave

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
            packet_wave = amplitude * np.sin(2 * np.pi * (frequency * time - distance / wavelength))

            # Prescribed oscillation weighted by the Gaussian envelope (1 at the centre line, fading to the free field)
            self.u[y_range, x_range] = (1 - gaussian) * self.u[y_range, x_range] + gaussian * packet_wave

        # Generate interference points
        for point in self.interference_points:
            x, y = point['position']
            amplitude = point['amplitude']
            frequency = point['frequency']
            x_idx, y_idx = int(x / self.dx), int(y / self.dy)
            self.u[y_idx, x_idx] = amplitude * np.sin(2 * np.pi * frequency * time)

        # The standing wave is superposed on the displayed field (see field()), not accumulated into u
        self.time = time


    def slit_walls(self):
        """The walls ('left', 'right', 'bottom', 'top') that carry at least one slit."""
        walls = set()
        for slit in self.slits:
            x_idx, y_idx = int(slit.position[0] / self.dx), int(slit.position[1] / self.dy)
            if x_idx == 0:
                walls.add("left")
            elif x_idx == self.resolution - 1:
                walls.add("right")
            elif y_idx == 0:
                walls.add("bottom")
            elif y_idx == self.resolution - 1:
                walls.add("top")
        return walls

    def apply_sponge(self, sides):
        """Damp u and u_prev in a SPONGE_CELLS-wide layer along the given walls, smoothly (quadratic profile, strongest
        at the wall) so the layer itself does not reflect."""
        n = SPONGE_CELLS
        factor = 1 - SPONGE_STRENGTH * ((n - np.arange(n)) / n) ** 2  # index 0 = at the wall
        for arr in (self.u, self.u_prev):
            if "bottom" in sides:
                arr[:n, :] *= factor[:, np.newaxis]
            if "top" in sides:
                arr[-n:, :] *= factor[::-1, np.newaxis]
            if "left" in sides:
                arr[:, :n] *= factor[np.newaxis, :]
            if "right" in sides:
                arr[:, -n:] *= factor[np.newaxis, ::-1]

    def apply_mur(self, sides):
        """First-order Mur (Engquist-Majda) absorbing condition on the given walls: the wall cells take the value
        that lets a wave leave at normal incidence without reflection. Uses u at time n (u_prev, just saved) and the
        freshly updated interior at n+1 (u)."""
        old, new = self.u_prev, self.u
        kx = (self.c * self.dt - self.dx) / (self.c * self.dt + self.dx)
        ky = (self.c * self.dt - self.dy) / (self.c * self.dt + self.dy)
        if "left" in sides:
            new[1:-1, 0] = old[1:-1, 1] + kx * (new[1:-1, 1] - old[1:-1, 0])
        if "right" in sides:
            new[1:-1, -1] = old[1:-1, -2] + kx * (new[1:-1, -2] - old[1:-1, -1])
        if "bottom" in sides:
            new[0, 1:-1] = old[1, 1:-1] + ky * (new[1, 1:-1] - old[0, 1:-1])
        if "top" in sides:
            new[-1, 1:-1] = old[-2, 1:-1] + ky * (new[-2, 1:-1] - old[-1, 1:-1])

    def standing_wave(self):
        """Standing-wave mode m at the current time: 0.5 sin(m pi x / W) sin(2 pi t) (zeros if no mode)."""
        if self.standing_wave_mode is None:
            return np.zeros_like(self.u)
        mode = self.standing_wave_mode
        amplitude = 0.5
        return amplitude * np.sin(mode * np.pi * self.X / self.width) * np.sin(2 * np.pi * self.time)

    def field(self):
        """The displayed wave field: propagating waves u plus the superposed standing-wave mode."""
        if self.standing_wave_mode is None:
            return self.u
        return self.u + self.standing_wave()

    def source_amplitude(self):
        """The largest source amplitude (1 if there are no sources); the field stays of this order."""
        amps = [s.amplitude for s in self.slits] + [p['amplitude'] for p in self.wave_packets]
        amps += [p['amplitude'] for p in self.interference_points]
        if self.standing_wave_mode is not None:
            amps.append(0.5)
        return max(amps) if amps and max(amps) > 0 else 1

    def colour_range(self, percentile=COLOUR_PERCENTILE):
        """Symmetric colour limit for plotting: a high percentile of |field| (the prescribed source cells are much
        stronger than the waves they radiate, so a +-amplitude range would show only the sources), but at least 1 %
        of the largest source amplitude so an almost empty tank is not shown as noise."""
        return float(max(np.percentile(np.abs(self.field()), percentile), 0.01 * self.source_amplitude()))

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
        self.time = 0.0

    def plot(self, ax):
        vmax = self.colour_range()  # +- 95th percentile of |u| (see colour_range)
        vmin = -vmax
        im = ax.imshow(self.field(), cmap='seismic', animated=True,
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
