# Integration Patterns

## AI agent integration

All commands output JSON on stdout. No HTTP server, no webhooks — pure stdio.

### Pattern 1: Shell tool (Hermes, generic agents)

```yaml
tools:
  - name: findmy_doctor
    cmd: "findmy-agent doctor --json"
    description: "Check Find My bridge status"
  - name: findmy_list
    cmd: "findmy-agent list --json --skip-offline"
    description: "List all online Apple devices with location"
  - name: findmy_locate
    cmd: "findmy-agent locate \"{{name}}\" --json"
    description: "Locate a specific device by name"
```

### Pattern 2: Direct subprocess (Python)

```python
import subprocess, json

result = subprocess.run(
    ["findmy-agent", "list", "--json", "--skip-offline"],
    capture_output=True, text=True, timeout=15
)
data = json.loads(result.stdout)
for device in data["assets"]:
    print(f"{device['name']}: {device['latitude']}, {device['longitude']}")
```

### Pattern 3: Background monitor

```bash
#!/usr/bin/env bash
# Save device positions to a log file every 15 minutes
LOGFILE="$HOME/findmy-history.jsonl"
while true; do
  DATA=$(findmy-agent list --json --skip-offline 2>/dev/null)
  if [ -n "$DATA" ]; then
    echo "$DATA" | jq -c "{timestamp: now, assets: .assets}" >> "$LOGFILE"
  fi
  sleep 900
done
```

---

## Shell usage examples

### Pretty-print with jq

```bash
# Get formatted table of devices
findmy-agent list --json | jq -r '
  .assets[] | [.name, .latitude, .longitude, .battery, .last_seen]
  | @tsv
' | column -t -s $'\t'

# Check if a specific device is online
findmy-agent locate "iPhone" --json | jq -r '
  if .asset == null then "iPhone: not found"
  elif .asset.location_is_old then "iPhone: OFFLINE"
  else "iPhone: \(.asset.latitude), \(.asset.longitude)"
  end
'
```

### Alert when a device goes offline

```bash
#!/usr/bin/env bash
DEVICE="MacBook Pro"
RESULT=$(findmy-agent locate "$DEVICE" --json)
if echo "$RESULT" | jq -e '.asset.location_is_old == true' > /dev/null; then
  echo "[ALERT] $DEVICE went offline at $(date)"
  # send notification: mail, ntfy, pushover, etc.
fi
```

### Calculate distance between two devices

```bash
findmy-agent locate "iPhone" --json > /tmp/iphone.json
findmy-agent locate "MacBook Pro" --json > /tmp/macbook.json

python3 -c "
import json, math

def distance(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))

with open('/tmp/iphone.json') as f:
    iphone = json.load(f)['asset']
with open('/tmp/macbook.json') as f:
    macbook = json.load(f)['asset']

if iphone and macbook and iphone['latitude'] and macbook['latitude']:
    km = distance(iphone['latitude'], iphone['longitude'], macbook['latitude'], macbook['longitude'])
    print(f'Distance: {km:.1f} km')
"
```

---

## Cron automation

```cron
# Check every 15 minutes, log device positions
*/15 * * * * findmy-agent list --json --skip-offline >> /var/log/findmy-devices.log

# Every hour, check if all devices are online
0 * * * * findmy-agent list --json | jq -e '[.assets[] | .location_is_old] | all(.; not)' || echo "Device offline detected" | mail -s "Find My Alert" user@example.com

# Daily cleanup of stale cache files
0 3 * * * findmy-agent doctor --json | jq -e '.cache.state == "stale"' && rm -f /home/user/.local/state/findmypipe/asset_cache.json
```

---

## OpenClaw integration

```json
{
  "name": "findmypipe",
  "env": {
    "FINDMY_APPLE_ID": "[REDACTED]",
    "FINDMY_APPLE_PASSWORD": "[REDACTED]",
    "FINDMY_AGENT_PROVIDER": "icloud",
    "FINDMY_CACHE_TTL": "300"
  },
  "tools": {
    "findmy_doctor": {
      "path": "findmy-agent",
      "args": ["doctor", "--json"]
    },
    "findmy_list": {
      "path": "findmy-agent",
      "args": ["list", "--json", "--skip-offline"]
    },
    "findmy_locate": {
      "path": "findmy-agent",
      "args": ["locate", "{{name}}", "--json"]
    }
  }
}
```

---

## Hermes integration

```yaml
# ~/.hermes/config.yaml
tools:
  - name: findmy_doctor
    cmd: "findmy-agent doctor --json"
  - name: findmy_list
    cmd: "findmy-agent list --json --skip-offline"
  - name: findmy_locate
    cmd: "findmy-agent locate \"{{name}}\" --json"

# Optional: run doctor on startup
startup:
  - cmd: "findmy-agent doctor --json"
```
