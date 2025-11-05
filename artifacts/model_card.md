# Model Card (Optional)

## Overview
- Baseline: GradientBoostingRegressor(n_estimators=100)
- Optimized: GradientBoostingRegressor(n_estimators=80, subsample=0.7, lr=0.08)

## Intended Use
- Demonstrate carbon-aware scheduling + measurement; not a domain SOTA model.

## Metrics
- Quality: MAE on validation split
- Footprint: runtime_s, kWh, kgCO2e

## Risks & Limitations
- Simple models; not tuned for domain accuracy.
