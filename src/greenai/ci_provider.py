from __future__ import annotations
import requests
import pandas as pd
from datetime import datetime, timezone


def fetch_uk_current_ci(region: str = "GB", timeout: int = 8) -> int:
    """
    Fetch current grid carbon intensity (gCO2/kWh) from UK National Grid API.
    Falls back to forecast if 'actual' is None.
    """
    url = "https://api.carbonintensity.org.uk/intensity"
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    data = r.json()
    intensity = data["data"][0]["intensity"]
    value = intensity.get("actual") or intensity.get("forecast")
    return int(value)


essential_meta_columns = ["region", "UTC_hour", "carbon_intensity_gco2_per_kwh"]


def read_meta_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    return df


def pick_low_ci_window(meta: pd.DataFrame, region: str | None = None) -> dict:
    dfm = meta if (region is None or "region" not in meta.columns) else meta[meta["region"].eq(region)]
    row = dfm.sort_values("carbon_intensity_gco2_per_kwh").head(1)
    return dict(
        region=str(row["region"].iloc[0]) if "region" in row.columns else (region or "UNKNOWN"),
        utc_hour=int(row["UTC_hour"].iloc[0]) if "UTC_hour" in row.columns else None,
        carbon_intensity_gco2_per_kwh=float(row["carbon_intensity_gco2_per_kwh"].iloc[0]),
    )


def pick_low_ci_within_horizon(meta: pd.DataFrame, horizon_hours: int, region: str | None = None) -> dict:
    """
    Pick the lowest CI row within the next `horizon_hours` based on `UTC_hour` if present.
    Falls back to global minimum if no temporal information is available.
    """
    dfm = meta if (region is None or "region" not in meta.columns) else meta[meta["region"].eq(region)]
    if len(dfm) == 0:
        # Fallback to all rows if region filter yields none
        dfm = meta
    if horizon_hours and "UTC_hour" in dfm.columns:
        now_h = datetime.now(timezone.utc).hour
        # Accept hours in [now_h, now_h + horizon] modulo 24
        try:
            cand = dfm[dfm["UTC_hour"].apply(lambda h: ((int(h) - now_h) % 24) <= horizon_hours)]
        except Exception:
            cand = dfm
        if len(cand) > 0:
            dfm = cand
    if len(dfm) == 0:
        # Ultimate fallback: return the overall min from meta
        dfm = meta
    row = dfm.sort_values("carbon_intensity_gco2_per_kwh").head(1)
    return dict(
        region=(str(row["region"].iloc[0]) if ("region" in row.columns and len(row) > 0) else (region or "UNKNOWN")),
        utc_hour=(int(row["UTC_hour"].iloc[0]) if ("UTC_hour" in row.columns and len(row) > 0) else None),
        carbon_intensity_gco2_per_kwh=(float(row["carbon_intensity_gco2_per_kwh"].iloc[0]) if len(row) > 0 else float(meta["carbon_intensity_gco2_per_kwh"].median())),
    )
