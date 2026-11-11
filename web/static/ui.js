// Shared page helpers: control specs and example set-ups from the API, colour-range handling and the colour legend.
import { api } from './core.js';
import { SEISMIC_LUT, drawField, robustMax } from './wave_render.js';

let setupPromise = null;
// { controls, setups } from /api/controls and /api/setups (sim_setup.py and web/reference.py on the server).
export function loadSetup() {
  if (!setupPromise) setupPromise = Promise.all([api('/controls'), api('/setups')]).then(([controls, setups]) => ({ controls, setups }));
  return setupPromise;
}

// Colour range: 'desktop' is Tank.plot's fixed vmin -1 / vmax 1; 'auto' scales to the 99th percentile of |u|.
export function colourRange(tank, mode) { return mode === 'auto' ? robustMax(tank.u) : 1; }

export function draw(canvas, sim, mode = 'desktop', marks = true) {
  const range = colourRange(sim.tank, mode);
  drawField(canvas.getContext('2d'), sim.tank, { range, marks });
  return range;
}

// Horizontal seismic colour bar with its range labels.
export function legend(host) {
  host.innerHTML = '<span class="lo">-1</span><canvas width="256" height="1" aria-hidden="true"></canvas><span class="hi">+1</span>';
  const ctx = host.querySelector('canvas').getContext('2d'), img = ctx.createImageData(256, 1);
  SEISMIC_LUT.forEach((c, i) => { img.data.set([c[0] * 255, c[1] * 255, c[2] * 255, 255], i * 4); });
  ctx.putImageData(img, 0, 0);
  return range => {
    const t = range >= 100 ? range.toFixed(0) : range >= 1 ? range.toFixed(1) : range.toPrecision(2);
    host.querySelector('.lo').textContent = '-' + t; host.querySelector('.hi').textContent = '+' + t;
  };
}

// Desktop pacing: SimulationGUI's timer fires every 50 ms; returns true when the next frame is due at rAF time t.
export function pacer(ms = 50) {
  let last = -Infinity;
  return t => { if (t - last < ms - 4) return false; last = t; return true; };   // 4 ms slack for rAF jitter
}

export const fmtNum = (v, d = 3) => (Math.abs(v) >= 1000 ? v.toFixed(0) : v.toPrecision(d));

// Decode a little-endian float64 base64 array (the /reference endpoint).
export function decodeF64(b64) {
  const bin = atob(b64), bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  return new Float64Array(bytes.buffer);
}
