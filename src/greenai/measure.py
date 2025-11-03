import time
from typing import Callable, Any, Dict


def energy_co2_proxy(runtime_s: float, mean_ci_g_per_kwh: float, assumed_kw: float = 0.1):
    """
    Conservative CPU baseline: 100W (0.1 kW)
    Energy (kWh) = Power (kW) × Time (hours)
    CO₂e (kg) = Energy (kWh) × Carbon Intensity (gCO₂/kWh) / 1000
    """
    energy_kwh = assumed_kw * (runtime_s / 3600.0)
    co2e_kg = energy_kwh * (mean_ci_g_per_kwh / 1000.0)
    return energy_kwh, co2e_kg


def track_execution(
    func: Callable[..., Any],
    *,
    mean_ci_g_per_kwh: float,
    assumed_kw: float = 0.1,
    use_codecarbon: bool = True,
    **kwargs,
) -> Dict[str, Any]:
    """
    Runs func(**kwargs) while measuring runtime and emissions.
    If CodeCarbon is available, uses it to estimate kg CO₂e; otherwise falls back to proxy.
    Returns: {"result": Any, "runtime_s": float, "energy_kwh": float, "co2e_kg": float, "co2e_kg_measured": Optional[float]}
    """
    tracker = None
    emissions_kg = None

    if use_codecarbon:
        try:
            from codecarbon import EmissionsTracker  # type: ignore

            tracker = EmissionsTracker(
                project_name="green-ai-carbon-scheduler",
                log_level="error",
            )
            tracker.start()
        except Exception:
            tracker = None

    t0 = time.time()
    result = func(**kwargs)
    runtime_s = time.time() - t0

    if tracker is not None:
        try:
            emissions_kg = tracker.stop()
        except Exception:
            emissions_kg = None

    energy_kwh, co2e_kg_proxy = energy_co2_proxy(runtime_s, mean_ci_g_per_kwh, assumed_kw)
    co2e_kg = emissions_kg if emissions_kg is not None else co2e_kg_proxy

    return {
        "result": result,
        "runtime_s": runtime_s,
        "energy_kwh": energy_kwh,
        "co2e_kg": co2e_kg,
        "co2e_kg_measured": emissions_kg,
    }
