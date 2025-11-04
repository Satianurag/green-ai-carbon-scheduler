from __future__ import annotations
import os
import csv
import time
import json
from datetime import datetime, timezone
from typing import Dict, Optional

from .measure import track_execution
from .ci_provider import fetch_uk_current_ci, read_meta_csv
from .pipeline import train_and_eval

EVIDENCE_HEADER = [
    "run_id",
    "phase",
    "task",
    "dataset",
    "hardware",
    "region",
    "timestamp_utc",
    "kWh",
    "kgCO2e",
    "water_L",
    "runtime_s",
    "quality_metric_name",
    "quality_metric_value",
    "notes",
]


def _append_row(path: str, row: Dict):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    exists = os.path.exists(path)
    with open(path, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=EVIDENCE_HEADER)
        if not exists:
            w.writeheader()
        w.writerow(row)


def _detect_hardware() -> str:
    import platform
    cpu = platform.processor() or "CPU"
    mach = platform.machine() or "x86_64"
    return f"{cpu}_{mach}"


def run_once(
    *,
    mode: str,
    dataset_csv: Optional[str],
    out_path: str,
    threshold: int,
    defer_seconds: int,
    assumed_kw: float,
    ci_mode: str = "live",
    ci_csv_path: Optional[str] = None,
    task: str = "regression",
    region: str = "GB",
    notes: str = "",
    log_decision_path: Optional[str] = None,
) -> Dict:
    assert mode in {"baseline", "optimized"}
    # Determine carbon intensity source
    if ci_mode == "csv":
        if not ci_csv_path:
            raise ValueError("--ci csv requires --ci-csv metaData.csv path")
        meta = read_meta_csv(ci_csv_path)
        col = "carbon_intensity_gco2_per_kwh"
        if mode == "baseline":
            ci = float(meta[col].mean())
        else:
            ci = float(meta[col].min())
    else:
        ci = float(fetch_uk_current_ci())
    decision = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "region": region,
        "naive_ci": int(ci),
        "threshold": int(threshold),
        "action": "run" if ci < threshold else "defer",
    }

    if ci >= threshold and defer_seconds > 0 and ci_mode == "live":
        time.sleep(min(defer_seconds, 300))  # cap to 5 minutes in demo
        ci = float(fetch_uk_current_ci())
        decision["chosen_ci"] = int(ci)
        decision["deferred_seconds"] = min(defer_seconds, 300)
        decision["action_after_defer"] = "run" if ci < threshold else "forced_run"

    t0 = datetime.now(timezone.utc).isoformat()
    measured = track_execution(
        lambda: train_and_eval(mode, csv_path=dataset_csv),
        mean_ci_g_per_kwh=float(ci),
        assumed_kw=float(assumed_kw),
    )

    row = dict(
        run_id=f"{mode}_{int(time.time())}",
        phase=mode,
        task=task,
        dataset=("csv" if dataset_csv else "synthetic"),
        hardware=_detect_hardware(),
        region=region,
        timestamp_utc=t0,
        kWh=f"{measured['energy_kwh']:.8f}",
        kgCO2e=f"{measured['co2e_kg']:.8f}",
        water_L="",
        runtime_s=f"{measured['runtime_s']:.6f}",
        quality_metric_name="MAE",
        quality_metric_value=f"{measured['result']['mae']:.6f}",
        notes=notes or ("CodeCarbon" if measured.get("co2e_kg_measured") else "Proxy"),
    )

    _append_row(out_path, row)

    if log_decision_path:
        os.makedirs(os.path.dirname(log_decision_path), exist_ok=True)
        try:
            if os.path.exists(log_decision_path):
                with open(log_decision_path, "r") as f:
                    log = json.load(f)
            else:
                log = []
        except Exception:
            log = []
        log.append({
            "timestamp": t0,
            "region": region,
            "naive_run": {"carbon_intensity": decision.get("naive_ci"),},
            "green_run": {"carbon_intensity": int(ci), "deferred_seconds": decision.get("deferred_seconds", 0)},
            "savings": {}
        })
        with open(log_decision_path, "w") as f:
            json.dump(log, f, indent=2)

    return row
