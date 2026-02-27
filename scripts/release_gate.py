#!/usr/bin/env python3
"""
Pre-deploy release gate: run security gate, lint, and full tests.
Run every time before deploy. CI runs these on push; use this locally to pass the same checks.
Usage: python scripts/release_gate.py
"""
import os
import subprocess
import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
os.chdir(_root)


def run(name: str, cmd: list) -> bool:
    print(f"\n--- {name} ---")
    r = subprocess.run(cmd)
    if r.returncode != 0:
        print(f"[FAIL] {name} exited with {r.returncode}")
        return False
    return True


def main():
    ok = True
    ok = run("Security gate", [sys.executable, "scripts/security_gate.py"]) and ok
    ok = run("Lint (ruff)", [sys.executable, "-m", "pip", "install", "-q", "ruff"]) and ok
    if ok:
        ok = run("Ruff check", [sys.executable, "-m", "ruff", "check", "."]) and ok
    ok = run("Tests", [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short", "-W", "default"]) and ok
    if not ok:
        print("\n[RELEASE GATE FAILED] Fix the above before deploying.")
        return 1
    print("\n[RELEASE GATE PASSED] Safe to deploy. Then verify health/ready/startup on the deployed app.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
