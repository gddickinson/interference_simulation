// Tank page (#/tank, #/tank?setup=<slug>): the full simulator. The FDTD tank (wave_engine.js) advances one desktop
// frame (Simulation.step(0.05)) per animation frame while running; controls mirror the PyQt5 GUI in main.py.
import { route, app, esc, animate, download } from './core.js';
import { buildSetup, FRAME_DT } from './wave_engine.js';
import { loadSetup, draw, legend, fmtNum, pacer } from './ui.js';
import { renderPanel, randomElement } from './tank_panel.js';

route('tank', async (_args, query) => {
  const data = await loadSetup();
  const { controls: C, setups } = data;
  const first = setups.find(s => s.slug === query.setup) || setups[0];
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const state = { slug: first.slug, setup: first, resolution: C.resolution, colour: 'desktop', click: 'obstacle', running: !reduced };
  let sim = null, panel = null, dirty = true;

  app().innerHTML = `
    <h1 class="glow">Wave tank</h1>
    <p class="lead" id="note"></p>
    <section class="sim">
      <div class="controls" id="panel" aria-label="Simulation controls"></div>
      <div class="view">
        <canvas id="field" width="720" height="720" tabindex="0" role="img"
          aria-label="Wave field u(x, y): blue negative, white zero, red positive. Space starts or stops, R resets."></canvas>
        <div class="legend" id="legend"></div>
        <div class="readout" id="readout" aria-live="off"></div>
        <p class="small mute">Space: start/stop · R: reset · click the tank to place the element chosen under "View".</p>
      </div>
    </section>`;
  const canvas = document.getElementById('field');
  const setLegend = legend(document.getElementById('legend'));

  function rebuild(setup, slug = '') {
    state.setup = setup; state.slug = slug;
    sim = buildSetup(setup, state.resolution);
    document.getElementById('note').textContent = setup.note
      ? `${setup.name}: ${setup.note}` : 'Custom tank: slits spaced evenly along each side, as the desktop app sets them up.';
    panel = renderPanel(document.getElementById('panel'), data, state, sim, handlers);
    dirty = true;
  }

  const handlers = {
    example: slug => { const s = setups.find(x => x.slug === slug); if (s) rebuild(s, slug); },
    build: (counts, res) => { state.resolution = res; rebuild({ slits: counts }); },
    resolution: res => { state.resolution = res; rebuild(state.setup, state.slug); },
    toggle: () => { state.running = !state.running; panel.setRunning(state.running); },
    reset: () => { sim.reset(); panel.setStanding(null); dirty = true; },
    add: kind => { randomElement(kind, C, sim.tank)(); dirty = true; },
    global: (key, v) => {
      if (key === 'time_scale') sim.setTimeScale(v);
      else if (key === 'depth') sim.tank.setDepth(v);
      else sim.tank.setDecayFactor(v);
      dirty = true;
    },
    boundary: b => { sim.tank.setBoundaryType(b); dirty = true; },
    standing: m => { sim.tank.setStandingWaveMode(m); dirty = true; },
    colour: c => { state.colour = c; dirty = true; },
    click: c => { state.click = c; },
    changed: () => { dirty = true; },
    png: () => canvas.toBlob(b => download(`wave_tank_t${sim.time.toFixed(2)}.png`, b)),
  };

  canvas.addEventListener('click', e => {
    if (state.click === 'none') return;
    const r = canvas.getBoundingClientRect(), t = sim.tank;
    const x = (e.clientX - r.left) / r.width * t.width, y = (1 - (e.clientY - r.top) / r.height) * t.height;
    randomElement(state.click, C, t, [Math.min(Math.max(x, 0), t.width), Math.min(Math.max(y, 0), t.height)])();
    dirty = true;
  });
  canvas.addEventListener('keydown', e => {
    if (e.key === ' ') { e.preventDefault(); handlers.toggle(); }
    else if (e.key === 'r' || e.key === 'R') handlers.reset();
  });

  const readout = document.getElementById('readout');
  function show(range) {
    const t = sim.tank;
    let mx = 0; for (const v of t.field()) { const a = Math.abs(v); if (a > mx) mx = a; }
    const rows = [['time t', sim.time.toFixed(3)], ['wave speed c = 10 √depth', fmtNum(t.c)], ['FDTD step dt', t.dt.toExponential(3)],
      ['steps per frame', sim.stepsPerFrame(FRAME_DT)], ['grid', `${t.resolution} x ${t.resolution}`], ['max |u|', fmtNum(mx)],
      ['slits · obstacles · packets · points', `${t.slits.length} · ${t.obstacles.length} · ${t.wavePackets.length} · ${t.interferencePoints.length}`]];
    readout.innerHTML = rows.map(([k, v]) => `<div><span>${esc(k)}</span><b>${esc(v)}</b></div>`).join('');
    setLegend(range);
  }

  rebuild(first, first.slug);
  if (reduced) { for (let i = 0; i < 20; i++) sim.step(FRAME_DT); }
  const due = pacer();   // one desktop frame per 50 ms, like SimulationGUI's timer
  animate(t => {
    if (state.running && due(t)) { sim.step(FRAME_DT); dirty = true; }
    if (dirty) { show(draw(canvas, sim, state.colour)); dirty = false; }
  });
});
