// JS port of simulation.py (Tank, Simulation) and sim_setup.create_simulation: the same FDTD update, sources, decay
// and boundary handling, operation for operation, so the browser tank matches the Python one to rounding error
// (checked by wave_engine.test.mjs against tests/fixtures/wave_reference.json). Grids are row-major Float64Arrays,
// row i = y index, column j = x index (numpy's u[y, x]); row 0 is the bottom of the tank (imshow origin='lower').

export const FRAME_DT = 0.05;          // the desktop timer calls simulation.step(0.05) every 50 ms
export const TANK = { width: 20, height: 20, resolution: 200 };
export const SLIT_DEFAULTS = { width: 0.5, amplitude: 10, frequency: 1, wavelength: 2 };
export const SIDES = ['bottom', 'top', 'left', 'right'];
export const BOUNDARIES = ['reflective', 'absorbing', 'open'];

// numpy.linspace(start, stop, num) (endpoint included, last value set to stop)
export function linspace(start, stop, num) {
  const out = new Float64Array(num), step = (stop - start) / (num - 1);
  for (let i = 0; i < num; i++) out[i] = i * step + start;
  if (num > 1) out[num - 1] = stop;
  return out;
}

export class Tank {
  constructor(width, height, resolution, slits, { depth = 1.0, decayFactor = 0.999 } = {}) {
    Object.assign(this, { width, height, resolution, slits, depth, decayFactor });
    this.obstacles = [];
    this.boundaryType = 'reflective';
    this.dx = width / (resolution - 1);
    this.dy = height / (resolution - 1);
    this.c = 10 * Math.sqrt(depth);
    this.dt = 0.05 * Math.min(this.dx, this.dy) / this.c;
    this.x = linspace(0, width, resolution);
    this.y = linspace(0, height, resolution);
    const n = resolution * resolution;
    this.u = new Float64Array(n);
    this.uPrev = new Float64Array(n);
    this.uNext = new Float64Array(n);   // scratch for the interior update
    this.boundary = new Float64Array(n);
    this.distanceMap = new Float64Array(n);
    this.updateBoundary();
    this.updateDistanceMap();
    this.wavePackets = [];
    this.interferencePoints = [];
    this.standingWaveMode = null;
  }

