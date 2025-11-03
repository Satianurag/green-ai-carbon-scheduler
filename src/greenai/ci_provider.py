from __future__ import annotations
import requests
import pandas as pd


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
