<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://img.shields.io/badge/FindMyPipe-000000?style=for-the-badge&logo=apple&logoColor=white">
    <img src="https://img.shields.io/badge/FindMyPipe-000000?style=for-the-badge&logo=apple&logoColor=white" alt="FindMyPipe">
  </picture>
</p>

<p align="center">
  <strong>Your Apple devices' location, via CLI — for AI agents and humans.</strong>
</p>

<p align="center">
  <a href="#installation"><img src="https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.11+"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="MIT License"></a>
  <a href="./SKILL.md"><img src="https://img.shields.io/badge/AgentSkills.io-compliant-FF6B6B?style=flat-square" alt="AgentSkills.io"></a>
  <img src="https://img.shields.io/badge/CLI-Typer-009688?style=flat-square" alt="CLI">
  <img src="https://img.shields.io/badge/tests-31%20passed-success?style=flat-square" alt="Tests">
</p>

<p align="center">
  🇬🇧 <strong>English</strong> · 🇮🇹 <a href="./README.it.md">Italiano</a>
</p>

---

## What is it?

**FindMyPipe** is a local CLI bridge that queries **Apple Find My** from Linux and returns device locations as **structured JSON**, ready for AI agents, shell scripts, and automation pipelines.

Beyond simply knowing where your devices are, `findmypipe` is designed to power **location-aware workflows**: given the coordinates of a device, an AI agent can query external services to find nearby points of interest — restaurants, hotels, hospitals, transit stops — and build richer, context-aware experiences.

> *"Where's my iPhone?"* · *"Is my MacBook at home?"* · *"Find a coffee shop near my AirPods"* · *"What's the nearest hospital to my iPad?"*

---

## ✨ Features

