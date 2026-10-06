#!/usr/bin/env python3
"""
capture_terminal.py - Standalone terminal screenshot utility for ai-coding-workshop.
Captures terminal commands, active tmux panes, interactive TUIs, and Opencode sessions
as high-resolution PNG, SVG, or WebP images using Charmbracelet freeze.
"""

import argparse
import datetime
import os
import shutil
import subprocess
import sys
import time
import uuid


def find_freeze() -> str:
    freeze_bin = shutil.which("freeze") or "/home/coder/.pixi/bin/freeze"
    if not os.path.exists(freeze_bin) and not shutil.which("freeze"):
        raise RuntimeError(
            "freeze binary not found. Install it via 'pixi global install freeze'."
        )
    return freeze_bin


def find_default_pane() -> str:
    pane = os.environ.get("TMUX_PANE")
    if pane:
        return pane
    res = subprocess.run(
        ["tmux", "list-panes", "-F", "#{pane_id}"],
        capture_output=True,
        text=True,
    )
    lines = res.stdout.strip().splitlines()
    return lines[0] if lines else "0"


def render_pipe(stdin_data: bytes, output_path: str, window: bool, freeze_bin: str):
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    cmd = [freeze_bin, "-o", output_path]
    if window:
        cmd.append("--window")

    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate(input=stdin_data)
    if p.returncode != 0:
        raise RuntimeError(f"Freeze failed: {stderr.decode('utf-8', errors='replace')}")
    print(f"Screenshot successfully saved to: {output_path}")


