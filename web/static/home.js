// Home page: hero with a live two-source tank, counts from the API, entry cards.
import { route, api, app, esc, list, animate } from './core.js';
import { buildSetup, FRAME_DT } from './wave_engine.js';
import { loadSetup, draw, pacer } from './ui.js';

const DOORS = [
  ['#/tank', 'Wave tank', 'The full simulator: slits on any side, depth, decay, time scale, boundary type, standing-wave modes, obstacles, wave packets and interference points.'],
  ['#/examples', 'Examples', 'Six ready-made set-ups, each running live in a small tank. Click one to open it in the simulator.'],
  ['#/check', 'Cross-check', 'The browser engine against the Python simulation.py: the same set-ups computed by NumPy, compared value by value.'],
  ['#/about', 'About', 'The physics and numerics, what each control does (and the model\'s quirks), how to run the desktop and web apps.'],
];

route('home', async () => {
  const [info, { setups }] = await Promise.all([api('/info'), loadSetup()]);
  app().innerHTML = `
  <section class="hero two herotank">
    <div>
      <p class="kicker">Slits · obstacles · FDTD · interference</p>
      <h1 class="glow">Wave Interference Simulation</h1>
      <p class="lead">${esc(info.description)} The tank runs in your browser, ported line by line from the Python /
      PyQt5 desktop app.</p>
      <a class="btn" href="#/tank">Open the wave tank</a><a class="btn alt" href="#/examples">See the examples</a>
    </div>
    <figure class="fig"><canvas id="hero" width="480" height="480" role="img" aria-label="Live simulation: interference of waves from two slits on the bottom edge"></canvas>
      <figcaption class="small mute" id="herocap"></figcaption></figure>
  </section>
  <div class="tiles">
    <div class="tile"><b>${info.tank[0]} × ${info.tank[1]}</b><span>tank size</span></div>
    <div class="tile"><b>${info.resolution}²</b><span>grid points (desktop)</span></div>
    <div class="tile"><b>${info.boundary_types}</b><span>boundary types</span></div>
    <div class="tile"><b>${info.standing_modes}</b><span>standing-wave modes</span></div>
    <div class="tile"><b>${info.controls}</b><span>sliders</span></div>
    <div class="tile"><b>${info.setups}</b><span>example set-ups</span></div>
  </div>
  <div class="grid wide">${list(DOORS, ([href, t, d]) => `<a class="card door" href="${href}"><b>${t}</b><span>${d}</span></a>`)}</div>
  <h2>Example set-ups</h2>
  <p>${list(setups, s => `<a class="tag a" href="#/tank?setup=${s.slug}">${esc(s.name)}</a>`)}</p>`;
  hero(setups[0]);
});

// Two bottom slits at a 120 x 120 grid, one desktop frame per 50 ms; starts over every CYCLE frames so the
// interference fan stays visible (later the reflections from the walls fill the tank).
const CYCLE = 50;
function hero(setup) {
  const canvas = document.getElementById('hero'), sim = buildSetup(setup, 120);
  document.getElementById('herocap').textContent = `${setup.name}, 120 × 120 grid, restarting every ${CYCLE * 0.05} s of animation; colours -1 (blue) to +1 (red) as in the desktop plot`;
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    for (let i = 0; i < 40; i++) sim.step(FRAME_DT);
    draw(canvas, sim); return;
  }
  const due = pacer();
  let frame = 0;
  animate(t => {
    if (!due(t)) return;
    if (++frame > CYCLE) { sim.reset(); frame = 0; }
    sim.step(FRAME_DT); draw(canvas, sim);
  });
}
