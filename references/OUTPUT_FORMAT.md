# Output Format Reference

All `findmy-agent` commands output structured JSON. This document describes every field.

---

## `doctor`

```json
{
  "ok": true,
  "provider": "mock",
  "transport": "local",
  "secrets_redacted": true,
  "live_probe_available": true,
  "cache": {
    "enabled": false,
    "ttl_seconds": 0,
    "path": "/home/user/.local/state/findmypipe/asset_cache.json",
    "state": "empty"
  }
}
```

| Field | Type | Description |
|---|---|---|
| `ok` | bool | Always `true` on success |
| `provider` | string | Active provider: `"mock"` or `"icloud"` |
| `transport` | string | Always `"local"` (stdio only) |
| `secrets_redacted` | bool | Always `true` — credentials never leak |
| `live_probe_available` | bool | Whether pyicloud package is installed (`[live]` extra) |
| `cache.enabled` | bool | Whether cache is active (`FINDMY_CACHE_TTL > 0`) |
| `cache.ttl_seconds` | int | Cache TTL in seconds. `0` means disabled |
| `cache.path` | string | Absolute path to cache JSON file |
| `cache.state` | string | `"empty"` (no cache file), `"fresh"` (within TTL), `"stale"` (expired), `"corrupt"` (parse error) |
| `cache.age_seconds` | float | *(present only when state is fresh/stale)* Age of cache in seconds |
| `cache.asset_count` | int | *(present only when state is fresh/stale)* Number of cached assets |

---

## `list`

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
    }
  ]
}
```

### Per-asset fields

| Field | Type | Always present | Description |
|---|---|---|---|
| `id` | string | ✅ | Stable hash ID: `icloud:<sha256:16>`. Same device always has same hash. |
| `name` | string | ✅ | Device display name (e.g., "iPhone 15 Pro", "MacBook Pro M4"). Matches what you see in Apple's Find My app. |
| `kind` | string | ✅ | `"device"` for devices, `"unknown"` for unclassified. *(AirTag/item support planned)* |
| `provider` | string | ✅ | Source provider: `"mock"`, `"icloud"` |
| `latitude` | float\|null | ✅ | Decimal latitude. `null` when unavailable (device offline or no location data). |
| `longitude` | float\|null | ✅ | Decimal longitude. `null` when unavailable. |
| `accuracy_m` | float\|null | ✅ | Horizontal accuracy in meters. `null` when unknown. Smaller = more precise. |
| `battery` | float\|null | ✅ | Battery level 0.0–1.0. `null` when unknown. Multiply by 100 for percentage. |
| `battery_status` | string | ✅ | `"charged"`, `"charging"`, `"unknown"`, or other Apple status strings. |
| `last_seen` | string\|null | ✅ | ISO 8601 timestamp in UTC (suffix `Z`). `null` when never seen. |
| `location_is_old` | bool\|null | ✅ | `true` when Apple reports the location is stale (device offline). `null` when unknown. |
| `raw_redacted` | dict | ❌ | *(Only with `--include-raw`)* Redacted raw pyicloud payload for debugging. Sensitive fields replaced with `"<REDACTED>"`. |

### Important notes

- **Empty list** (`{"assets": []}`) means no devices found or no devices visible.
- In **mock mode** (`--provider mock`, default), there are zero devices. Use `--provider icloud` for real data.
- Raw payload is **never included** unless `--include-raw` is explicitly passed. This is by design for privacy.

---

## `locate`

```json
{
  "asset": {
    "id": "icloud:a1b2c3d4e5f6a7b8",
    "name": "iPhone 15 Pro",
    "latitude": 45.4642,
    "longitude": 9.1900,
    "battery": 0.85,
    ...
  }
}
```

| Field | Type | Description |
|---|---|---|
| `asset` | object\|null | Full device object (same schema as `list` asset) **or** `null` if not found |

- Match is **case-insensitive** and **exact** (full name or ID match).
- If you need substring search, use `list` and filter client-side.

---

## `login`

**Success:**
```json
{
  "ok": true,
  "provider": "icloud",
  "assets_seen": 3,
  "cookie_dir": "/home/user/.local/state/findmypipe/icloud",
  "secret_safe": true
}
```

| Field | Type | Description |
|---|---|---|
| `ok` | bool | `true` on successful authentication |
| `provider` | string | Always `"icloud"` |
| `assets_seen` | int | Number of devices found after authentication |
| `cookie_dir` | string | Path to session cookie directory |
| `secret_safe` | bool | Always `true` |

**Error:**
```json
{
  "ok": false,
  "error": "2FA_REQUIRED",
  "error_type": "login_error",
  "secret_safe": true,
  "next_step": "Rerun with --code <2FA>"
}
```

---

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Success |
| `2` | Error (provider config, login failure, etc.) |
| `1` | Unexpected runtime error (bug) |
