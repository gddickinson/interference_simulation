"""Web interface tests: every exported endpoint answers, the static build is complete, and the JS engine tests pass.

Run: python -m pytest -q tests/test_web.py
"""
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from web.app import STATIC, STATIC_ENDPOINTS, app  # noqa: E402

client = TestClient(app)


def test_index_served():
    r = client.get("/")
    assert r.status_code == 200 and "static/main.js" in r.text


@pytest.mark.parametrize("path", STATIC_ENDPOINTS)
def test_endpoint(path):
    r = client.get("/api" + path)
    assert r.status_code == 200, r.text
    assert r.json() is not None


def test_static_build(tmp_path):
    sys.path.insert(0, str(ROOT / "scripts"))
    import build_static
    build_static.build(tmp_path / "site")
    assert (tmp_path / "site" / "index.html").read_text().count("APP_STATIC") == 1
    for path in STATIC_ENDPOINTS:
        assert (tmp_path / "site" / "api" / (path.strip("/") + ".json")).exists()


def test_static_assets_referenced_exist():
    html = (STATIC / "index.html").read_text()
    for name in ("style.css", "main.js"):
        assert f"static/{name}" in html and (STATIC / name).exists()


@pytest.mark.skipif(not shutil.which("node"), reason="node not installed")
def test_js_engine():
    tests = sorted(STATIC.glob("*.test.mjs"))
    for t in tests:
        r = subprocess.run(["node", str(t)], capture_output=True, text=True)
        assert r.returncode == 0, r.stdout + r.stderr


# --- wave-tank-specific API tests -------------------------------------------------------------------------------------
import base64  # noqa: E402
import json  # noqa: E402

import numpy as np  # noqa: E402

import sim_setup  # noqa: E402
from web.reference import EXAMPLE_SETUPS, fixture, run  # noqa: E402


def test_controls_come_from_sim_setup():
    d = client.get("/api/controls").json()
    assert {k: [v["label"], v["min"], v["max"], v["scale"]] for k, v in d["specs"].items()} == \
        {k: list(v) for k, v in sim_setup.CONTROL_SPECS.items()}
    assert d["boundaries"] == sim_setup.BOUNDARY_TYPES and d["standing_modes"] == sim_setup.STANDING_WAVE_MODES
    assert d["resolution"] == 200 and d["frame_dt"] == 0.05


def test_info_counts():
    d = client.get("/api/info").json()
    assert (d["boundary_types"], d["standing_modes"], d["controls"], d["setups"]) == (3, 5, 7, len(EXAMPLE_SETUPS))


def test_reference_is_the_python_tank():
    r = client.get("/api/reference/double-slit").json()
    u = np.frombuffer(base64.b64decode(r["u_b64"]), dtype="<f8").reshape(r["resolution"], r["resolution"])
    sim = run(EXAMPLE_SETUPS[0], r["frames"], r["resolution"])
    assert np.array_equal(u, sim.tank.u) and r["max_abs"] == np.abs(u).max() > 1
    assert client.get("/api/reference/nope").status_code == 404


def test_setups_are_finite_after_running():
    for s in EXAMPLE_SETUPS:
        assert np.isfinite(run(s, 3, 60).tank.u).all(), s["slug"]


def _close(a, b, path="fixture"):
    if isinstance(a, dict):
        assert a.keys() == b.keys(), path
        for k in a:
            _close(a[k], b[k], f"{path}.{k}")
    elif isinstance(a, list):
        assert len(a) == len(b), path
        for i, (x, y) in enumerate(zip(a, b)):
            _close(x, y, f"{path}[{i}]")
    elif isinstance(a, float) or isinstance(b, float):
        # rtol 1e-9 plus a small absolute floor: libm differs in the last digit between macOS and Linux (CI)
        assert abs(a - b) <= 1e-9 * max(abs(a), abs(b)) + 1e-8, f"{path}: {a} != {b}"
    else:
        assert a == b, path


def test_js_fixture_is_current():
    """tests/fixtures/wave_reference.json must match a fresh run of the Python code (run scripts/make_js_fixtures.py)."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import make_js_fixtures
    _close(json.loads(make_js_fixtures.FIXTURE.read_text()), json.loads(make_js_fixtures.dumps(fixture())))
