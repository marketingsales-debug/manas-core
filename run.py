#!/usr/bin/env python3
"""
Launch Project Manas — Neuromorphic Cognitive AI Agent.

Usage:
  python run.py           # CLI chat interface
  python run.py --web     # Web dashboard on http://localhost:8000
  python run.py --web --port 9000   # Custom port
"""

import sys
import os
import argparse

# Ensure we can import the src package
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)


def launch_cli():
    from src.interface.chat import main
    main()


def launch_web(host: str = "127.0.0.1", port: int = 8000):
    import uvicorn
    from src.cognition.mind import Mind
    from src.interface.web_server import create_app

    print(f"\n  🧠  Manas Web Dashboard")
    print(f"  ──────────────────────────────────────────")
    print(f"  Starting brain… this may take a moment.")

    mind = Mind()
    app  = create_app(mind)

    print(f"\n  ✅  Dashboard ready → http://{host}:{port}")
    print(f"  Press Ctrl+C to stop.\n")

    uvicorn.run(app, host=host, port=port, log_level="warning")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Project Manas launcher")
    parser.add_argument("--web",  action="store_true", help="Launch web dashboard instead of CLI")
    parser.add_argument("--host", default="127.0.0.1", help="Web server host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Web server port (default: 8000)")
    args = parser.parse_args()

    if args.web:
        launch_web(host=args.host, port=args.port)
    else:
        launch_cli()
