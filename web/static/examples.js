// Examples page (#/examples): every example set-up running live in a small tank; click to open it in the simulator.
import { route, app, esc, list, animate } from './core.js';
import { buildSetup, FRAME_DT } from './wave_engine.js';
import { loadSetup, draw, pacer } from './ui.js';

const RES = 90, CYCLE = 60;   // frames before each tank starts over

route('examples', async () => {
  const { setups } = await loadSetup();
  app().innerHTML = `
    <h1 class="glow">Examples</h1>
    <p class="lead">Ready-made tanks built with the desktop app's own pieces: slits spaced evenly along a side (as the
    start-up prompt sets them), obstacles, wave packets, interference points and standing-wave modes. These set-ups
    were chosen for this web page; the desktop app starts from the slit counts you type in. Each runs live here on a
    ${RES} × ${RES} grid at the desktop pace (one frame per 50 ms) and starts over every ${CYCLE * 0.05} s.</p>
    <div class="grid gal">${list(setups, s => `
      <a class="card" href="#/tank?setup=${s.slug}">
        <canvas width="300" height="300" data-slug="${s.slug}" role="img" aria-label="${esc(s.name)}: live wave field"></canvas>
        <b>${esc(s.name)}</b><span>${esc(s.note)}</span>
        <small>${esc(describe(s))}</small></a>`)}</div>`;
  const live = setups.map(s => ({ sim: buildSetup(s, RES), canvas: app().querySelector(`canvas[data-slug="${s.slug}"]`) }));
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    live.forEach(l => { for (let i = 0; i < 30; i++) l.sim.step(FRAME_DT); draw(l.canvas, l.sim); });
    return;
  }
  const due = pacer();
  let frame = 0;
  animate(t => {
    if (!due(t)) return;
    if (++frame > CYCLE) { live.forEach(l => l.sim.reset()); frame = 0; }
    live.forEach(l => { l.sim.step(FRAME_DT); draw(l.canvas, l.sim); });
  });
});

export function describe(s) {
  const slits = Object.entries(s.slits || {}).filter(([, n]) => n).map(([side, n]) => `${n} ${side}`).join(', ') || 'no slits';
  const bits = [`slits: ${slits}`, `boundary: ${s.boundary || 'reflective'}`];
  if (s.depth) bits.push(`depth ${s.depth}`);
  if (s.standing) bits.push(`standing mode ${s.standing}`);
  if (s.obstacles) bits.push(`${s.obstacles.length} obstacle`);
  if (s.packets) bits.push(`${s.packets.length} packet`);
  if (s.points) bits.push(`${s.points.length} points`);
  return bits.join(' · ');
}
