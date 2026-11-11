"""Write tests/fixtures/wave_reference.json: numbers from the real Python wave tank (simulation.py) and matplotlib's
'seismic' colormap that the node test web/static/wave_engine.test.mjs compares the JavaScript port against.

Run after changing simulation.py, sim_setup.py or web/reference.py:
    python scripts/make_js_fixtures.py
tests/test_web.py fails if the committed fixture is out of date.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from web.reference import fixture  # noqa: E402

FIXTURE = ROOT / "tests" / "fixtures" / "wave_reference.json"


def dumps(data) -> str:
    return json.dumps(data, separators=(",", ":"), sort_keys=True)


def main():
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(dumps(fixture()))
    print(f"wrote {FIXTURE} ({FIXTURE.stat().st_size / 1e3:.0f} kB)")


if __name__ == "__main__":
    main()
