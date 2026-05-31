# Error Handling Reference

All errors follow a consistent JSON structure:

```json
{
  "ok": false,
  "error": "Human-readable message",
  "error_type": "machine_readable_type",
  "secret_safe": true
}
```

---

## Error types

### `configuration_error`

The environment or provider is misconfigured.

| Example error | Cause | Fix |
|---|---|---|
| `Unknown provider: bad` | `--provider` set to an invalid value | Use `mock` or `icloud` |
| `FINDMY_APPLE_ID not set` | Missing env var for live mode | `export FINDMY_APPLE_ID="[REDACTED]"` |
| `FINDMY_APPLE_PASSWORD not set` | Missing env var for live mode | `export FINDMY_APPLE_PASSWORD="[REDACTED]"` |
| `pyicloud is not installed` | Missing `[live]` extras | `pip install findmypipe[live]` |

### `login_error`

iCloud authentication failed.

| Example error | Cause | Fix |
|---|---|---|
| `2FA_REQUIRED` | Apple requires 2FA code | Run `login --code <code>` or pass `--code` |
| `Invalid Apple ID or password` | Wrong credentials | Double-check Apple ID and app-specific password |
| `Authentication took too long` | 2FA timeout | Restart login with a fresh 2FA code |
| `Too many login attempts` | Rate limited by Apple | Wait 15–30 minutes before retrying |

### `not_found`

*(Not yet used — reserved for future locate-by-ID API calls)*

---

## Agent decision tree

When a CLI command fails, check the `error_type` field to determine next action:

```
error_type = "configuration_error"
  → Check environment variables (FINDMY_APPLE_ID, FINDMY_APPLE_PASSWORD)
  → Verify provider name is "mock" or "icloud"
  → If pyicloud missing, install with [live] extras

error_type = "login_error"
  → If "2FA_REQUIRED", prompt user for 2FA code and re-run with --code
  → If invalid credentials, ask user to verify Apple ID & app-specific password
  → If rate-limited, wait and retry

Any error with "secret_safe": true
  → Safe to display the error message to the user (no secrets leaked)
```

---

## When to retry vs. fail

| Scenario | Action |
|---|---|
| `2FA_REQUIRED` | Ask user for code → retry with `--code <code>` |
| Network timeout (exit 1) | Wait 5s → retry up to 3 times |
| Configuration error | Do NOT retry — fix config first |
| Rate limited | Wait 15 min → retry once |
| "Invalid Apple ID or password" | Ask user to regenerate app-specific password |
