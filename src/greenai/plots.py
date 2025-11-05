from __future__ import annotations
import os
import pandas as pd
import matplotlib.pyplot as plt


def plot_energy_co2_bars(evidence_csv: str, out_dir: str):
    os.makedirs(out_dir, exist_ok=True)
    df = pd.read_csv(evidence_csv)
    agg = df.groupby("phase").agg({"kWh": "mean", "kgCO2e": "mean"}).reset_index()
    agg["kWh"] = agg["kWh"].astype(float)
    agg["kgCO2e"] = agg["kgCO2e"].astype(float)

    fig, ax = plt.subplots(1, 2, figsize=(8, 3))
    ax[0].bar(agg["phase"], agg["kWh"], color=["#888", "#2e7"])
    ax[0].set_title("Energy (kWh)")
    ax[1].bar(agg["phase"], agg["kgCO2e"], color=["#888", "#2e7"])
    ax[1].set_title("CO₂e (kg)")
    plt.tight_layout()
    fp = os.path.join(out_dir, "energy_co2_bars.png")
    plt.savefig(fp, dpi=160)
    return fp
