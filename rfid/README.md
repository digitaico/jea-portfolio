# Race Timing Service — v1 Monolith

A single-script RFID-based race timing system. Reads tags via LLRP (sllurp),
detects the most probable crossing time per checkpoint, and writes one JSON
file per tag — updated progressively as the runner advances through the course.

---

## Scope (v1)

| In scope | Out of scope |
|---|---|
| RFID reading via sllurp / LLRP | MQTT / cloud publishing |
| Multi-checkpoint support | Microservices / EDA |
| Crossing detection (peak / centroid) | Bib-to-EPC mapping |
| Per-tag JSON output | Web UI / dashboard |
| Single reader, N antennas | Multi-reader sync |

---

## How it works

```
Reader (LLRP/TCP)
      │
      ▼
RFIDListener          ← connects to reader, streams raw TagRead events
      │
      ▼
CrossingBuffer        ← groups reads by (epc, checkpoint_id)
      │  settles after debounce_window_seconds with no new reads
      ▼
CrossingDetector      ← picks best timestamp (peak RSSI or centroid)
      │
      ▼
PayloadBuilder        ← assembles / updates the tag's full JSON payload
      │
      ▼
FileWriter            ← writes/overwrites outputs/<EPC>.json
```

---

## Crossing Detection Algorithms

### Peak RSSI
Selects the single read with the highest RSSI value.
Best for: fast crossings, narrow antenna mats.

### Centroid (default)
Computes RSSI-weighted average of timestamps:

```
t_crossing = Σ(timestamp_i × rssi_linear_i) / Σ(rssi_linear_i)
```

Where `rssi_linear = 10^(rssi_dbm / 10)`.
Best for: standard race mats, reduces noise.

---

## Checkpoint lifecycle per tag

```
no file          → tag read at START   → file created  (status: running)
status: running  → tag read at KM5     → file updated  (status: running)
status: running  → tag read at FINISH  → file updated  (status: finished)
```

Special statuses:
- `pending`  — reads arriving, buffer not yet settled
- `running`  — confirmed start crossing, no finish yet
- `finished` — confirmed finish crossing
- `dns`      — finish detected without prior start

---

## Crossing validity rules

1. Reads below `rssi_floor_dbm` are discarded.
2. A buffer needs at least `min_reads_to_confirm` reads to be valid.
3. Crossings are only accepted in **distance order** — a checkpoint at 5 km
   is ignored if start has not been confirmed yet.
4. A new crossing at the same checkpoint within `debounce_window_seconds`
   is ignored (prevents double-counting on slow runners or officials).

---

## Output JSON

One file per tag: `outputs/<EPC>.json`

```json
{
  "epc": "E2801190200052062580DF3D",
  "status": "finished",
  "crossings": [
    {
      "checkpoint_id": "start",
      "distance_meters": 0,
      "timestamp": "2025-05-28T08:00:01.342Z",
      "rssi_dbm": -42.5,
      "algorithm": "centroid",
      "read_count": 12
    },
    {
      "checkpoint_id": "finish",
      "distance_meters": 21097,
      "timestamp": "2025-05-28T10:05:33.881Z",
      "rssi_dbm": -38.1,
      "algorithm": "centroid",
      "read_count": 9
    }
  ],
  "elapsed_seconds": 7532.539,
  "written_at": "2025-05-28T10:05:34.001Z"
}
```

---

## Project layout

```
race_timing/
├── config.yaml               ← all configuration, no hardcoded values
├── main.py                   ← entry point
├── app.py                    ← RaceTimingOrchestrator (wires everything)
├── models/
│   ├── tag_read.py           ← TagRead dataclass (single raw read)
│   └── payload.py            ← TagPayload, Crossing dataclasses
├── core/
│   ├── crossing_buffer.py    ← CrossingBuffer (per epc/checkpoint)
│   ├── crossing_detector.py  ← CrossingDetector (peak | centroid)
│   └── payload_builder.py    ← PayloadBuilder
├── io/
│   ├── rfid_listener.py      ← RFIDListener (sllurp wrapper)
│   └── file_writer.py        ← FileWriter
└── README.md
```

---

## Configuration — config.yaml

```yaml
reader:
  host: "192.168.1.100"
  port: 5084                    # default LLRP port
  tx_power: 30                  # dBm, reader-dependent
  mode_index: 0                 # reader sensitivity mode

checkpoints:
  - id: "start"
    distance_meters: 0
    antenna_ports: [1]
    algorithm: "centroid"       # peak | centroid
  - id: "finish"
    distance_meters: 21097
    antenna_ports: [1]          # same physical antenna in dev, different port in prod
    algorithm: "centroid"

crossing:
  rssi_floor_dbm: -65           # reads weaker than this are discarded
  min_reads_to_confirm: 3       # minimum reads before a crossing is valid
  debounce_window_seconds: 30   # silence window to settle a crossing

output:
  directory: "./outputs"
```

> **Dev note:** In development with one reader and one antenna, both
> `start` and `finish` checkpoints point to `antenna_ports: [1]`.
> The system distinguishes them by time order — first confirmed crossing
> is start, second is finish. Add a `dev_mode: true` flag to
> enable this single-antenna mode explicitly.

---

## Dependencies

```
sllurp          — LLRP reader communication
pydantic        — config and model validation
pyyaml          — config file parsing
asyncio         — async event loop
```

Install:
```bash
pip install sllurp pydantic pyyaml
```

---

## Running

```bash
python main.py --config config.yaml
```

Output files land in `./outputs/` (configurable).
Each file is named `<EPC>.json` and updated in place.

---

## v2 Roadmap (not in this version)

- MQTT publish to cloud
- Multi-reader clock synchronisation
- Bib ↔ EPC mapping table
- REST API for live results
- EDA / microservices split
- Docker + docker-compose
