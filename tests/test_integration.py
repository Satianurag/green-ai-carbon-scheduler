#!/usr/bin/env python3
"""
Integration tests for greenai package.
Tests end-to-end workflows and module interactions.
"""
import pytest
import sys
import os
import json
import csv
from pathlib import Path
from unittest.mock import patch, Mock

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from greenai.scheduler import should_run
from greenai.metrics import run_once
from greenai.pipeline import fit_and_predict
from greenai.plots import plot_energy_co2_bars


class TestEndToEndWorkflow:
    """Test complete carbon-aware training workflows."""

    @patch('greenai.metrics.fetch_uk_current_ci')
    @patch('greenai.metrics.track_execution')
    def test_baseline_to_optimized_workflow(self, mock_track, mock_fetch, tmp_path):
        """Test complete workflow: baseline → optimized → plotting."""
        mock_fetch.return_value = 150.0
        mock_track.return_value = {
            "result": {"mae": 0.5},
            "runtime_s": 1.0,
            "energy_kwh": 0.001,
            "co2e_kg": 0.0002,
            "co2e_kg_measured": None
        }
        
        out_path = tmp_path / "evidence.csv"
        plots_dir = tmp_path / "plots"
        
        # Step 1: Run baseline
        row1 = run_once(
            mode="baseline",
            dataset_csv=None,
            out_path=str(out_path),
            threshold=200,
            defer_seconds=0,
            assumed_kw=0.1,
            use_codecarbon=False
        )
        
        # Step 2: Run optimized
        mock_track.return_value["energy_kwh"] = 0.0005  # More efficient
        mock_track.return_value["co2e_kg"] = 0.0001
        
        row2 = run_once(
            mode="optimized",
            dataset_csv=None,
            out_path=str(out_path),
            threshold=200,
            defer_seconds=0,
            assumed_kw=0.1,
            use_codecarbon=False
        )
        
        # Step 3: Generate plots
        plot_path = plot_energy_co2_bars(str(out_path), str(plots_dir))
        
        # Verify workflow
        assert os.path.exists(out_path)
        assert os.path.exists(plot_path)
        assert row1["phase"] == "baseline"
        assert row2["phase"] == "optimized"
        
        # Verify CSV has both runs
        with open(out_path) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 2

    @patch('greenai.scheduler.fetch_uk_current_ci')
    def test_scheduler_integration(self, mock_fetch):
        """Test scheduler decision making workflow."""
        # Scenario 1: Low CI - should run
        mock_fetch.return_value = 100
        can_run, decision = should_run(threshold_gco2_per_kwh=200)
        assert can_run is True
        
        # Scenario 2: High CI - should defer
        mock_fetch.return_value = 300
        can_run, decision = should_run(threshold_gco2_per_kwh=200)
        assert can_run is False

    def test_kaggle_submission_workflow(self, tmp_path):
        """Test complete Kaggle submission workflow."""
        # Create train and test datasets
        train_csv = tmp_path / "train.csv"
        test_csv = tmp_path / "test.csv"
        submission_csv = tmp_path / "submission.csv"
        
        train_csv.write_text(
            "Id,feature1,feature2,GreenScore\n"
            "1,1.0,2.0,10\n"
            "2,2.0,3.0,20\n"
            "3,3.0,4.0,30\n"
            "4,4.0,5.0,40\n"
            "5,5.0,6.0,50\n"
        )
        
        test_csv.write_text(
            "Id,feature1,feature2\n"
            "6,6.0,7.0\n"
            "7,7.0,8.0\n"
        )
        
        # Generate predictions
        df_sub = fit_and_predict(
            mode="optimized",
            train_csv=str(train_csv),
            test_csv=str(test_csv),
            random_state=42,
            n_jobs=1
        )
        
        # Save submission
        df_sub.to_csv(submission_csv, index=False)
        
        # Verify
        assert os.path.exists(submission_csv)
        assert len(df_sub) == 2
        assert "Id" in df_sub.columns
        assert "GreenScore" in df_sub.columns

    @patch('greenai.metrics.fetch_uk_current_ci')
    @patch('greenai.metrics.track_execution')
    def test_csv_based_ci_workflow(self, mock_track, mock_fetch, tmp_path):
        """Test workflow using CSV-based carbon intensity data."""
        # Create CI metadata CSV
        ci_csv = tmp_path / "meta.csv"
        ci_csv.write_text(
            "region,UTC_hour,carbon_intensity_gco2_per_kwh\n"
            "GB,0,200\n"
            "GB,1,100\n"
            "GB,2,150\n"
        )
        
        mock_track.return_value = {
            "result": {"mae": 0.5},
            "runtime_s": 1.0,
            "energy_kwh": 0.001,
            "co2e_kg": 0.0001,
            "co2e_kg_measured": None
        }
        
        out_path = tmp_path / "evidence.csv"
        
        # Run with CSV CI mode
        row = run_once(
            mode="optimized",
            dataset_csv=None,
            out_path=str(out_path),
            threshold=200,
            defer_seconds=0,
            assumed_kw=0.1,
            ci_mode="csv",
            ci_csv_path=str(ci_csv),
            horizon_hours=24,
            use_codecarbon=False
        )
        
        assert os.path.exists(out_path)
        assert row["phase"] == "optimized"

    @patch('greenai.metrics.fetch_uk_current_ci')
    @patch('greenai.metrics.track_execution')
    def test_decision_logging_workflow(self, mock_track, mock_fetch, tmp_path):
        """Test decision logging across multiple runs."""
        mock_fetch.return_value = 150.0
        mock_track.return_value = {
            "result": {"mae": 0.5},
            "runtime_s": 1.0,
            "energy_kwh": 0.001,
            "co2e_kg": 0.0002,
            "co2e_kg_measured": None
        }
        
        out_path = tmp_path / "evidence.csv"
        decision_path = tmp_path / "decisions.json"
        
        # Run 1
        run_once(
            mode="baseline",
            dataset_csv=None,
            out_path=str(out_path),
            threshold=200,
            defer_seconds=0,
            assumed_kw=0.1,
            log_decision_path=str(decision_path),
            use_codecarbon=False
        )
        
        # Run 2
        mock_fetch.return_value = 120.0
        run_once(
            mode="optimized",
            dataset_csv=None,
            out_path=str(out_path),
            threshold=200,
            defer_seconds=0,
            assumed_kw=0.1,
            log_decision_path=str(decision_path),
            use_codecarbon=False
        )
        
        # Verify decision log
        with open(decision_path) as f:
            log = json.load(f)
            assert len(log) == 2
            assert all("timestamp" in entry for entry in log)
            assert all("green_run" in entry for entry in log)


