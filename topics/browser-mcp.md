# Browser MCP Integration with Chrome DevTools

This guide covers how to set up and configure the Chrome DevTools Model Context
Protocol (MCP) server for opencode, enabling browser automation and screenshots.

---

## 1. Installing Headless Chrome

Chrome DevTools MCP requires a running Chrome or Chromium instance. In
non-graphical environments (like Coder Workspaces), Chrome must run in
**headless** mode.

Install the official Google Chrome package:
```bash
sudo apt-get update
sudo apt-get install -y wget curl gnupg

# Download and install Google Chrome Stable
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt-get install -y ./google-chrome-stable_current_amd64.deb
```

## 2. Installing Node.js & npm

The Chrome DevTools MCP server runs on Node.js and is executed via `npx` (which
comes bundled with npm).

Install them directly from the standard Ubuntu repositories:

```bash
sudo apt-get update
sudo apt-get install -y nodejs npm
```

## 3. Configuring opencode

Once Chrome and npm are installed, register the `chrome-devtools` server in your
opencode configuration file.

### Configuration Path
You can add this to your:
- **Global Config:** `~/.config/opencode/opencode.json`
- **Project Config:** `opencode.json` (in your workspace root)

### JSON Configuration
Add the following configuration block under the `"mcp"` key:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "chrome-devtools": {
      "type": "local",
      "command": ["npx", "-y", "chrome-devtools-mcp@latest", "--headless"],
      "enabled": true
    }
  }
}
```
The `--headless` flag is crucial when running opencode in a virtualized or
containerized terminal context that lacks a graphical display.


## 4. Verification

After saving the configuration, **quit and restart opencode**. Test the setup by asking:

```md
Take a screenshot of https://www.library.ucsb.edu
```
