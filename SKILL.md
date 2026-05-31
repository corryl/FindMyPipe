---
name: findmypipe
description: >
  Locate Apple devices (iPhone, iPad, Mac, AirPods) via iCloud Find My using the
  `findmy-agent` CLI. Use this skill when the user asks to find an Apple device,
  check iPhone/iPad/Mac/AirPods location, locate lost AirPods, "Where's my iPhone",
  "Dov'è il mio Mac", verify if a device is home vs away, or check if devices are
  online. Outputs structured JSON. Supports offline filtering and optional cache.
license: MIT
metadata:
  author: "Corrado + Agata"
  version: "0.1.0"
compatibility: >
  Requires Python 3.11+ and Linux or macOS. Live mode needs an Apple ID (app-specific
  password required). The pyicloud package is bundled with the [live] extra.
  No HTTP server or open ports -- all output on stdio.
---

# FindMyPipe

FindMyPipe is a bridge that exposes **Apple Find My / Dov'è** data as a CLI tool for AI agents.

All commands produce structured JSON on stdout. There is **no HTTP server, no open
ports, no daemon**. Everything runs locally on-demand.

## Quick reference

| Goal | Command |
|---|---|
| Check if the bridge works | `findmy-agent doctor --json` |
| List all devices with location | `findmy-agent list --json` |
| Find a specific device | `findmy-agent locate "iPhone" --json` |
| Authenticate with Apple | `findmy-agent login --json` |
| List only online devices | `findmy-agent list --json --skip-offline` |
| List devices seen in last 30 min | `findmy-agent list --json --max-age 30` |

> **Entry point**: `findmy-agent` (after pip install). The `scripts/findmy-agent` wrapper
> tries the installed binary first, then falls back to `python -m findmy_agent_bridge.cli`.

---

## Agent decision flow

```
User asks about device location
  │
  ├─ Is this the first time?
  │   └─ Yes → Run doctor to verify bridge state
  │
  ├─ Does the user want ALL devices?
  │   └─ Yes → Run findmy-agent list --json
  │            Optionally apply --skip-offline for online-only
  │            Optionally apply --max-age N for recency filter
  │
  ├─ Does the user want ONE specific device?
  │   └─ Yes → Run findmy-agent locate "Device Name" --json
  │            │
  │            ├─ Found → Return device data to user
  │            │
  │            └─ null  → Exact name mismatch. Run findmy-agent list --json
  │                       to discover exact device names, then retry locate
  │                       with the correct full name
  │
  ├─ Does the user want to check if a device is home/away?
  │   └─ Yes → Run locate for the device and check latitude/longitude
  │            against known home coordinates
  │
  ├─ Did the command fail with an error?
  │   └─ Yes → Check error_type (configuration_error vs login_error)
  │            See references/ERRORS.md for resolution
  │
  └─ Does the user want to set up live mode?
      └─ Yes → Guide them through login with 2FA
```

---

## Install & setup

```bash
git clone <repo-url>
cd FindMyPipe
python3 -m venv .venv

# Mock mode (immediate, no Apple credentials)
.venv/bin/pip install -e '.[dev]'

# Live mode (requires Apple ID)
.venv/bin/pip install -e '.[dev,live]'

# Verify installation
.venv/bin/findmy-agent doctor --json
```

### Environment variables for live mode

| Variable | Required | Default | Description |
|---|---|---|---|
| `FINDMY_AGENT_PROVIDER` | Yes* | `mock` | Set to `icloud` for live data |
| `FINDMY_APPLE_ID` | Yes* | — | Apple ID email |
| `FINDMY_APPLE_PASSWORD` | Yes* | — | App-specific password (not the account password!) |
| `FINDMY_CACHE_TTL` | No | `0` (disabled) | Cache TTL in seconds (e.g., `300` = 5 min) |
| `FINDMY_CACHE_FILE` | No | `~/.local/state/.../cache.json` | Custom cache file path |
| `FINDMY_COOKIE_DIR` | No | `~/.local/state/.../icloud` | iCloud session directory |

> **\*** Only required for live mode. In mock mode no configuration is needed.
>
> **Important**: Use an **app-specific password** generated from Apple ID security
> settings. Your normal Apple ID password will not work with pyicloud.

### Interactive 2FA login

```bash
findmy-agent login --json
# When prompted, enter the 2FA code shown on your Apple device
```

---

## Commands in detail

### `doctor` — Check bridge health

```bash
findmy-agent doctor --json
findmy-agent doctor --provider icloud --json
```

Output (doc — see [references/OUTPUT_FORMAT.md](references/OUTPUT_FORMAT.md) for all fields):

```json
{
  "cache": {"enabled": false, "path": ".../asset_cache.json", "state": "empty", "ttl_seconds": 0},
  "live_probe_available": true,
  "ok": true,
  "provider": "mock",
  "secrets_redacted": true,
  "transport": "local"
}
```

