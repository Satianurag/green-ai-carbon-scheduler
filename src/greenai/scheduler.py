from __future__ import annotations
from datetime import datetime, timezone
from typing import Tuple, Dict

from .ci_provider import fetch_uk_current_ci


def should_run(threshold_gco2_per_kwh: int = 200) -> Tuple[bool, Dict]:
    """
    Returns (can_run, decision_dict)
    decision_dict includes: timestamp_utc, region, carbon_intensity, threshold
    """
    ci = fetch_uk_current_ci()
    decision = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "region": "GB",
        "carbon_intensity": int(ci),
        "threshold": int(threshold_gco2_per_kwh),
    }
    return (ci < threshold_gco2_per_kwh), decision
