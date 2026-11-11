// node wave_engine.test.mjs: the JS wave tank against the Python one (tests/fixtures/wave_reference.json, written by
// scripts/make_js_fixtures.py from web/reference.py running simulation.py), plus the seismic colour map.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { buildSetup, linspace, createSimulation, FRAME_DT } from './wave_engine.js';
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
    const ps = t.uPrev.reduce((s, v) => s + v, 0);
    assert.ok(rel(ps, ref.u_prev_sum, scale * ref.u.length) < 1e-9, `u_prev sum ${ps} vs ${ref.u_prev_sum}`);
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

console.log(`wave_engine: ${n} checks passed (${F.cases.length} Python reference cases at ${F.resolution} x ${F.resolution})`);
