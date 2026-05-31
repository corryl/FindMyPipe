<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://img.shields.io/badge/FindMyPipe-000000?style=for-the-badge&logo=apple&logoColor=white">
    <img src="https://img.shields.io/badge/FindMyPipe-000000?style=for-the-badge&logo=apple&logoColor=white" alt="FindMyPipe">
  </picture>
</p>

<p align="center">
  <strong>La posizione dei tuoi dispositivi Apple, via CLI — per agenti AI e umani.</strong>
</p>

<p align="center">
  <a href="#installazione"><img src="https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.11+"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="MIT License"></a>
  <a href="./SKILL.md"><img src="https://img.shields.io/badge/AgentSkills.io-compliant-FF6B6B?style=flat-square" alt="AgentSkills.io"></a>
  <img src="https://img.shields.io/badge/CLI-Typer-009688?style=flat-square" alt="CLI">
  <img src="https://img.shields.io/badge/tests-31%20passed-success?style=flat-square" alt="Tests">
</p>

<p align="center">
  🇮🇹 <strong>Italiano</strong> · 🇬🇧 <a href="./README.md">English</a>
</p>

---

## Cos'è?

**FindMyPipe** è un bridge locale a riga di comando che interroga **Apple Find My / Dov'è** da Linux e restituisce la posizione dei dispositivi come **JSON strutturato**, pronto per agenti AI, script shell e pipeline di automazione.

Oltre a sapere dove si trovano i tuoi dispositivi, `findmypipe` è progettato per alimentare **workflow location-aware**: date le coordinate di un dispositivo, un agente AI può interrogare servizi esterni per trovare punti di interesse nelle vicinanze — ristoranti, hotel, ospedali, fermate dei mezzi — e costruire esperienze più ricche e contestuali.

> *"Dov'è il mio iPhone?"* · *"Il mio MacBook è a casa?"* · *"Trova un bar vicino ai miei AirPods"* · *"Qual è l'ospedale più vicino al mio iPad?"*

---

## ✨ Funzionalità