| Feature | Description |
|---|---|
| **🔍 Locate Apple devices** | iPhone, iPad, Mac, AirPods — real-time position via iCloud |
| **📍 Points of interest nearby** | Feed coordinates to any POI API (Google Places, OSM, Foursquare) to find what's around your device |
| **🖥️ Professional CLI** | Clean structured JSON output on stdout, easy to pipe and parse |
| **🔐 Privacy-first** | Redacted credentials in logs, device IDs replaced by SHA-256 hash |
| **📦 Zero configuration** | Mock mode works out of the box — no Apple ID needed to explore |
| **⏱️ Optional cache** | Configurable TTL to avoid hammering the iCloud API |
| **🧹 Smart filters** | `--skip-offline` and `--max-age` to keep only fresh, relevant data |
| **🔄 Full 2FA login** | Complete Apple authentication flow, interactive 2FA included |
| **🤖 AI agent-ready** | Designed as an [AgentSkills.io](https://agentskills.io)-compliant skill — plug it into any agent framework |

---

## 🤖 What is an AgentSkills.io Skill?

FindMyPipe ships with a [`SKILL.md`](./SKILL.md) definition conforming to the [AgentSkills.io](https://agentskills.io) standard. This means:

- Any AI agent framework that supports the standard can **automatically discover and invoke** this tool
- The skill is **self-describing**: it declares its inputs, outputs, and capabilities in a machine-readable format
- It integrates seamlessly with agents like **Hermes**, custom LLM pipelines, or any shell-capable orchestrator

Think of it as an OpenAPI spec, but for AI agent tools.

---

## 💡 Use Cases

### 🗺️ Find points of interest near your device

```bash
# Get your iPhone's coordinates
COORDS=$(findmy-agent locate "iPhone" --json | jq -r '"\(.asset.latitude),\(.asset.longitude)"')

# Query nearby restaurants (example with Google Places API)
curl "https://maps.googleapis.com/maps/api/place/nearbysearch/json\
?location=$COORDS&radius=500&type=restaurant&key=$GOOGLE_API_KEY" | jq '.results[].name'
```

### 📍 Check if a device is home

```bash
findmy-agent locate "MacBook" --json | jq '.asset | {name, latitude, longitude, last_seen}'
```

### 🔔 Periodic monitoring via cron

```bash
# Every 15 minutes, log all online devices
*/15 * * * * findmy-agent list --json --skip-offline >> /var/log/findmy.log
```

### 🤖 AI agent integration (Hermes)

```yaml
# ~/.hermes/config.yaml
tools:
  - name: findmy_locate
    cmd: "findmy-agent locate \"{{name}}\" --json"
  - name: findmy_list
    cmd: "findmy-agent list --json --skip-offline"
  - name: findmy_doctor
    cmd: "findmy-agent doctor --json"
```

---

## 📦 Installation

### Prerequisites

- **Python 3.11+**
- **Linux** (tested) or **macOS**
- An **Apple ID** with Find My enabled (live mode only)

### Quick install

```bash
git clone https://github.com/corryl/FindMyPipe.git
cd FindMyPipe
python3 -m venv .venv

# Mock mode only (works immediately, no Apple ID needed)
.venv/bin/pip install -e '.[dev]'

# With live iCloud support
.venv/bin/pip install -e '.[dev,live]'

# Verify installation
.venv/bin/findmy-agent doctor --json
```

Expected output:

```json
{
  "cache": {"enabled": false, "state": "empty", "ttl_seconds": 0},
  "live_probe_available": true,
  "ok": true,
  "provider": "mock",
  "secrets_redacted": true,
  "transport": "local"
}
```

---

## ⚙️ Configuration

### Live iCloud mode

```bash
export FINDMY_AGENT_PROVIDER="icloud"
export FINDMY_APPLE_ID="[REDACTED]"
export FINDMY_APPLE_PASSWORD="[REDACTED]"
```

> **🔐** Use an **app-specific password** — Apple ID → Security → App-Specific Passwords.
> Never use your main Apple ID password.

### Optional settings

```bash
export FINDMY_COOKIE_DIR="$HOME/.local/state/findmypipe/icloud"
export FINDMY_CACHE_TTL="300"       # seconds (0 = disabled)
export FINDMY_CACHE_FILE="$HOME/.local/state/findmypipe/cache.json"
```

### Interactive login (first run)

```bash
findmy-agent login --json
# Type your 2FA code when Apple sends it
```

---

## 🖥️ CLI Reference

All commands accept `--json` for structured output.

### `findmy-agent doctor`

Check bridge status and provider availability.

```bash
findmy-agent doctor --json
findmy-agent doctor --provider icloud --json
```

### `findmy-agent list`

List all devices with location, battery level, and last seen time.

```bash
findmy-agent list --json
findmy-agent list --json --skip-offline --max-age 30
findmy-agent list --json --include-raw
```

<details>
<summary><strong>Example output</strong></summary>

```json
{
  "assets": [{
    "id": "icloud:a1b2c3d4e5f6a7b8",
    "name": "iPhone",
    "kind": "device",
    "provider": "icloud",
    "latitude": 45.1234,
    "longitude": 9.5678,
    "accuracy_m": 15.0,
    "battery": 0.85,
    "battery_status": "charged",
    "last_seen": "2025-05-30T12:34:56Z",
    "location_is_old": false
  }]
}
```
</details>

### `findmy-agent locate`

Search for a specific device by name or ID (case-insensitive).

```bash
findmy-agent locate "iPhone" --json
findmy-agent locate "AirPods" --json --skip-offline --max-age 60
```

### `findmy-agent login`

Interactive iCloud authentication with 2FA.

```bash
findmy-agent login --json
```

### Common options

| Option | Description |
|---|---|
| `--provider` | `mock` (default) or `icloud` |
| `--json` | Structured JSON output |
| `--include-raw` | Include redacted raw payload (debug) |
| `--max-age <min>` | Filter positions older than N minutes |
| `--skip-offline` | Exclude offline devices |

### Error format

All errors return a consistent structured format:

```json
{"error": "FINDMY_APPLE_ID not set", "error_type": "configuration_error", "ok": false, "secret_safe": true}
```

---

## 🔐 Privacy & Security

- **No HTTP server** — all I/O on stdio, no open ports, no daemon
- **No webhooks** — outbound polling only toward Apple's servers
- **Credentials never logged** — password, 2FA codes, and tokens always redacted
- **Hashed device IDs** — real identifiers replaced by SHA-256 hash in all output
- **Raw payload hidden by default** — requires explicit `--include-raw` flag
- **Restrictive file permissions** — directories `0700`, files `0600`

```
~/.local/state/findmypipe/
├── icloud/        # Cookies & sessions (0700)
└── cache.json     # Optional cache (0600)
```

---

## 🏗️ Architecture

```
┌──────────────────────────────────────┐
│   AI Agent / Shell Script / Terminal  │
└────────────┬─────────────────────────┘
             │  CLI (stdin/stdout/stderr)
┌────────────▼─────────────────────────┐
│           findmy-agent               │
│                                      │
│  ┌──────────┐   ┌──────────────────┐ │
│  │   CLI    │   │     Cache        │ │
│  │ (Typer)  │   │  (JSON file)     │ │
│  └────┬─────┘   └──────────────────┘ │
│       │                              │
│  ┌────▼──────┐                       │
│  │   Core    │                       │
│  └────┬──────┘                       │
│       │                              │
│  ┌────▼──────┐                       │
│  │ Provider  │                       │
│  │ Mock│iCld │                       │
│  └───────────┘                       │
└────────────┬─────────────────────────┘
             │ HTTPS (outbound only)
┌────────────▼─────────────────────────┐
│         Apple iCloud API             │
└──────────────────────────────────────┘
```

---

## 🧪 Tests

```bash
.venv/bin/pytest -q --tb=short
```

```
tests/test_cache.py ..........
tests/test_cli.py ....
tests/test_core.py ........
tests/test_icloud_provider.py ...
tests/test_provider_factory.py ...
31 passed
```

---

## 📋 Limits & Roadmap

| Aspect | Status |
|---|---|
| iPhone, iPad, Mac, AirPods | ✅ Supported |
| AirTag / Items | ⏳ Not yet supported |
| Linux | ✅ Tested |
| macOS | ✅ Should work |
| Interactive 2FA | ✅ Supported |
| POI integration (built-in) | ⏳ Planned |

---

## 📄 License

MIT — see [LICENSE](LICENSE).

---

<p align="center">
  <sub>
    Built with ❤️ for the AI community · <a href="https://agentskills.io">AgentSkills.io</a> · <a href="./SKILL.md">Skill Definition</a><br>
    <em>Local. Secure. Private. Your data, under your control.</em>
  </sub>
</p>