def capture_pane_to_file(
    target_pane: str,
    output_path: str,
    window: bool = True,
    scrollback: int = 0,
    freeze_bin: str = "freeze",
):
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    capture_cmd = ["tmux", "capture-pane", "-e", "-p"]
    if scrollback > 0:
        capture_cmd.extend(["-S", f"-{scrollback}"])
    capture_cmd.extend(["-t", target_pane])

    freeze_cmd = [freeze_bin, "-o", output_path]
    if window:
        freeze_cmd.append("--window")

    p1 = subprocess.Popen(capture_cmd, stdout=subprocess.PIPE)
    p2 = subprocess.Popen(freeze_cmd, stdin=p1.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p1.stdout:
        p1.stdout.close()
    stdout, stderr = p2.communicate()

    if p2.returncode != 0:
        err = stderr.decode("utf-8", errors="replace")
        raise RuntimeError(f"Freeze failed: {err}")

    print(f"Screenshot successfully saved to: {output_path}")


def capture_command_execution(
    command_str: str,
    output_path: str,
    window: bool = True,
    freeze_bin: str = "freeze",
):
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    cmd = [freeze_bin, "--execute", command_str, "-o", output_path]
    if window:
        cmd.append("--window")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Freeze failed executing '{command_str}': {res.stderr}")
    print(f"Screenshot successfully saved to: {output_path}")


def capture_interactive_app(
    app_cmd: str,
    output_path: str,
    width: int = 120,
    height: int = 34,
    window: bool = True,
    delay: float = 1.0,
    freeze_bin: str = "freeze",
):
    session_id = f"snap-app-{uuid.uuid4().hex[:8]}"
    try:
        subprocess.run(
            ["tmux", "new-session", "-d", "-s", session_id, "-x", str(width), "-y", str(height), "bash"],
            check=True,
        )
        time.sleep(0.3)
        subprocess.run(["tmux", "send-keys", "-t", session_id, app_cmd, "Enter"], check=True)
        time.sleep(delay)
        capture_pane_to_file(session_id, output_path, window=window, freeze_bin=freeze_bin)
    finally:
        subprocess.run(["tmux", "kill-session", "-t", session_id], capture_output=True)


def capture_opencode_session(
    prompt: str | None,
    output_path: str,
    width: int = 120,
    height: int = 34,
    window: bool = True,
    freeze_bin: str = "freeze",
):
    session_id = f"snap-oc-{uuid.uuid4().hex[:8]}"
    try:
        subprocess.run(
            ["tmux", "new-session", "-d", "-s", session_id, "-x", str(width), "-y", str(height), "bash"],
            check=True,
        )
        time.sleep(0.3)
        subprocess.run(["tmux", "send-keys", "-t", session_id, "opencode", "Enter"], check=True)

        for _ in range(25):
            time.sleep(0.3)
            res = subprocess.run(
                ["tmux", "capture-pane", "-p", "-t", session_id],
                capture_output=True,
                text=True,
            )
            if "Ask anything" in res.stdout or "Build ·" in res.stdout:
                break

        if prompt:
            subprocess.run(["tmux", "send-keys", "-l", "-t", session_id, prompt], check=True)
            time.sleep(0.8)

        capture_pane_to_file(session_id, output_path, window=window, freeze_bin=freeze_bin)
    finally:
        subprocess.run(["tmux", "kill-session", "-t", session_id], capture_output=True)


def main():
    parser = argparse.ArgumentParser(
        description="Capture beautiful screenshots of terminal commands, panes, TUIs, or Opencode sessions."
    )

    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "-x", "--command",
        type=str,
        help="Execute a CLI command and capture its output (e.g. --command 'git status').",
    )
    mode_group.add_argument(
        "--app",
        type=str,
        help="Run an interactive TUI application in a headless session (e.g. --app 'htop').",
    )
    mode_group.add_argument(
        "--opencode",
        action="store_true",
        help="Launch a clean Opencode session to capture.",
    )
    mode_group.add_argument(
        "--pane",
        type=str,
        help="Capture a specific tmux pane target (e.g. --pane '%%0' or --pane 'session:0.0').",
    )
    mode_group.add_argument(
        "--current",
        action="store_true",
        help="Capture the current active tmux pane (default if no other mode is specified).",
    )

    parser.add_argument(
        "--prompt",
        type=str,
        help="Prompt text to type into Opencode input area without submitting (auto-enables --opencode).",
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        help="Output image path (.png, .svg, .webp). Defaults to ~/screenshots/term_<timestamp>.png",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.0,
        help="Delay in seconds before capturing.",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=120,
        help="Terminal column width (default: 120).",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=34,
        help="Terminal row height (default: 34).",
    )
    parser.add_argument(
        "--no-window",
        action="store_true",
        help="Disable window chrome / title bar buttons.",
    )
    parser.add_argument(
        "--scrollback",
        type=int,
        default=0,
        help="Number of lines of scrollback history to capture.",
    )

    args = parser.parse_args()
    freeze_bin = find_freeze()

    if not args.output:
        prefix = "opencode" if (args.opencode or args.prompt) else "terminal"
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output = os.path.expanduser(f"~/screenshots/{prefix}_{timestamp}.png")
    else:
        args.output = os.path.expanduser(args.output)

    if not sys.stdin.isatty():
        stdin_data = sys.stdin.buffer.read()
        if stdin_data:
            render_pipe(stdin_data, args.output, window=not args.no_window, freeze_bin=freeze_bin)
            return

    if args.delay > 0:
        time.sleep(args.delay)

    if args.prompt or args.opencode:
        capture_opencode_session(
            prompt=args.prompt,
            output_path=args.output,
            width=args.width,
            height=args.height,
            window=not args.no_window,
            freeze_bin=freeze_bin,
        )
    elif args.command:
        capture_command_execution(
            command_str=args.command,
            output_path=args.output,
            window=not args.no_window,
            freeze_bin=freeze_bin,
        )
    elif args.app:
        capture_interactive_app(
            app_cmd=args.app,
            output_path=args.output,
            width=args.width,
            height=args.height,
            window=not args.no_window,
            delay=max(args.delay, 1.0),
            freeze_bin=freeze_bin,
        )
    else:
        target = args.pane or find_default_pane()
        capture_pane_to_file(
            target_pane=target,
            output_path=args.output,
            window=not args.no_window,
            scrollback=args.scrollback,
            freeze_bin=freeze_bin,
        )


if __name__ == "__main__":
    main()
