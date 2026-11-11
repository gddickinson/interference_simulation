// node wave_engine.test.mjs: the JS wave tank against the Python one (tests/fixtures/wave_reference.json, written by
// scripts/make_js_fixtures.py from web/reference.py running simulation.py), plus the seismic colour map.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { buildSetup, linspace, createSimulation, FRAME_DT, Tank, Simulation } from './wave_engine.js';
import { SEISMIC_LUT } from './wave_render.js';

const F = JSON.parse(readFileSync(new URL('../../tests/fixtures/wave_reference.json', import.meta.url)));
let n = 0;
const ok = (name, fn) => { fn(); n++; console.log('ok  ', name); };
const rel = (a, b, scale) => Math.abs(a - b) / Math.max(1, scale);

ok('linspace equals numpy.linspace', () => {
  const x = linspace(0, 20, F.resolution);
  F.x.forEach((v, i) => assert.equal(x[i], v));
});

for (const ref of F.cases) {
  const c = ref.setup;
  ok(`case "${c.slug}" (${c.boundary || 'reflective'}): ${c.frames} frames x ${ref.steps} steps match Python`, () => {
    const sim = buildSetup(c, F.resolution);
    const t = sim.tank;
    assert.equal(sim.stepsPerFrame(), ref.steps);
    assert.equal(t.dt, ref.dt); assert.equal(t.c, ref.c);
    assert.equal(t.boundary.filter(v => v === 0).length, ref.boundary_zeros);
    const dsum = t.distanceMap.reduce((s, v) => s + v, 0);
    assert.ok(Math.abs(dsum - ref.distance_sum) < 1e-9, `distance sum ${dsum} vs ${ref.distance_sum}`);
    ref.distance_row7.forEach((v, j) => assert.ok(Math.abs(t.distanceMap[7 * F.resolution + j] - v) < 1e-14));
    for (let f = 0; f < c.frames; f++) sim.step(FRAME_DT);
    assert.ok(Math.abs(sim.time - ref.time) < 1e-12, `time ${sim.time} vs ${ref.time}`);
    const scale = Math.max(...ref.u.map(Math.abs));
    let worst = 0;
    ref.u.forEach((v, k) => { worst = Math.max(worst, rel(t.u[k], v, scale)); });
    assert.ok(worst < 1e-9, `max |u_js - u_py| / max|u| = ${worst}`);
    const fs = t.field().reduce((a, v) => a + v, 0);
    assert.ok(rel(fs, ref.field_sum, scale * ref.u.length) < 1e-9, `field sum ${fs} vs ${ref.field_sum}`);
    assert.equal(t.colourRange(), ref.colour_range);
    const ps = t.uPrev.reduce((s, v) => s + v, 0);
    assert.ok(rel(ps, ref.u_prev_sum, scale * ref.u.length) < 1e-9, `u_prev sum ${ps} vs ${ref.u_prev_sum}`);
    if (!c.slug.includes('standing')) assert.ok(scale < 5 * ref.colour_range, 'bounded by 5 x source amplitude');
    console.log(`      max |u| ${scale.toFixed(3)}, max relative difference ${worst.toExponential(2)}`);
  });
}

ok('seismic colour map equals matplotlib (256 entries)', () => {
  assert.equal(SEISMIC_LUT.length, F.seismic.length);
  F.seismic.forEach((rgb, i) => rgb.forEach((v, ch) => assert.ok(Math.abs(SEISMIC_LUT[i][ch] - v) < 1e-12, `lut ${i}`)));
});

ok('createSimulation matches sim_setup defaults (two bottom slits, 200 x 200, reflective)', () => {
  const sim = createSimulation({ bottom: 2 });
  assert.deepEqual(sim.tank.slits.map(s => s.position), [[20 / 3, 0], [40 / 3, 0]]);
  assert.equal(sim.tank.resolution, 200); assert.equal(sim.tank.boundaryType, 'reflective');
  assert.equal(sim.stepsPerFrame(), 99);
});

