---
name: workshop-screenshots
description: Capture terminal, CLI, and OpenCode screenshots for the workshop documentation without disturbing active sessions or configs. Use when taking screenshots or updating images for lessons, including model pickers and TUI sessions.
---

# Workshop Screenshots

Project-specific skill for generating clean, publication-ready terminal and OpenCode screenshots for the AI Coding Workshop curriculum. Uses isolated headless `tmux` sessions and Charmbracelet's `freeze` renderer.

Supported output formats: **PNG**, **SVG**, **WebP**.

---

## Bundled Scripts

All scripts are located in `scripts/` within this skill directory (`.agents/skills/workshop-screenshots/scripts/`):

1. `generate_opencode_screenshots.py`:
   Automates generation of all OpenCode interface screenshots for `lessons/02_agent.qmd`:
   - `images/vscode_opencode.png`: OpenCode landing / greeting screen
   - `images/opencode_connect_provider.png`: `/connect` provider selection modal
   - `images/opencode_connect_apikey.png`: API key input modal
   - `images/opencode_connect_model.png`: `/models` picker modal with model highlighted

2. `capture_terminal.py`:
   General-purpose terminal capture tool for commands, active panes, interactive TUIs, and staged prompts.

---

## Automated Screenshot Generation

To regenerate all OpenCode lesson screenshots in one step:

```bash
python3 .agents/skills/workshop-screenshots/scripts/generate_opencode_screenshots.py
```

Or via `just`:

```bash
just opencode-screenshots
```

This spins up fresh headless tmux instances, launches `opencode`, navigates the relevant modals, captures high-resolution window screenshots, and tears down the sessions cleanly without modifying current user configurations or active model sessions.

---

## Custom Terminal & Session Captures

### 1. Capturing CLI Commands
Run any shell command and capture formatted output with full syntax colors:

```bash
python3 .agents/skills/workshop-screenshots/scripts/capture_terminal.py \
  --command "git status" \
  -o images/git_status.png
```

Vector format:
```bash
python3 .agents/skills/workshop-screenshots/scripts/capture_terminal.py \
  --command "ls -la" \
  -o images/ls.svg
```

### 2. Capturing an OpenCode Prompt (Staged)
To show a prompt entered into OpenCode without executing it:

```bash
python3 .agents/skills/workshop-screenshots/scripts/capture_terminal.py \
  --prompt "Tell me about the machine you're running on: OS, resources, etc." \
  -o images/staged_prompt.png
```

### 3. Capturing an Existing Pane
Capture what is currently active in a specific tmux pane:

```bash
python3 .agents/skills/workshop-screenshots/scripts/capture_terminal.py \
  --pane "%0" \
  -o images/pane_capture.png
```

### 4. Interactive TUIs & Key Sequences
To capture custom multi-step TUI interactions, script tmux `send-keys` inside an isolated headless session:

```python
import subprocess, time

session = "custom-shot"
subprocess.run(["tmux", "new-session", "-d", "-s", session, "-x", "100", "-y", "28", "bash"])
subprocess.run(["tmux", "send-keys", "-t", session, "opencode", "Enter"])
time.sleep(5)  # Wait for greeting
subprocess.run(["tmux", "send-keys", "-t", session, "/models", "Tab", "DREAM"])
time.sleep(1)

# Capture pane buffer into freeze
p1 = subprocess.Popen(["tmux", "capture-pane", "-e", "-p", "-t", session], stdout=subprocess.PIPE)
subprocess.run(["/home/coder/.pixi/bin/freeze", "--window", "-o", "images/custom.png"], stdin=p1.stdout)
p1.stdout.close()
subprocess.run(["tmux", "kill-session", "-t", session])
```

---

## Safety & Isolation Rules

- **Do Not Change Current Session**: Never invoke commands in the active user shell or current tmux pane that switch the live model or alter `~/.config/opencode/opencode.json` during screenshot tasks.
- **Always Tear Down**: Wrap headless tmux sessions in `try...finally` blocks to ensure background sessions are cleaned up even if capture fails.
