// Cross-check page (#/check): each example set-up run by the Python simulation.py (on the server, or exported at build
// time for the static site) and by the browser engine, drawn side by side with the largest difference.
import { route, api, app, esc, list } from './core.js';
import { buildSetup, FRAME_DT } from './wave_engine.js';
import { loadSetup, decodeF64, fmtNum } from './ui.js';
import { drawField } from './wave_render.js';
import { describe } from './examples.js';

route('check', async () => {
  const { setups } = await loadSetup();
  app().innerHTML = `
    <h1 class="glow">Cross-check: browser vs Python</h1>
    <p class="lead">For every example set-up the Python <code>Tank</code> / <code>Simulation</code> classes
    (simulation.py, NumPy) and the browser engine (wave_engine.js) run the same number of desktop frames. Left: the
    Python field; right: the browser field; below: the largest difference relative to the largest |u|.</p>
    <div class="grid wide" id="pairs">${list(setups, s => `
      <div class="card"><b>${esc(s.name)}</b><small>${esc(describe(s))}</small>
        <div class="pair"><figure><canvas width="240" height="240" id="py-${s.slug}" role="img" aria-label="Python field"></canvas><figcaption>Python</figcaption></figure>
        <figure><canvas width="240" height="240" id="js-${s.slug}" role="img" aria-label="Browser field"></canvas><figcaption>browser</figcaption></figure></div>
        <span id="res-${s.slug}" class="mono">computing...</span></div>`)}</div>
    <p class="small mute">The node test <code>web/static/wave_engine.test.mjs</code> makes the same comparison on six
    more cases (all three boundary types, changed slit parameters, depth, decay and time scale) against
    <code>tests/fixtures/wave_reference.json</code>.</p>`;
  for (const s of setups) {
    const ref = await api('/reference/' + s.slug);
    const sim = buildSetup(s, ref.resolution);
    for (let f = 0; f < ref.frames; f++) sim.step(FRAME_DT);
    const py = decodeF64(ref.u_b64);
    let worst = 0;
    py.forEach((v, k) => { worst = Math.max(worst, Math.abs(v - sim.tank.u[k])); });
    const rel = worst / Math.max(1, ref.max_abs);
    const pyTank = { ...sim.tank, u: py, slits: sim.tank.slits, obstacles: sim.tank.obstacles };
    drawField(document.getElementById('py-' + s.slug).getContext('2d'), pyTank);
    drawField(document.getElementById('js-' + s.slug).getContext('2d'), sim.tank);
    const el = document.getElementById('res-' + s.slug);
    el.className = 'mono ' + (rel < 1e-9 ? 'ok' : 'err');
    el.textContent = `${ref.frames} frames × ${ref.steps_per_frame} steps, t = ${ref.time.toFixed(3)}, max |u| ${fmtNum(ref.max_abs)}; ` +
      `max difference ${worst.toExponential(1)} (relative ${rel.toExponential(1)}) ${rel < 1e-9 ? 'agree' : 'DIFFER'}`;
  }
});