**When to use**: Always run this first if you're unsure whether the bridge is
configured. Check `provider` to see if it's `mock` (no real data) or `icloud`
(live). Check `live_probe_available` to see if pyicloud is installed.

---

### `list` — List all devices

```bash
# All devices
findmy-agent list --json

# Online only, seen within last 30 minutes
findmy-agent list --json --skip-offline --max-age 30

# With redacted raw payload (debugging)
findmy-agent list --json --include-raw
```

**Real-world output** (with live iCloud — see [references/OUTPUT_FORMAT.md](references/OUTPUT_FORMAT.md)):

```json
{
  "assets": [
    {
      "id": "icloud:a1b2c3d4e5f6a7b8",
      "name": "iPhone 15 Pro",
      "kind": "device",
      "provider": "icloud",
      "latitude": 45.4642,
      "longitude": 9.1900,
      "accuracy_m": 15.0,
      "battery": 0.85,
      "battery_status": "charged",
      "last_seen": "2025-05-30T12:34:56Z",
      "location_is_old": false
    },
    {
      "id": "icloud:9b8a7c6d5e4f3a2b",
      "name": "MacBook Pro",
      "kind": "device",
      "provider": "icloud",
      "latitude": null,
      "longitude": null,
      "accuracy_m": null,
      "battery": null,
      "battery_status": "unknown",
      "last_seen": "2025-05-29T08:00:00Z",
      "location_is_old": true
    },
    {
      "id": "icloud:f1e2d3c4b5a60798",
      "name": "AirPods Pro",
      "kind": "device",
      "provider": "icloud",
      "latitude": 45.4645,
      "longitude": 9.1905,
      "accuracy_m": 25.0,
      "battery": 0.32,
      "battery_status": "charging",
      "last_seen": "2025-05-30T12:30:00Z",
      "location_is_old": false
    }
  ]
}
```

In **mock mode** (default), assets will be an empty array: `{"assets": []}`.

**When to use**: For "Where are all my devices?", "Show me my stuff on a map",
"Check if all devices are home", "Which devices are online?".

**How to check if a device is home**:

```json
{
  "id": "icloud:a1b2c3d4e5f6a7b8",
  "name": "iPhone 15 Pro",
  "latitude": 45.4642,
  "longitude": 9.1900,
  "location_is_old": false
}
```

Compare `latitude`/`longitude` against the user's home coordinates. If
`location_is_old` is `true`, the position is stale — the device was last seen
at `last_seen` and may have moved since.

---

### `locate` — Find a specific device

```bash
findmy-agent locate "iPhone 15 Pro" --json
findmy-agent locate "AirPods Pro" --json --skip-offline --max-age 60
```

Output:

```json
{
  "asset": {
    "id": "icloud:a1b2c3d4e5f6a7b8",
    "name": "iPhone 15 Pro",
    "kind": "device",
    "provider": "icloud",
    "latitude": 45.4642,
    "longitude": 9.1900,
    "accuracy_m": 15.0,
    "battery": 0.85,
    "battery_status": "charged",
    "last_seen": "2025-05-30T12:34:56Z",
    "location_is_old": false
  }
}
```

If the device is not found: `{"asset": null}`

**Matching rules**:
- Case-insensitive (`"iphone"` matches `"iPhone 15 Pro"`)
- **Exact match** on full name or ID (`"iPhone"` does NOT match `"iPhone 15 Pro"`)
- If the user says "find my iPhone", try `"iPhone"` first, then try broader
  searches like `"iPhone 15"`, `"iPhone"`, etc. using `list` and filtering
- Use [references/ERRORS.md](references/ERRORS.md) if the command fails

**When to use**: For "Where is my iPhone?", "Find my MacBook", "Are my AirPods
at home?", "Is my iPad with me?", "Find my device".

**How to interpret results**:

| Scenario | `asset` value | Meaning |
|---|---|---|
| Device located | Full object | Device found, has latest known location |
| Device not found | `null` | No device matches that name/ID |
| Device is offline | `location_is_old: true` | Location is from `last_seen`, may be outdated |

---

### `login` — Authenticate with iCloud

```bash
findmy-agent login --json
```

Success output:

```json
{
  "assets_seen": 3,
  "cookie_dir": ".../icloud",
  "ok": true,
  "provider": "icloud",
  "secret_safe": true
}
```

2FA required output:

```json
{
  "error": "2FA_REQUIRED",
  "error_type": "login_error",
  "next_step": "Rerun with --code <2FA>",
  "ok": false,
  "secret_safe": true
}
```

**Required only once** — after successful login with 2FA, session cookies are
saved to `cookie_dir`. Subsequent `list`/`locate` calls reuse the session.

---

## Real-world scenarios

### Scenario 1: User asks "Where is my iPhone?"

```bash
# 1. Try locate with the device name
findmy-agent locate "iPhone" --json

# 2. If null, discover the exact name
findmy-agent list --json
# → e.g. "iPhone 15 Pro"

# 3. Retry with exact name
findmy-agent locate "iPhone 15 Pro" --json
```

