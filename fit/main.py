import json
import os
import sys
import warnings

import fitdecode

warnings.simplefilter("ignore")

# Message types kept. file_id + device_info carry watch/manufacturer info.
KEEP = ("file_id", "device_info", "session", "lap", "record")

# Core per-record fields. Edit this list to taste.
RECORD_FIELDS = (
    "timestamp", "distance", "heart_rate", "speed",
    "cadence", "altitude", "power",
    "position_lat", "position_long",
)

# FIT stores position in semicircles; multiply by this to get degrees.
SEMICIRCLE_TO_DEG = 180.0 / (2 ** 31)


def read_run(path):
    data = {}
    with fitdecode.FitReader(path) as fit:
        for f in fit:
            if not isinstance(f, fitdecode.FitDataMessage) or f.name not in KEEP:
                continue
            v = {x.name: x.value for x in f.fields}
            if f.name == "record":
                v = {k: v.get(k) for k in RECORD_FIELDS}
                lat, lon = v.get("position_lat"), v.get("position_long")
                v["position_lat"] = lat * SEMICIRCLE_TO_DEG if lat is not None else None
                v["position_long"] = lon * SEMICIRCLE_TO_DEG if lon is not None else None
            data.setdefault(f.name, []).append(v)
    return data


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "activity.fit"
    data = read_run(path)
    out = os.path.splitext(path)[0] + ".json"
    with open(out, "w") as fp:
        json.dump(data, fp, default=str, indent=2)
    print("saved", out)