ok('no slits: field stays finite (Fix NaN wave field when the tank has no slits)', () => {
  const sim = createSimulation({}, { resolution: 30 });
  sim.tank.addInterferencePoint([10, 10], 1, 1);
  sim.step();
  assert.ok(sim.tank.u.every(Number.isFinite));
});

ok('prescribed sources stay bounded: 300 frames, every boundary, max |u| < 5 A', () => {
  for (const boundary of ['reflective', 'absorbing', 'open']) {
    const sim = createSimulation({ bottom: 2 }, { resolution: 60 });
    sim.tank.setBoundaryType(boundary);
    let peak = 0;
    for (let f = 0; f < 300; f++) { sim.step(); for (const v of sim.tank.u) peak = Math.max(peak, Math.abs(v)); }
    assert.ok(peak < 50, `${boundary}: peak ${peak}`);
  }
});

ok('slits on one wall oscillate in phase', () => {
  for (const cfg of [{ bottom: 2 }, { bottom: 3 }, { top: 4 }, { right: 2 }]) {
    const sim = createSimulation(cfg, { resolution: 60 }), t = sim.tank, N = t.resolution;
    sim.step();
    const v = t.slits.map(({ position: [x, y] }) =>
      t.u[Math.min(Math.trunc(y / t.dy), N - 1) * N + Math.min(Math.trunc(x / t.dx), N - 1)]);
    v.forEach(a => assert.ok(Math.abs(a - v[0]) < 1e-12, JSON.stringify(cfg) + ' ' + v));
  }
});

// Energy of a Gaussian pulse left in an empty tank after t = 3 (tests/test_physics.py pulse_energy_left)
export function pulseEnergyLeft(boundary, time = 3) {
  const t = new Tank(20, 20, 100, [], { decayFactor: 1 }), N = t.resolution;
  t.setBoundaryType(boundary);
  for (let i = 0; i < N; i++) for (let j = 0; j < N; j++)
    t.u[i * N + j] = Math.exp(-((t.x[j] - 10) ** 2 + (t.y[i] - 10) ** 2) / (2 * 0.8 ** 2));
  t.uPrev.set(t.u);
  const sim = new Simulation(t), energy = () => {
    let e = 0;
    for (let i = 1; i < N - 1; i++) for (let j = 1; j < N - 1; j++) {
      const k = i * N + j, ut = (t.u[k] - t.uPrev[k]) / t.dt;
      const gx = (t.u[k + 1] - t.u[k - 1]) / (2 * t.dx), gy = (t.u[k + N] - t.u[k - N]) / (2 * t.dy);
      e += ut ** 2 + t.c ** 2 * (gx ** 2 + gy ** 2);
    }
    return e;
  };
  sim.step();
  const e0 = energy();
  while (sim.time < time) sim.step();
  return energy() / e0;
}
ok('open and absorbing walls let a pulse leave (< 3 % of its energy left; reflective keeps > 50 %)', () => {
  assert.ok(pulseEnergyLeft('reflective') > 0.5);
  for (const b of ['open', 'absorbing']) {
    const left = pulseEnergyLeft(b);
    assert.ok(left < 0.03, `${b}: ${left}`);
    console.log(`      ${b} walls: ${(100 * left).toFixed(3)} % of the pulse energy left`);
  }
});

ok('absorbing walls keep the slit strength (transmitted peak >= 0.7 x open)', () => {
  const peak = boundary => {
    const sim = createSimulation({ bottom: 1 }, { resolution: 100 }), t = sim.tank;
    t.setBoundaryType(boundary);
    const k = Math.trunc(6 / t.dy) * t.resolution + Math.trunc(10 / t.dx);
    let p = 0;
    for (let f = 0; f < 80; f++) { sim.step(); if (f >= 40) p = Math.max(p, Math.abs(t.u[k])); }
    return p;
  };
  const a = peak('absorbing'), o = peak('open');
  assert.ok(a > 0.7 * o, `absorbing ${a} vs open ${o}`);
});

console.log(`wave_engine: ${n} checks passed (${F.cases.length} Python reference cases at ${F.resolution} x ${F.resolution})`);
