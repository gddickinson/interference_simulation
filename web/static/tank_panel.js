// Control panel of the Tank page: the desktop GUI's controls (same ranges and scales, from /api/controls) plus the
// slit-count prompt, example set-ups and a few web-only conveniences (resolution, colour range, click to place).
import { esc, list, slider } from './core.js';

const RESOLUTIONS = [100, 150, 200];

// Render the panel into host. state: { setup, resolution, colour, click, running }. cb: handlers called on change.
export function renderPanel(host, { controls: C, setups }, state, sim, cb) {
  const s = state.setup, slits = s.slits || {};
  host.innerHTML = `
    <label for="ex">Example set-up</label>
    <select id="ex"><option value="">Custom</option>${list(setups, x =>
      `<option value="${x.slug}" ${x.slug === state.slug ? 'selected' : ''}>${esc(x.name)}</option>`)}</select>
    <h3>Slits per side</h3>
    <div class="sides">${list(C.sides, side => `<div><label for="n-${side}">${side}</label>
      <input id="n-${side}" type="number" min="0" max="8" value="${slits[side] || 0}"></div>`)}</div>
    <div class="row"><div><label for="res">Grid</label><select id="res">${list(RESOLUTIONS, r =>
      `<option value="${r}" ${r === state.resolution ? 'selected' : ''}>${r} x ${r}${r === C.resolution ? ' (desktop)' : ''}</option>`)}</select></div></div>
    <button id="build" class="alt">Build tank</button>
    <div class="btns">
      <button id="run">${state.running ? 'Stop' : 'Start'}</button><button id="reset" class="alt">Reset</button>
      <button id="obst" class="alt">Add Obstacle</button><button id="pack" class="alt">Add Wave Packet</button>
      <button id="point" class="alt">Add Interference Point</button>
    </div>
    <h3>Global controls</h3><div id="globals"></div>
    <label for="bnd">Boundary type</label>
    <select id="bnd">${list(C.boundaries, b => `<option ${b.toLowerCase() === sim.tank.boundaryType ? 'selected' : ''}>${b}</option>`)}</select>
    <label for="stand">Standing wave mode</label>
    <select id="stand">${list(C.standing_modes, m => `<option ${String(sim.tank.standingWaveMode ?? 'None') === m ? 'selected' : ''}>${m}</option>`)}</select>
    <h3>Slit controls</h3><div id="slits">${sim.tank.slits.length ? '' : '<p class="small mute">No slits in this tank.</p>'}</div>
    <h3>View (web only)</h3>
    <label for="col">Colour range</label>
    <select id="col"><option value="desktop" ${state.colour === 'desktop' ? 'selected' : ''}>-1 to +1 (as the desktop plot)</option>
      <option value="auto" ${state.colour === 'auto' ? 'selected' : ''}>auto (99th percentile of |u|)</option></select>
    <label for="click">Clicking the tank adds</label>
    <select id="click">${list([['none', 'nothing'], ['obstacle', 'an obstacle'], ['point', 'an interference point'], ['packet', 'a wave packet']],
      ([v, t]) => `<option value="${v}" ${state.click === v ? 'selected' : ''}>${t}</option>`)}</select>
    <button id="png" class="alt">Save PNG</button>`;
  const $ = id => host.querySelector('#' + id);

  const g = $('globals'), cur = { time_scale: sim.timeScale, depth: sim.tank.depth, decay_factor: sim.tank.decayFactor };
  for (const key of C.global) {
    const sp = C.specs[key];
    slider(g, { id: key, label: sp.label, min: sp.min, max: sp.max, value: Math.trunc(cur[key] * sp.scale), fmt: v => +(v / sp.scale).toFixed(3) },
      v => cb.global(key, v / sp.scale));
  }
  sim.tank.slits.forEach((sl, i) => {
    const d = document.createElement('details');
    d.className = 'slit'; d.open = i === 0;
    d.innerHTML = `<summary>Slit ${i + 1} at (${sl.position.map(v => +v.toFixed(2)).join(', ')})</summary>`;
    $('slits').appendChild(d);
    for (const key of C.slit) {
      const sp = C.specs[key];
      slider(d, { id: `s${i}-${key}`, label: sp.label, min: sp.min, max: sp.max, value: Math.trunc(sl[key] * sp.scale), fmt: v => +(v / sp.scale).toFixed(3) },
        v => { sl[key] = v / sp.scale; cb.changed(); });
    }
  });

  $('ex').addEventListener('change', e => cb.example(e.target.value));
  $('build').addEventListener('click', () => {
    const counts = Object.fromEntries(C.sides.map(side => [side, Math.max(0, Math.min(8, Math.trunc(+$('n-' + side).value || 0)))]));
    cb.build(counts, +$('res').value);
  });
  $('res').addEventListener('change', e => cb.resolution(+e.target.value));
  $('run').addEventListener('click', () => cb.toggle());
  $('reset').addEventListener('click', () => cb.reset());
  $('obst').addEventListener('click', () => cb.add('obstacle'));
  $('pack').addEventListener('click', () => cb.add('packet'));
  $('point').addEventListener('click', () => cb.add('point'));
  $('bnd').addEventListener('change', e => cb.boundary(e.target.value.toLowerCase()));
  $('stand').addEventListener('change', e => cb.standing(e.target.value === 'None' ? null : +e.target.value));
  $('col').addEventListener('change', e => cb.colour(e.target.value));
  $('click').addEventListener('change', e => cb.click(e.target.value));
  $('png').addEventListener('click', () => cb.png());
  return { setRunning: on => { $('run').textContent = on ? 'Stop' : 'Start'; }, setStanding: m => { $('stand').value = m === null ? 'None' : String(m); } };
}

// Random element with the desktop GUI's uniform ranges (sim_setup.RANDOM_RANGES); at (x, y) if given.
export function randomElement(kind, C, tank, at = null, rand = Math.random) {
  const R = C.random_ranges, u = ([a, b]) => a + (b - a) * rand();
  const pos = at || [u([0, tank.width]), u([0, tank.height])];
  if (kind === 'obstacle') return () => tank.addObstacle(pos, u(R.obstacle.radius));
  if (kind === 'point') {
    const r = R.interference_point;
    return () => tank.addInterferencePoint(pos, u(r.amplitude), u(r.frequency));
  }
  const r = R.wave_packet;
  return () => tank.addWavePacket(pos, u(r.amplitude), u(r.frequency), u(r.wavelength), u(r.width), [u(r.direction), u(r.direction)]);
}