If still not found, the device might be offline or not visible to the account.

### Scenario 2: User asks "Are all my devices at home?"

```bash
findmy-agent list --json --skip-offline
```

Check each asset's `latitude`/`longitude` against the user's home address.
If `location_is_old` is `true`, the device may have moved since last seen.

### Scenario 3: User asks "Is my MacBook battery low?"

```bash
findmy-agent locate "MacBook Pro" --json
```

Check `battery` (0.0-1.0). Values below 0.2 indicate critically low battery.
`battery_status` tells you if it's currently charging.

### Scenario 4: First-time setup

```bash
# 1. Check current state
findmy-agent doctor --json
# → provider is "mock" — no real data

# 2. Set environment variables
export FINDMY_AGENT_PROVIDER=icloud
export FINDMY_APPLE_ID="[REDACTED]"
export FINDMY_APPLE_PASSWORD="[REDACTED]"

# 3. Authenticate (may trigger 2FA)
findmy-agent login --json

# 4. Verify it works
findmy-agent doctor --json
# → provider is now "icloud"
findmy-agent list --json
# → assets show real devices
```

### Scenario 5: Automation / monitoring

```bash
# Check periodically that a specific device is online
DEVICE="MacBook Pro"
STATUS=$(findmy-agent locate "$DEVICE" --json)
if echo "$STATUS" | grep -q '"location_is_old": true'; then
  echo "$DEVICE went offline at $(date)"
fi
```

See [references/INTEGRATION.md](references/INTEGRATION.md) for cron, Hermes,
OpenClaw, and advanced shell patterns.

---

## Cache behavior

- **Disabled** by default (`FINDMY_CACHE_TTL=0`)
- When enabled, data is cached as JSON in `~/.local/state/findmypipe/asset_cache.json`
- On TTL expiry, the next call refreshes from iCloud
- Cache file permissions: directory `0700`, file `0600`
- Check cache state via `doctor` output (`cache.state`: `empty`, `fresh`, `stale`, `corrupt`)

See [references/OUTPUT_FORMAT.md](references/OUTPUT_FORMAT.md) for all cache
fields in the doctor response.

---

## Common errors

All errors return consistent JSON (see [references/ERRORS.md](references/ERRORS.md)):

```json
{
  "error": "FINDMY_APPLE_ID not set",
  "error_type": "configuration_error",
  "ok": false,
  "secret_safe": true
}
```

### Quick fixes

| Error | Likely cause | Fix |
|---|---|---|
| `Unknown provider: bad` | Invalid `--provider` value | Use `mock` or `icloud` |
| `FINDMY_APPLE_ID not set` | Missing env var | `export FINDMY_APPLE_ID="[REDACTED]"` |
| `FINDMY_APPLE_PASSWORD not set` | Missing env var | `export FINDMY_APPLE_PASSWORD="[REDACTED]"` |
| `pyicloud is not installed` | Missing `[live]` extra | `pip install 'findmypipe[live]'` |
| `2FA_REQUIRED` | 2FA challenge | Run `login --code <code>` |
| Server returns exit code 2 | Config or auth error | Check `error_type` field |
| Empty `{"assets": []}` in icloud mode | No devices or bad session | Check credentials, run `login` |

All errors have `"secret_safe": true` — you can safely display the error
message to the user. No credentials or tokens are leaked.

---

## Agent notes

- **Default provider is `mock`** — until the user sets `FINDMY_AGENT_PROVIDER=icloud`,
  `list` returns `[]` and `locate` returns `null`. This is by design.
- **Raw payload is always omitted** unless `--include-raw` is explicitly passed.
- **Device IDs are hashed**: `icloud:<sha256:16>`. Same device = same hash
  across runs. Human-readable names are safe to use.
- **Credentials are never logged** — password, 2FA codes, Apple ID, tokens are
  always redacted from output and logs.
- **Session cookies persist** after successful `login`. Subsequent calls reuse
  them automatically until they expire (typically ~2 months).
- **AirTag/item support** is not yet available (tracked for future releases).
- **Cache is optional** and off by default. Enable with `FINDMY_CACHE_TTL=300`
  for 5-minute cache.
- **Filters compose**: `--skip-offline --max-age 30` together show only online
  devices seen in the last 30 minutes.
- **For partial name matching**: `locate` does exact match (case-insensitive).
  If not found, use `list` and filter the results client-side by substring.

---

## File structure

```
findmypipe/
├── SKILL.md                 ← This file — agent instructions
├── scripts/
│   └── findmy-agent         ← Executable entry point
├── references/
│   ├── ERRORS.md            ← Error handling reference
│   ├── OUTPUT_FORMAT.md     ← Full field-by-field output docs
│   └── INTEGRATION.md       ← Agent, shell, cron integration
├── assets/                  ← Templates & resources
├── src/findmy_agent_bridge/ ← Python source
└── tests/                   ← Automated test suite
```