  updateDistanceMap() {
    const { resolution: n, x, y, distanceMap: dm } = this;
    dm.fill(Infinity);
    for (const s of this.slits) {
      const [sx, sy] = s.position;
      for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) {
        const ddx = x[j] - sx, ddy = y[i] - sy, d = Math.sqrt(ddx * ddx + ddy * ddy);
        if (d < dm[i * n + j]) dm[i * n + j] = d;
      }
    }
    if (!this.slits.length) { dm.fill(0); return; }   // no slits: no distance decay (see simulation.py)
    let mx = -Infinity;
    for (const v of dm) if (v > mx) mx = v;
    for (let k = 0; k < dm.length; k++) dm[k] /= mx;
  }

  updateBoundary() {
    const { resolution: n, x, y, boundary: b } = this;
    b.fill(1);
    for (let k = 0; k < n; k++) { b[k] = 0; b[(n - 1) * n + k] = 0; b[k * n] = 0; b[k * n + n - 1] = 0; }
    for (const o of this.obstacles) {
      const [ox, oy] = o.position, r2 = o.radius ** 2;
      for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) {
        const ddx = x[j] - ox, ddy = y[i] - oy;
        if (ddx * ddx + ddy * ddy <= r2) b[i * n + j] = 0;
      }
    }
  }

  update(time) {
    const { resolution: n, u, uPrev, uNext, boundary: b, distanceMap: dm, x, y } = this;
    const idx2 = this.dx ** 2, idy2 = this.dy ** 2, k2 = this.c ** 2 * this.dt ** 2, keep = 1 - this.decayFactor;
    const refl = this.boundaryType === 'reflective';
    for (let i = 1; i < n - 1; i++) {
      const edgeRow = i === 1 || i === n - 2;
      for (let j = 1; j < n - 1; j++) {
        const k = i * n + j, c = u[k];
        const lap = (u[k + 1] + u[k - 1] - 2 * c) / idx2 + (u[k + n] + u[k - n] - 2 * c) / idy2;
        let v = 2 * c - uPrev[k] + k2 * lap;
        v *= 1 - keep * dm[k];
        // reflective: tank walls + obstacles; absorbing/open: obstacles only (outer ring of the interior kept)
        if (refl || !(edgeRow || j === 1 || j === n - 2)) v *= b[k];
        uNext[k] = v;
      }
    }
    uPrev.set(u);
    for (let i = 1; i < n - 1; i++) for (let j = 1; j < n - 1; j++) u[i * n + j] = uNext[i * n + j];

    const TWO_PI = 2 * Math.PI;
    for (const s of this.slits) {
      const [sx, sy] = s.position;
      const xi = Math.trunc(sx / this.dx), yi = Math.trunc(sy / this.dy);
      const sw = Math.max(1, Math.trunc(s.width / this.dx)), h = Math.floor(sw / 2);
      let r0, r1, c0, c1;
      if (xi === 0) { c0 = 0; c1 = 3; r0 = Math.max(0, yi - h); r1 = Math.min(n, yi + h + 1); }
      else if (xi === n - 1) { c0 = n - 3; c1 = n; r0 = Math.max(0, yi - h); r1 = Math.min(n, yi + h + 1); }
      else if (yi === 0) { c0 = Math.max(0, xi - h); c1 = Math.min(n, xi + h + 1); r0 = 0; r1 = 3; }
      else if (yi === n - 1) { c0 = Math.max(0, xi - h); c1 = Math.min(n, xi + h + 1); r0 = n - 3; r1 = n; }
      else continue;
      for (let i = r0; i < r1; i++) for (let j = c0; j < c1; j++)
        u[i * n + j] += s.amplitude * Math.sin(TWO_PI * (s.frequency * time - x[j] / s.wavelength));
    }

    for (const p of this.wavePackets) {
      const [px, py] = p.position, w = p.width, [d0, d1] = p.direction;
      const c0 = Math.max(0, Math.trunc((px - w) / this.dx)), c1 = Math.min(n, Math.trunc((px + w) / this.dx));
      const r0 = Math.max(0, Math.trunc((py - w) / this.dy)), r1 = Math.min(n, Math.trunc((py + w) / this.dy));
      const den = 2 * w ** 2;
      for (let i = r0; i < r1; i++) for (let j = c0; j < c1; j++) {
        const d = (x[j] - px) * d0 + (y[i] - py) * d1;
        const g = Math.exp(-(d ** 2) / den);
        u[i * n + j] += p.amplitude * Math.sin(TWO_PI * (p.frequency * time - d / p.wavelength)) * g;
      }
    }

    for (const p of this.interferencePoints) {
      const xi = Math.trunc(p.position[0] / this.dx), yi = Math.trunc(p.position[1] / this.dy);
      u[yi * n + xi] += p.amplitude * Math.sin(TWO_PI * p.frequency * time);
    }

    if (this.standingWaveMode !== null) {
      const m = this.standingWaveMode, st = Math.sin(TWO_PI * time);
      for (let j = 0; j < n; j++) {
        const v = 0.5 * Math.sin(m * Math.PI * x[j] / this.width) * st;
        for (let i = 0; i < n; i++) u[i * n + j] += v;
      }
    }

    if (this.boundaryType === 'absorbing') {
      const ew = 10, ef = linspace(0, 1, ew);
      for (let a = 0; a < ew; a++) {
        const top = (n - ew + a) * n;
        for (let j = 0; j < n; j++) u[a * n + j] *= ef[a];
        for (let j = 0; j < n; j++) u[top + j] *= ef[ew - 1 - a];
      }
      for (let i = 0; i < n; i++) for (let a = 0; a < ew; a++) {
        u[i * n + a] *= ef[a];
        u[i * n + n - ew + a] *= ef[ew - 1 - a];
      }
    }
  }

  addObstacle(position, radius) { this.obstacles.push({ position, radius }); this.updateBoundary(); }
  setBoundaryType(t) {
    if (!BOUNDARIES.includes(t)) throw new Error("Invalid boundary type. Choose 'reflective', 'absorbing', or 'open'.");
    this.boundaryType = t;
  }
  setDepth(depth) { this.depth = depth; this.c = 10 * Math.sqrt(depth); this.dt = 0.05 * Math.min(this.dx, this.dy) / this.c; }
  setDecayFactor(f) { this.decayFactor = f; }
  addWavePacket(position, amplitude, frequency, wavelength, width, direction) {
    this.wavePackets.push({ position, amplitude, frequency, wavelength, width, direction });
  }
  addInterferencePoint(position, amplitude, frequency) { this.interferencePoints.push({ position, amplitude, frequency }); }
  setStandingWaveMode(mode) { this.standingWaveMode = mode; }
  reset() {
    this.u.fill(0); this.uPrev.fill(0);
    this.updateBoundary(); this.updateDistanceMap();
    this.wavePackets = []; this.interferencePoints = []; this.standingWaveMode = null;
  }
}

