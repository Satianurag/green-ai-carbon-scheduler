# FOOTPRINT: Measurement Methodology

## Tools
- CodeCarbon v3.0.8 for hardware-level emissions (kg CO₂e). Falls back to proxy if sensors unavailable.
- Proxy formula for energy when needed: Energy (kWh) = Power (kW) × Time (h), default power 0.1 kW (100W CPU).
- Grid carbon intensity: UK National Grid API (https://api.carbonintensity.org.uk/intensity).

## Procedure
- Deterministic training (random_state=42), identical preprocessing across modes.
- For each run, record: runtime_s, energy_kWh (proxy), kgCO2e (CodeCarbon if available), CI (gCO2/kWh), MAE.
- evidence.csv contains baseline and optimized rows with UTC timestamps and hardware string.

## SCI (Software Carbon Intensity)
- SCI per functional unit (prediction) is derived by dividing per-run CO₂e by number of predictions.
- Report both per-run totals and per-unit SCI when applicable.

## Reproducibility
- Python 3.11, pinned requirements in requirements.txt
- One-command run: `bash run.sh`
- Lock your environment after running: `pip freeze > artifacts/requirements.lock.txt`

## Limitations
- UK-only live CI by default. Extend to ElectricityMaps/WattTime for multi-region.
- If CodeCarbon can't access power sensors, CO₂e from CodeCarbon may use regional averages.
