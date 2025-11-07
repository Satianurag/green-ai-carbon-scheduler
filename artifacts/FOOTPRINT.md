# 📊 Measurement Methodology

## How We Measured Impact

**Goal:** Prove carbon reduction with real hardware measurements, not estimates.

### Measurement Stack
- **CodeCarbon v3.0.8** — Hardware-level power consumption sensors
- **UK National Grid API** — Real-time carbon intensity (gCO₂/kWh)
- **Deterministic setup** — `random_state=42` for identical task across runs
- **Complete logging** — Every run timestamped with hardware metadata

### What We Track (Per Run)
```
evidence.csv columns:
├── runtime_s           # How long training took
├── kWh                 # Energy consumed (hardware sensors)
├── kgCO2e              # Carbon emitted (kWh × grid CI)
├── quality_metric      # Model accuracy (MAE)
└── hardware + region   # Reproducibility metadata
```

### SCI Compliance (Software Carbon Intensity)

Following [Green Software Foundation SCI Standard](https://sci.greensoftware.foundation/):

```
SCI = (Energy × Carbon Intensity) / Functional Unit

Where:
  Energy = kWh (hardware measured)
  Carbon Intensity = gCO₂/kWh (live API)
  Functional Unit = 1 ML training run
```

## Reproducibility

**Run it yourself:**
```bash
git clone https://github.com/Satianurag/green-ai-carbon-scheduler.git
cd green-ai-carbon-scheduler
bash run.sh  # One command, full replication
```

**Environment:**
- Python 3.11+
- Dependencies pinned in `requirements.txt`
- Lock file: `artifacts/requirements.lock.txt`

## Measurement Variance & Limitations

**Observed CO₂ Reduction Range**: 14% to 90% across multiple runs

**Root Cause**: Ultra-short runtimes (0.05-0.6s) approach the noise floor of power measurement sensors. CodeCarbon is optimized for longer training jobs (minutes to hours), not micro-benchmarks.

**Implications**:
- Individual measurements show high variance due to sensor precision limits
- Best measured run: 89-90% CO₂ reduction (Nov 7, 2025)
- Average across runs: ~24% CO₂ reduction (CodeCarbon)
- **Production use case** (longer training jobs) would show more stable measurements

**Methodology Strengths** (independent of micro-task variance):
- Carbon-aware scheduling architecture is production-ready
- SCI-compliant measurement discipline
- Documented decision logs and audit trails
- Scalable to GPU workloads and longer training runs

## System Limitations
- UK-only live CI by default. Extend to ElectricityMaps/WattTime for multi-region.
- If CodeCarbon can't access power sensors, CO₂e from CodeCarbon may use regional averages.
- Measurement precision degrades for tasks under 1 second runtime.