| Funzionalità | Descrizione |
|---|---|
| **🔍 Localizza dispositivi Apple** | iPhone, iPad, Mac, AirPods — posizione in tempo reale via iCloud |
| **📍 Punti di interesse nelle vicinanze** | Passa le coordinate a qualsiasi API POI (Google Places, OSM, Foursquare) per trovare cosa c'è intorno al tuo dispositivo |
| **🖥️ CLI professionale** | Output JSON strutturato su stdout, facile da pipe e da parsare |
| **🔐 Privacy-first** | Credenziali redatte nei log, ID dispositivi sostituiti da hash SHA-256 |
| **📦 Zero configurazione** | La modalità mock funziona subito — nessun Apple ID necessario per esplorare |
| **⏱️ Cache opzionale** | TTL configurabile per evitare chiamate eccessive all'API iCloud |
| **🧹 Filtri smart** | `--skip-offline` e `--max-age` per mantenere solo i dati freschi e rilevanti |
| **🔄 Login 2FA completo** | Autenticazione Apple completa con 2FA interattivo incluso |
| **🤖 Pronto per agenti AI** | Progettato come skill [AgentSkills.io](https://agentskills.io)-compliant — integrabile in qualsiasi framework di agenti |

---

## 🤖 Cos'è una Skill AgentSkills.io?

FindMyPipe include una definizione [`SKILL.md`](./SKILL.md) conforme allo standard [AgentSkills.io](https://agentskills.io). Questo significa che:

- Qualsiasi framework di agenti AI che supporta lo standard può **scoprire e invocare automaticamente** questo tool
- La skill è **auto-descrittiva**: dichiara input, output e capacità in formato leggibile dalle macchine
- Si integra senza frizioni con agenti come **Hermes**, pipeline LLM personalizzate, o qualsiasi orchestratore con supporto shell

Pensaci come un'OpenAPI spec, ma per i tool degli agenti AI.

---

## 💡 Casi d'uso

### 🗺️ Trovare punti di interesse vicino al tuo dispositivo

```bash
# Ottieni le coordinate del tuo iPhone
COORDS=$(findmy-agent locate "iPhone" --json | jq -r '"\(.asset.latitude),\(.asset.longitude)"')

# Cerca ristoranti nelle vicinanze (esempio con Google Places API)
curl "https://maps.googleapis.com/maps/api/place/nearbysearch/json\
?location=$COORDS&radius=500&type=restaurant&key=$GOOGLE_API_KEY" | jq '.results[].name'
```

### 📍 Verificare se un dispositivo è a casa

```bash
findmy-agent locate "MacBook" --json | jq '.asset | {name, latitude, longitude, last_seen}'
```

### 🔔 Monitoraggio periodico con cron

```bash
# Ogni 15 minuti, log di tutti i dispositivi online
*/15 * * * * findmy-agent list --json --skip-offline >> /var/log/findmy.log
```

### 🤖 Integrazione con agente AI (Hermes)

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

## 📦 Installazione

### Prerequisiti

- **Python 3.11+**
- **Linux** (testato) o **macOS**
- Un **Apple ID** con Dov'è attivato (solo modalità live)

### Installazione rapida

```bash
git clone https://github.com/corryl/FindMyPipe.git
cd FindMyPipe
python3 -m venv .venv

# Solo modalità mock (funziona subito, nessun Apple ID necessario)
.venv/bin/pip install -e '.[dev]'

# Con supporto live iCloud
.venv/bin/pip install -e '.[dev,live]'

# Verifica installazione
.venv/bin/findmy-agent doctor --json
```

Output atteso:

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

## ⚙️ Configurazione

### Modalità live iCloud

```bash
export FINDMY_AGENT_PROVIDER="icloud"
export FINDMY_APPLE_ID="[REDACTED]"
export FINDMY_APPLE_PASSWORD="[REDACTED]"
```

> **🔐** Usa una **password specifica per app** — Apple ID → Sicurezza → Password specifiche per app.  
> Non usare mai la password principale del tuo Apple ID.

### Impostazioni opzionali

```bash
export FINDMY_COOKIE_DIR="$HOME/.local/state/findmypipe/icloud"
export FINDMY_CACHE_TTL="300"       # secondi (0 = disabilitato)
export FINDMY_CACHE_FILE="$HOME/.local/state/findmypipe/cache.json"
```

### Login interattivo (primo avvio)

```bash
findmy-agent login --json
# Inserisci il codice 2FA quando Apple te lo invia
```

---

## 🖥️ Riferimento CLI

Tutti i comandi accettano `--json` per output strutturato.

### `findmy-agent doctor`

Verifica lo stato del bridge e la disponibilità del provider.

```bash
findmy-agent doctor --json
findmy-agent doctor --provider icloud --json
```

### `findmy-agent list`

Elenca tutti i dispositivi con posizione, livello batteria e ultimo rilevamento.

```bash
findmy-agent list --json
findmy-agent list --json --skip-offline --max-age 30
findmy-agent list --json --include-raw
```

<details>
<summary><strong>Esempio di output</strong></summary>

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

Cerca un dispositivo specifico per nome o ID (case-insensitive).

```bash
findmy-agent locate "iPhone" --json
findmy-agent locate "AirPods" --json --skip-offline --max-age 60
```

### `findmy-agent login`

Autenticazione iCloud interattiva con 2FA.

```bash
findmy-agent login --json
```

### Opzioni comuni

| Opzione | Descrizione |
|---|---|
| `--provider` | `mock` (default) o `icloud` |
| `--json` | Output JSON strutturato |
| `--include-raw` | Includi payload raw redatto (debug) |
| `--max-age <min>` | Filtra posizioni più vecchie di N minuti |
| `--skip-offline` | Escludi dispositivi offline |

### Formato errori

Tutti gli errori restituiscono un formato strutturato consistente:

```json
{"error": "FINDMY_APPLE_ID not set", "error_type": "configuration_error", "ok": false, "secret_safe": true}
```

---

## 🔐 Privacy e sicurezza

- **Nessun server HTTP** — tutto su stdio, nessuna porta in ascolto, nessun daemon
- **Nessun webhook** — solo polling outbound verso i server Apple
- **Credenziali mai loggate** — password, codici 2FA e token sempre redatti
- **ID hashati** — identificatori reali sostituiti da hash SHA-256 in tutto l'output
- **Payload raw nascosto di default** — richiede il flag esplicito `--include-raw`
- **Permessi restrittivi** — directory `0700`, file `0600`

```
~/.local/state/findmypipe/
├── icloud/        # Cookie e sessioni (0700)
└── cache.json     # Cache opzionale (0600)
```

---

## 🏗️ Architettura

```
┌──────────────────────────────────────┐
│   Agente AI / Script Shell / Terminale│
└────────────┬─────────────────────────┘
             │  CLI (stdin/stdout/stderr)
┌────────────▼─────────────────────────┐
│           findmy-agent               │
│                                      │
│  ┌──────────┐   ┌──────────────────┐ │
│  │   CLI    │   │     Cache        │ │
│  │ (Typer)  │   │  (file JSON)     │ │
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
             │ HTTPS (solo outbound)
┌────────────▼─────────────────────────┐
│         Apple iCloud API             │
└──────────────────────────────────────┘
```

---

## 🧪 Test

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

## 📋 Limiti e Roadmap

| Aspetto | Stato |
|---|---|
| iPhone, iPad, Mac, AirPods | ✅ Supportati |
| AirTag / Oggetti | ⏳ Non ancora supportati |
| Linux | ✅ Testato |
| macOS | ✅ Dovrebbe funzionare |
| 2FA interattivo | ✅ Supportato |
| Integrazione POI (built-in) | ⏳ In pianificazione |

---

## 📄 Licenza

MIT — vedi [LICENSE](LICENSE).

---

<p align="center">
  <sub>
    Costruito con ❤️ per la community AI · <a href="https://agentskills.io">AgentSkills.io</a> · <a href="./SKILL.md">Skill Definition</a><br>
    <em>Locale. Sicuro. Privato. I tuoi dati, sotto il tuo controllo.</em>
  </sub>
</p>
