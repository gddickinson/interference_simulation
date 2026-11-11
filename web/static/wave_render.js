// Canvas rendering of the wave field the way Tank.plot draws it: matplotlib's 'seismic' colour map, vmin/vmax at
// -/+ Tank.colour_range (95th percentile of |u|) or a chosen range, origin at the bottom left, slits as dots and obstacles as circle outlines.

// matplotlib _seismic_data, evenly spaced, expanded to 256 entries exactly as LinearSegmentedColormap.from_list does.
const ANCHORS = [[0, 0, 0.3], [0, 0, 1], [1, 1, 1], [1, 0, 0], [0.5, 0, 0]];
export const SEISMIC_LUT = buildLut(ANCHORS, 256);

function buildLut(anchors, N) {
  const m = anchors.length, pos = anchors.map((_, k) => (k === m - 1 ? 1 : k * (1 / (m - 1))) * (N - 1));
  const lut = [];
  for (let i = 0; i < N; i++) {
    if (i === 0) { lut.push([...anchors[0]]); continue; }
    if (i === N - 1) { lut.push([...anchors[m - 1]]); continue; }
    let k = 0; while (pos[k] < i) k++;   // numpy.searchsorted(x, i) (side='left')
    const d = (i - pos[k - 1]) / (pos[k] - pos[k - 1]);
    lut.push([0, 1, 2].map(ch => Math.min(1, Math.max(0, d * (anchors[k][ch] - anchors[k - 1][ch]) + anchors[k - 1][ch]))));
  }
  return lut;
}
const LUT8 = SEISMIC_LUT.map(c => c.map(v => Math.round(v * 255)));

// Colour index for a value with Normalize(vmin, vmax) and Colormap.__call__ (truncate, clamp under/over).
export function lutIndex(v, vmin, vmax) {
  let xa = ((v - vmin) / (vmax - vmin)) * 256;
  if (xa === 256) xa = 255;
  return xa < 0 ? 0 : xa >= 256 ? 255 : Math.trunc(xa);
}

const off = typeof document !== 'undefined' ? document.createElement('canvas') : null;

// Draw the field (default tank.field()) into ctx (any canvas size). opts: range (vmax; vmin = -range), marks.
export function drawField(ctx, tank, { range = 1, marks = true, values = null } = {}) {
  const n = tank.resolution, u = values || tank.field();
  if (off.width !== n) { off.width = n; off.height = n; }
  const octx = off.getContext('2d'), img = octx.createImageData(n, n), d = img.data;
  for (let i = 0; i < n; i++) {
    const row = (n - 1 - i) * n;                       // origin='lower': row 0 at the bottom
    for (let j = 0; j < n; j++) {
      const c = LUT8[lutIndex(u[i * n + j], -range, range)], p = (row + j) * 4;
      d[p] = c[0]; d[p + 1] = c[1]; d[p + 2] = c[2]; d[p + 3] = 255;
    }
  }
  octx.putImageData(img, 0, 0);
  const W = ctx.canvas.width, H = ctx.canvas.height;
  ctx.imageSmoothingEnabled = true;
  ctx.drawImage(off, 0, 0, W, H);
  if (marks) drawMarks(ctx, tank);
}

// Dashed line at the inner edge of the absorbing layer on each wall without slits.
function drawSponge(ctx, tank, s) {
  const walls = tank.slitWalls(), w = tank.spongeCells() * tank.dx, W = tank.width, H = tank.height;
  const lines = { left: [[w, 0], [w, H]], right: [[W - w, 0], [W - w, H]], bottom: [[0, w], [W, w]], top: [[0, H - w], [W, H - w]] };
  ctx.save();
  ctx.setLineDash([6 * s, 6 * s]); ctx.lineWidth = 1.5 * s; ctx.strokeStyle = 'rgba(40,40,60,.55)';
  for (const [side, [a, b]] of Object.entries(lines)) {
    if (walls.has(side)) continue;
    ctx.beginPath(); ctx.moveTo(...toCanvas(ctx, tank, ...a)); ctx.lineTo(...toCanvas(ctx, tank, ...b)); ctx.stroke();
  }
  ctx.restore();
}

export function toCanvas(ctx, tank, x, y) {
  return [x / tank.width * ctx.canvas.width, (1 - y / tank.height) * ctx.canvas.height];
}

function drawMarks(ctx, tank) {
  const s = ctx.canvas.width / 600;
  if (tank.boundaryType === 'absorbing' && tank.slitWalls) drawSponge(ctx, tank, s);
  ctx.lineWidth = 2 * s;
  for (const o of tank.obstacles) {
    const [cx, cy] = toCanvas(ctx, tank, ...o.position);
    ctx.strokeStyle = '#000'; ctx.beginPath();
    ctx.arc(cx, cy, o.radius / tank.width * ctx.canvas.width, 0, 2 * Math.PI); ctx.stroke();
  }
  const dot = (x, y, fill, r) => {
    const [cx, cy] = toCanvas(ctx, tank, x, y);
    ctx.fillStyle = fill; ctx.strokeStyle = '#fff';
    ctx.beginPath(); ctx.arc(cx, cy, r * s, 0, 2 * Math.PI); ctx.fill(); ctx.stroke();
  };
  for (const sl of tank.slits) dot(...sl.position, '#000', 6);
  for (const p of tank.interferencePoints) dot(...p.position, '#1fd8a0', 4);
  for (const p of tank.wavePackets) dot(...p.position, '#ffb347', 4);
}
