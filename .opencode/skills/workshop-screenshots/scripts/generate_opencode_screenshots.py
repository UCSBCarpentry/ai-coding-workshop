#!/usr/bin/env python3
"""
generate_opencode_screenshots.py - Automated generator for OpenCode lesson screenshots.

Takes clean terminal screenshots for lessons/02_agent.qmd:
  1. images/vscode_opencode.png: OpenCode landing / greeting interface
  2. images/opencode_connect_provider.png: /connect provider selection (DREAM Lab highlighted)
  3. images/opencode_connect_apikey.png: /connect API key entry step
  4. images/opencode_connect_model.png: /models picker with Gemini 3.8 Flash highlighted

All sessions are run in isolated headless tmux instances and cleanly torn down,
preventing any disruption to the active session or configuration.
"""

import os
import shutil
import subprocess
import sys
import time


def find_freeze() -> str:
    freeze_bin = shutil.which("freeze") or "/home/coder/.pixi/bin/freeze"
    if not os.path.exists(freeze_bin) and not shutil.which("freeze"):
        raise RuntimeError(
            "freeze binary not found. Please install freeze or ensure /home/coder/.pixi/bin/freeze exists."
        )
    return freeze_bin


def capture_session(setup_fn, output_path: str, width: int = 100, height: int = 28, freeze_bin: str = "freeze"):
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    session_id = f"snap-ws-{int(time.time() * 1000) % 100000}"

    try:
        subprocess.run(
            ["tmux", "new-session", "-d", "-s", session_id, "-x", str(width), "-y", str(height), "bash"],
            check=True,
        )
        time.sleep(0.3)
        subprocess.run(["tmux", "send-keys", "-t", session_id, "opencode", "Enter"], check=True)

        # Wait for OpenCode TUI initialization
        for _ in range(25):
            time.sleep(0.5)
            res = subprocess.run(["tmux", "capture-pane", "-p", "-t", session_id], capture_output=True, text=True)
            if "Gemini" in res.stdout or "Ask anything" in res.stdout or "Build ·" in res.stdout:
                break

        time.sleep(0.5)
        if setup_fn:
            setup_fn(session_id)
        time.sleep(0.5)

        # Capture via tmux and render with freeze
        cmd_capture = ["tmux", "capture-pane", "-e", "-p", "-t", session_id]
        cmd_freeze = [freeze_bin, "--window", "-o", output_path]
        p1 = subprocess.Popen(cmd_capture, stdout=subprocess.PIPE)
        p2 = subprocess.Popen(cmd_freeze, stdin=p1.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if p1.stdout:
            p1.stdout.close()
        stdout, stderr = p2.communicate()
        if p2.returncode != 0:
            raise RuntimeError(f"freeze failed: {stderr.decode('utf-8', errors='replace')}")

        print(f"Captured: {output_path}")
    finally:
        subprocess.run(["tmux", "kill-session", "-t", session_id], capture_output=True)


def step_provider(s: str):
    subprocess.run(["tmux", "send-keys", "-t", s, "/connect"])
    time.sleep(0.5)
    subprocess.run(["tmux", "send-keys", "-t", s, "Tab"])
    time.sleep(0.5)
    subprocess.run(["tmux", "send-keys", "-t", s, "dream"])
    time.sleep(0.5)


def step_apikey(s: str):
    subprocess.run(["tmux", "send-keys", "-t", s, "/connect"])
    time.sleep(0.5)
    subprocess.run(["tmux", "send-keys", "-t", s, "Tab"])
    time.sleep(0.5)
    subprocess.run(["tmux", "send-keys", "-t", s, "dream"])
    time.sleep(0.5)
    subprocess.run(["tmux", "send-keys", "-t", s, "Enter"])
    time.sleep(0.5)
    subprocess.run(["tmux", "send-keys", "-t", s, "sk-dreamlab-apikey-example-123456789"])
    time.sleep(0.5)


def step_model(s: str):
    subprocess.run(["tmux", "send-keys", "-t", s, "/models"])
    time.sleep(0.5)
    subprocess.run(["tmux", "send-keys", "-t", s, "Tab"])
    time.sleep(0.5)
    subprocess.run(["tmux", "send-keys", "-t", s, "DREAM"])
    time.sleep(0.5)
    # Down arrow twice to move highlight to Gemini 3.8 Flash
    subprocess.run(["tmux", "send-keys", "-t", s, "Down", "Down"])
    time.sleep(0.5)


def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
    images_dir = os.path.join(repo_root, "images")
    freeze_bin = find_freeze()

    targets = [
        ("vscode_opencode.png", None),
        ("opencode_connect_provider.png", step_provider),
        ("opencode_connect_apikey.png", step_apikey),
        ("opencode_connect_model.png", step_model),
    ]

    print("Generating OpenCode lesson screenshots...")
    for filename, setup_fn in targets:
        out_path = os.path.join(images_dir, filename)
        capture_session(setup_fn, out_path, freeze_bin=freeze_bin)
    print("All screenshots generated successfully.")


if __name__ == "__main__":
    main()
