import time
__all__ = [
    "cli",
    "measure",
    "ci_provider",
    "scheduler",
    "pipeline",
    "metrics",
    "plots",
    "carbon_aware_train",
]

def carbon_aware_train(model, X, y, threshold_gco2_per_kwh=200, max_wait_seconds=0, assumed_kw=0.1, use_codecarbon=True):
    from .ci_provider import fetch_uk_current_ci
    from .measure import track_execution
    ci = float(fetch_uk_current_ci())
    if ci >= float(threshold_gco2_per_kwh) and int(max_wait_seconds) > 0:
        start = time.time()
        cap = int(max_wait_seconds)
        while (time.time() - start) < cap:
            time.sleep(min(60, cap - int(time.time() - start)))
            ci_new = float(fetch_uk_current_ci())
            if ci_new < ci:
                ci = ci_new
            if ci_new < float(threshold_gco2_per_kwh):
                ci = ci_new
                break
    res = track_execution(
        lambda: model.fit(X, y),
        mean_ci_g_per_kwh=ci,
        assumed_kw=float(assumed_kw),
        use_codecarbon=bool(use_codecarbon),
    )
    return model, {
        "runtime_s": res["runtime_s"],
        "energy_kwh": res["energy_kwh"],
        "co2e_kg": res["co2e_kg"],
        "co2e_kg_measured": res.get("co2e_kg_measured"),
    }
