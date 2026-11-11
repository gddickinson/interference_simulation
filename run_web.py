"""Start the Wave Interference Simulation web app on http://127.0.0.1:8230 (local only).

Run: python run_web.py [--port 8230]
Needs: pip install -r requirements-web.txt
"""
import argparse

import uvicorn

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8230)
    port = ap.parse_args().port
    print(f"Wave Interference Simulation web app: http://127.0.0.1:{port}")
    uvicorn.run("web.app:app", host="127.0.0.1", port=port)
