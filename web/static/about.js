// About page: the model as implemented in simulation.py, the controls (from /api/controls), running the apps, credits.
import { route, app, esc, list } from './core.js';
import { loadSetup } from './ui.js';

const HELP = {
  time_scale: 'Multiplies the time the sources see each step (time += dt × scale). Wave propagation per step is unchanged, so this changes how fast the sources oscillate relative to the waves.',
  depth: 'Water depth h; wave speed c = 10 √h. The FDTD step dt = 0.05 · dx / c shrinks as c grows, so a deeper tank takes more steps per frame and waves cross it faster on screen.',
  decay_factor: 'Damping per step, strongest far from the slits: u is multiplied by 1 − (1 − factor) × (distance to nearest slit / largest such distance).',
  amplitude: 'Amplitude of the slit source.', wavelength: 'λ in the source term sin(2π(f t − d/λ)).',
  frequency: 'f in the source term.', width: 'Width of the slit opening (rounded down to whole grid cells, at least one).',
};

route('about', async () => {
  const { controls: C } = await loadSetup();
  app().innerHTML = `
  <h1 class="glow">About</h1>
  <p class="lead">An interactive simulation of wave phenomena in a 2D tank: interference, reflection, absorption and
  diffraction. The original is a Python desktop app (PyQt5 GUI, matplotlib plot, NumPy solver); this web version runs
  a JavaScript port of the same solver (<code>simulation.py</code>) in the browser.</p>

  <h2>The model</h2>
  <p>The tank solves the 2D wave equation</p>
  <p class="eq">∂²u/∂t² = c² (∂²u/∂x² + ∂²u/∂y²)</p>
  <p>with the finite-difference time-domain (FDTD) update</p>
  <p class="eq">u(t+Δt) = 2u(t) − u(t−Δt) + c²Δt² ∇²u</p>
  <p>on a ${C.tank[0]} × ${C.tank[1]} tank with ${C.resolution} × ${C.resolution} grid points in the desktop app.
  Each frame of the desktop animation (a 50 ms timer) advances the simulation by ${C.frame_dt} time units, split into
  as many FDTD steps as fit. The colour map is matplotlib's <i>seismic</i> (blue negative, red positive), scaled each frame to ± the 95th
  percentile of |u|: the prescribed source cells are much stronger than the waves they radiate, so a scale set by
  the source amplitude would show little more than the slits.</p>
  <ul>
    <li><b>Slits</b> sit on the tank walls, spaced evenly along each side. They are prescribed (hard) sources, as
      the dipper of a ripple tank: every step the cells of the opening (three cells deep) are set to
      A·sin(2π(f t − d/λ)), where d is the distance from the wall into the tank: every slit on a wall is fed by the
      same plane wave, so slits on one wall are in phase.</li>
    <li><b>Obstacles</b> are discs where u is held at 0.</li>
    <li><b>Wave packets</b> drive a sinusoid travelling along a direction around a point, blended into the field
      with a Gaussian weight (fully prescribed on the centre line, untouched far from it).</li>
    <li><b>Interference points</b> hold a single grid point at A·sin(2π f t).</li>
    <li><b>Standing-wave modes</b> 1 to 5 superpose 0.5·sin(mπx/W)·sin(2πt) on the displayed field.</li>
    <li><b>Boundaries</b>: <i>reflective</i> holds u = 0 on the walls; <i>open</i> makes the walls transparent with the
      first-order Mur (Engquist–Majda) absorbing condition; <i>absorbing</i> adds a graded damping layer 6 units wide
      (quadratic profile, rate 2 per unit time at the wall; dashed line on the Tank page) along the walls that carry
      no slits, so slits keep their full strength. Measured against a pulse in a much larger tank, open walls
      reflect about 0.1 % of its energy and absorbing walls about 0.02 %.</li>
  </ul>
  <div class="callout"><b>Things worth knowing when you read the picture.</b>
    <ul>
      <li>Because sources are prescribed, |u| stays of the order of the source amplitude. The colour scale follows
        the field (95th percentile of |u|), so the cells right at the sources are saturated; choose "± largest
        source amplitude" on the Tank page to see them unsaturated.</li>
      <li>Reset clears the waves, packets, interference points and standing mode; obstacles stay.</li>
    </ul></div>

  <h2>Controls</h2>
  <div class="scroll"><table><tr><th>Control</th><th>Slider range</th><th>Value</th><th>What it does</th></tr>
  ${list(Object.entries(C.specs), ([k, s]) => `<tr><td>${esc(s.label)}${C.slit.includes(k) ? ' (per slit)' : ''}</td>
    <td class="mono">${s.min}–${s.max}</td><td class="mono">slider / ${s.scale}</td><td>${esc(HELP[k] || '')}</td></tr>`)}
  </table></div>
  <p>Also: boundary type (${esc(C.boundaries.join(', '))}), standing-wave mode (${esc(C.standing_modes.join(', '))}),
  Start/Stop, Reset, Add Obstacle, Add Wave Packet and Add Interference Point (random position and parameters, as in
  the desktop app). The web version adds a choice of grid size, an automatic colour range, click-to-place, example
  set-ups and PNG export.</p>

  <h2>Run it yourself</h2>
  <h3>Desktop app</h3>
  <pre>git clone https://github.com/gddickinson/interference_simulation.git
cd interference_simulation
pip install numpy matplotlib PyQt5
python main.py      # asks for the number of slits on each side, then click Start</pre>
  <h3>Web app</h3>
  <pre>pip install -r requirements-web.txt
python run_web.py   # http://127.0.0.1:8230</pre>
  <p>Tests: <code>python -m pytest -q tests</code> (includes the node test of the browser engine against the Python
  solver).</p>

  <h2>Credits</h2>
  <p>Wave Interference Simulation by George Dickinson, MIT License. Inspired by wave optics and fluid dynamics
  principles; built with PyQt5, matplotlib and NumPy. Web interface and JavaScript port added with Claude Code.
  <a href="https://github.com/gddickinson/interference_simulation">Source on GitHub</a>.</p>`;
});