export class Simulation {
  constructor(tank) { this.tank = tank; this.time = 0; this.timeScale = 1; }
  stepsPerFrame(dt = FRAME_DT) { return Math.max(1, Math.trunc(dt / this.tank.dt)); }
  step(dt = FRAME_DT) {
    const steps = this.stepsPerFrame(dt);
    for (let s = 0; s < steps; s++) { this.time += this.tank.dt * this.timeScale; this.tank.update(this.time); }
  }
  setTimeScale(s) { this.timeScale = s; }
  reset() { this.time = 0; this.tank.reset(); }
}

// sim_setup.slit_positions: evenly spaced slits on each side, in insertion order of the config.
export function slitPositions(config, width = TANK.width, height = TANK.height) {
  const out = [];
  for (const [side, num] of Object.entries(config)) for (let i = 0; i < num; i++) {
    const k = i + 1, d = num + 1;
    if (side === 'bottom') out.push([width * k / d, 0]);
    else if (side === 'top') out.push([width * k / d, height]);
    else if (side === 'left') out.push([0, height * k / d]);
    else if (side === 'right') out.push([width, height * k / d]);
  }
  return out;
}

// sim_setup.create_simulation
export function createSimulation(config, { depth = 1.0, decayFactor = 0.999, resolution = TANK.resolution } = {}) {
  const slits = slitPositions(config).map(position => ({ position, ...SLIT_DEFAULTS }));
  const tank = new Tank(TANK.width, TANK.height, resolution, slits, { depth, decayFactor });
  tank.setBoundaryType('reflective');
  return new Simulation(tank);
}

// web/reference.py build(): a Simulation from a setup object (the web app's example setups).
export function buildSetup(setup, resolution = TANK.resolution) {
  const sim = createSimulation(setup.slits || {}, { depth: setup.depth ?? 1.0, decayFactor: setup.decay_factor ?? 0.999, resolution });
  const t = sim.tank;
  for (const s of t.slits) Object.assign(s, setup.slit_params || {});
  t.setBoundaryType(setup.boundary || 'reflective');
  sim.setTimeScale(setup.time_scale ?? 1);
  t.setStandingWaveMode(setup.standing ?? null);
  for (const [x, y, r] of setup.obstacles || []) t.addObstacle([x, y], r);
  for (const [x, y, a, f, wl, w, ddx, ddy] of setup.packets || []) t.addWavePacket([x, y], a, f, wl, w, [ddx, ddy]);
  for (const [x, y, a, f] of setup.points || []) t.addInterferencePoint([x, y], a, f);
  return sim;
}