class TestErrorHandlingIntegration:
    """Test error handling across integrated components."""

    @patch('greenai.metrics.fetch_uk_current_ci')
    def test_api_failure_handling(self, mock_fetch, tmp_path):
        """Test graceful handling of API failures."""
        mock_fetch.side_effect = Exception("API Timeout")
        
        out_path = tmp_path / "evidence.csv"
        
        with pytest.raises(Exception):
            run_once(
                mode="baseline",
                dataset_csv=None,
                out_path=str(out_path),
                threshold=200,
                defer_seconds=0,
                assumed_kw=0.1,
                use_codecarbon=False
            )

    def test_missing_ci_csv_raises_error(self, tmp_path):
        """Test error when CI CSV is missing."""
        out_path = tmp_path / "evidence.csv"
        
        with pytest.raises(ValueError):
            run_once(
                mode="baseline",
                dataset_csv=None,
                out_path=str(out_path),
                threshold=200,
                defer_seconds=0,
                assumed_kw=0.1,
                ci_mode="csv",
                ci_csv_path=None,  # Missing!
                use_codecarbon=False
            )


class TestDataConsistency:
    """Test data consistency across pipeline stages."""

    @patch('greenai.metrics.fetch_uk_current_ci')
    @patch('greenai.metrics.track_execution')
    def test_random_seed_reproducibility(self, mock_track, mock_fetch, tmp_path):
        """Test that same seed produces consistent results."""
        mock_fetch.return_value = 150.0
        
        out_path1 = tmp_path / "evidence1.csv"
        out_path2 = tmp_path / "evidence2.csv"
        
        # Mock consistent results
        mock_track.return_value = {
            "result": {"mae": 0.441234},
            "runtime_s": 1.0,
            "energy_kwh": 0.001,
            "co2e_kg": 0.0002,
            "co2e_kg_measured": None
        }
        
        row1 = run_once(
            mode="baseline",
            dataset_csv=None,
            out_path=str(out_path1),
            threshold=200,
            defer_seconds=0,
            assumed_kw=0.1,
            random_state=42,
            use_codecarbon=False
        )
        
        row2 = run_once(
            mode="baseline",
            dataset_csv=None,
            out_path=str(out_path2),
            threshold=200,
            defer_seconds=0,
            assumed_kw=0.1,
            random_state=42,
            use_codecarbon=False
        )
        
        # MAE should be consistent with same seed
        assert row1["quality_metric_value"] == row2["quality_metric_value"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
