# Wave Interference Simulation

## Overview

This project is an interactive simulation of wave phenomena, focusing on interference patterns in a 2D environment. It provides a visual representation of various wave behaviors, including reflection, absorption, diffraction, and interference. The simulation is built using Python and PyQt5 for the graphical user interface, with matplotlib for rendering the wave field.

## Features

- Real-time simulation of wave propagation and interference
- Multiple wave sources (slits) with adjustable properties
- Various boundary conditions: reflective, absorbing, and open
- Addition of obstacles to observe diffraction and reflection
- Generation of wave packets and interference points
- Standing wave mode visualization
- Adjustable global parameters: time scale, depth, and decay factor

## Installation

1. Clone this repository:
git clone https://github.com/yourusername/wave-interference-simulation.git

2. Install the required dependencies:
pip install numpy matplotlib PyQt5

3. Run the simulation:
python main.py

## Usage Instructions

1. **Starting the Simulation**: Upon launching, you'll be prompted to enter the number of slits for each side of the tank. After setup, click the "Start" button to begin the simulation.

2. **Adjusting Global Parameters**:
- Use the "Time Scale" slider to speed up or slow down the simulation.
- The "Depth" slider adjusts the simulated water depth, affecting wave speed.
- "Wave Decay" controls how quickly waves dissipate over distance.

3. **Boundary Conditions**: Select between "Reflective", "Absorbing", or "Open" boundaries using the dropdown menu.

4. **Slit Controls**: Each slit has individual controls for amplitude, wavelength, frequency, and width.

5. **Adding Elements**:
- Click "Add Obstacle" to place a random circular obstacle in the tank.
- "Add Wave Packet" creates a localized wave disturbance.
- "Add Interference Point" places a point source of waves.

6. **Standing Waves**: Select a standing wave mode from the dropdown to visualize different harmonic patterns.

7. **Reset**: The "Reset" button clears all waves and returns the simulation to its initial state.

## Mathematical Background

The simulation is based on the 2D wave equation:

∂²u/∂t² = c²(∂²u/∂x² + ∂²u/∂y²)

Where:
- u is the wave amplitude
- t is time
- c is the wave speed
- x and y are spatial coordinates

We use the Finite-Difference Time-Domain (FDTD) method to numerically solve this equation. The discretized update equation is:

u(t+Δt) = 2u(t) - u(t-Δt) + c²Δt²(∂²u/∂x² + ∂²u/∂y²)

Key aspects of the simulation:

1. **Wave Speed**: c = √(gh), where g is gravity and h is water depth.
2. **Boundary Conditions**:
- Reflective: u = 0 at boundaries
- Absorbing: Gradual dampening near edges
- Open: Waves pass through unaffected
3. **Wave Sources**: Sinusoidal oscillations with adjustable amplitude, frequency, and wavelength.
4. **Obstacles**: Implemented as regions where u = 0.
5. **Wave Packets**: Gaussian-enveloped sinusoidal waves.
6. **Standing Waves**: Superposition of waves traveling in opposite directions, creating nodes and antinodes.

## Contributing

Contributions to improve the simulation or add new features are welcome. Please fork the repository and submit a pull request with your changes.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- This simulation was inspired by various wave optics and fluid dynamics principles.
- Special thanks to the PyQt5 and matplotlib commun
