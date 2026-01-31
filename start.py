#!/usr/bin/env python3
"""
PubCheck Launcher
Starts backend and frontend servers, opens browser when ready.

Usage: python start.py
"""

import subprocess
import sys
import time
import webbrowser
import socket
import os
from pathlib import Path

# Load .env file from project root
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

# Configuration
BACKEND_PORT = 8003
FRONTEND_PORT_START = 5173
PROJECT_ROOT = Path(__file__).parent


def find_free_port(start_port: int, max_attempts: int = 10) -> int:
    """Find the first available port starting from start_port."""
    for offset in range(max_attempts):
        port = start_port + offset
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise RuntimeError(f"No free port found in range {start_port}-{start_port + max_attempts}")


def is_port_ready(port: int) -> bool:
    """Check if something is listening on the port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        return s.connect_ex(("127.0.0.1", port)) == 0


def wait_for_port(port: int, timeout: int = 30) -> bool:
    """Wait for a port to become available."""
    start = time.time()
    while time.time() - start < timeout:
        if is_port_ready(port):
            return True
        time.sleep(0.3)
    return False


def kill_process_on_port(port: int) -> bool:
    """Kill any process using the given port (Windows)."""
    try:
        result = subprocess.run(
            f'netstat -ano | findstr ":{port}.*LISTENING"',
            shell=True, capture_output=True, text=True
        )
        killed = False
        for line in result.stdout.strip().split('\n'):
            if line:
                pid = line.strip().split()[-1]
                if pid and pid != '0':
                    subprocess.run(['taskkill', '/F', '/T', '/PID', pid],
                                 capture_output=True)
                    killed = True
        return killed
    except Exception:
        return False


def main():
    print()
    print("=" * 50)
    print("  PubCheck")
    print("=" * 50)
    print()

    # Kill any existing servers
    print("Cleaning up existing servers...")
    kill_process_on_port(BACKEND_PORT)
    for port in range(FRONTEND_PORT_START, FRONTEND_PORT_START + 10):
        kill_process_on_port(port)
    time.sleep(1)

    # Find free ports
    try:
        backend_port = BACKEND_PORT
        if is_port_ready(backend_port):
            kill_process_on_port(backend_port)
            time.sleep(0.5)

        frontend_port = find_free_port(FRONTEND_PORT_START)
    except RuntimeError as e:
        print(f"ERROR: {e}")
        return 1

    processes = []

    try:
        # Start backend
        print(f"Starting backend on port {backend_port}...")
        env = os.environ.copy()
        backend_proc = subprocess.Popen(
            [
                sys.executable, "-m", "uvicorn",
                "app.main:app",
                "--host", "127.0.0.1",
                "--port", str(backend_port),
                "--reload"
            ],
            cwd=PROJECT_ROOT / "backend",
            env=env,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
        )
        processes.append(("Backend", backend_proc))

        # Start frontend with backend port env var
        print(f"Starting frontend on port {frontend_port}...")
        npm_cmd = "npm.cmd" if os.name == 'nt' else "npm"
        env = os.environ.copy()
        env["VITE_BACKEND_PORT"] = str(backend_port)

        frontend_proc = subprocess.Popen(
            [npm_cmd, "run", "dev", "--", "--port", str(frontend_port)],
            cwd=PROJECT_ROOT / "frontend",
            env=env,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
        )
        processes.append(("Frontend", frontend_proc))

        # Wait for servers
        print()
        print("Waiting for servers...")

        if not wait_for_port(backend_port, timeout=30):
            print("ERROR: Backend failed to start!")
            return 1
        print(f"  Backend:  http://localhost:{backend_port}")

        if not wait_for_port(frontend_port, timeout=30):
            print("ERROR: Frontend failed to start!")
            return 1

        frontend_url = f"http://localhost:{frontend_port}"
        print(f"  Frontend: {frontend_url}")

        # Open browser
        print()
        time.sleep(1)
        webbrowser.open(frontend_url)

        print("=" * 50)
        print(f"  App running at {frontend_url}")
        print("  Press Ctrl+C to stop")
        print("=" * 50)
        print()

        # Monitor processes
        while True:
            for name, proc in processes:
                if proc.poll() is not None:
                    print(f"{name} stopped unexpectedly (exit code {proc.returncode})")
                    return 1
            time.sleep(1)

    except KeyboardInterrupt:
        print()
        print("Shutting down...")

    finally:
        for name, proc in processes:
            try:
                if os.name == 'nt':
                    subprocess.run(['taskkill', '/F', '/T', '/PID', str(proc.pid)],
                                 capture_output=True)
                else:
                    proc.terminate()
                    proc.wait(timeout=5)
            except Exception:
                pass
        print("Done.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
