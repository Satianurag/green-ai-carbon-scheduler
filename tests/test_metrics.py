#!/usr/bin/env python3
"""
Unit tests for greenai.metrics module.
Tests evidence collection, CSV writing, and decision logging.
"""
import pytest
import sys
import os
import json
import csv
from pathlib import Path
from unittest.mock import patch, Mock

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from greenai.metrics import run_once, EVIDENCE_HEADER


class TestRunOnce:
    """Test single run execution with metrics collection."""

    @patch('greenai.metrics.fetch_uk_current_ci')
    @patch('greenai.metrics.track_execution')
    def test_baseline_run_creates_evidence(self, mock_track, mock_fetch, tmp_path):
        """Test that baseline run creates evidence CSV."""
        mock_fetch.return_value = 150.0
        mock_track.return_value = {
            "result": {"mae": 0.5},
            "runtime_s": 1.0,
            "energy_kwh": 0.0001,
            "co2e_kg": 0.00002,
            "co2e_kg_measured": None
        }
        
        out_path = tmp_path / "evidence.csv"
        
        row = run_once(
            mode="baseline",
            dataset_csv=None,
            out_path=str(out_path),
            threshold=200,
            defer_seconds=0,
            assumed_kw=0.1,
            ci_mode="live",
            use_codecarbon=False
        )
        
        assert os.path.exists(out_path)
        assert row["phase"] == "baseline"
        assert float(row["kWh"]) == 0.0001

    @patch('greenai.metrics.fetch_uk_current_ci')
    @patch('greenai.metrics.track_execution')
    def test_optimized_run_with_csv_ci(self, mock_track, mock_fetch, tmp_path):
        """Test optimized run with CSV-based carbon intensity."""
        csv_path = tmp_path / "meta.csv"
        csv_path.write_text(
            "region,UTC_hour,carbon_intensity_gco2_per_kwh\n"
            "GB,0,100\n"
            "GB,1,150\n"
        )
        
        mock_track.return_value = {
            "result": {"mae": 0.6},
            "runtime_s": 0.5,
            "energy_kwh": 0.00005,
            "co2e_kg": 0.000005,
            "co2e_kg_measured": None
        }
        
        out_path = tmp_path / "evidence.csv"
        
        row = run_once(
            mode="optimized",
            dataset_csv=None,
            out_path=str(out_path),
            threshold=200,
            defer_seconds=0,
            assumed_kw=0.1,
            ci_mode="csv",
            ci_csv_path=str(csv_path),
            horizon_hours=24,
            use_codecarbon=False
        )
        
        assert row["phase"] == "optimized"
        assert os.path.exists(out_path)

    @patch('greenai.metrics.fetch_uk_current_ci')
    @patch('greenai.metrics.track_execution')
    def test_evidence_csv_structure(self, mock_track, mock_fetch, tmp_path):
        """Test that evidence CSV has correct headers."""
        mock_fetch.return_value = 150.0
        mock_track.return_value = {
            "result": {"mae": 0.5},
            "runtime_s": 1.0,
            "energy_kwh": 0.0001,
            "co2e_kg": 0.00002,
            "co2e_kg_measured": None
        }
        
        out_path = tmp_path / "evidence.csv"
        
        run_once(
            mode="baseline",
            dataset_csv=None,
            out_path=str(out_path),
            threshold=200,
            defer_seconds=0,
            assumed_kw=0.1,
            use_codecarbon=False
        )
        
        with open(out_path) as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            for expected_header in EVIDENCE_HEADER:
                assert expected_header in headers

    @patch('greenai.metrics.fetch_uk_current_ci')
    @patch('greenai.metrics.track_execution')
    def test_decision_logging(self, mock_track, mock_fetch, tmp_path):
        """Test that decisions are logged to JSON file."""
        mock_fetch.return_value = 150.0
        mock_track.return_value = {
            "result": {"mae": 0.5},
            "runtime_s": 1.0,
            "energy_kwh": 0.0001,
            "co2e_kg": 0.00002,
            "co2e_kg_measured": None
        }
        
        out_path = tmp_path / "evidence.csv"
        decision_path = tmp_path / "decisions.json"
        
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
        
        assert os.path.exists(decision_path)
        
        with open(decision_path) as f:
            log = json.load(f)
            assert isinstance(log, list)
            assert len(log) > 0
            assert "timestamp" in log[0]
            assert "green_run" in log[0]

    @patch('greenai.metrics.fetch_uk_current_ci')
    @patch('greenai.metrics.track_execution')
    def test_multiple_runs_append(self, mock_track, mock_fetch, tmp_path):
        """Test that multiple runs append to the same CSV."""
        mock_fetch.return_value = 150.0
        mock_track.return_value = {
            "result": {"mae": 0.5},
            "runtime_s": 1.0,
            "energy_kwh": 0.0001,
            "co2e_kg": 0.00002,
            "co2e_kg_measured": None
        }
        
        out_path = tmp_path / "evidence.csv"
        
        # First run
        run_once(
            mode="baseline",
            dataset_csv=None,
            out_path=str(out_path),
            threshold=200,
            defer_seconds=0,
            assumed_kw=0.1,
            use_codecarbon=False
        )
        
        # Second run
        run_once(
            mode="optimized",
            dataset_csv=None,
            out_path=str(out_path),
            threshold=200,
            defer_seconds=0,
            assumed_kw=0.1,
            use_codecarbon=False
        )
        
        with open(out_path) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 2
            assert rows[0]["phase"] == "baseline"
            assert rows[1]["phase"] == "optimized"

    @patch('greenai.metrics.fetch_uk_current_ci')
    @patch('greenai.metrics.track_execution')
    def test_custom_dataset(self, mock_track, mock_fetch, tmp_path):
        """Test run with custom dataset CSV."""
        dataset_csv = tmp_path / "data.csv"
        dataset_csv.write_text(
            "feature1,feature2,GreenScore\n"
            "1.0,2.0,10\n"
            "2.0,3.0,20\n"
        )
        
        mock_fetch.return_value = 150.0
        mock_track.return_value = {
            "result": {"mae": 0.5},
            "runtime_s": 1.0,
            "energy_kwh": 0.0001,
            "co2e_kg": 0.00002,
            "co2e_kg_measured": None
        }
        
        out_path = tmp_path / "evidence.csv"
        
        row = run_once(
            mode="baseline",
            dataset_csv=str(dataset_csv),
            out_path=str(out_path),
            threshold=200,
            defer_seconds=0,
            assumed_kw=0.1,
            use_codecarbon=False
        )
        
        assert row["dataset"] == "csv"

    @patch('greenai.metrics.fetch_uk_current_ci')
    @patch('greenai.metrics.track_execution')
    def test_threshold_enforcement(self, mock_track, mock_fetch, tmp_path):
        """Test that threshold parameter is respected."""
        mock_fetch.return_value = 250.0  # High CI
        mock_track.return_value = {
            "result": {"mae": 0.5},
            "runtime_s": 1.0,
            "energy_kwh": 0.0001,
            "co2e_kg": 0.00002,
            "co2e_kg_measured": None
        }
        
        out_path = tmp_path / "evidence.csv"
        
        # Run even though CI is above threshold (forced run)
        row = run_once(
            mode="baseline",
            dataset_csv=None,
            out_path=str(out_path),
            threshold=200,
            defer_seconds=0,
            assumed_kw=0.1,
            max_wait_seconds=0,
            use_codecarbon=False
        )
        
        # Should still complete the run
        assert row is not None

    @patch('greenai.metrics.fetch_uk_current_ci')
    @patch('greenai.metrics.track_execution')
    def test_notes_field(self, mock_track, mock_fetch, tmp_path):
        """Test that notes are included in evidence."""
        mock_fetch.return_value = 150.0
        mock_track.return_value = {
            "result": {"mae": 0.5},
            "runtime_s": 1.0,
            "energy_kwh": 0.0001,
            "co2e_kg": 0.00002,
            "co2e_kg_measured": 0.00002
        }
        
        out_path = tmp_path / "evidence.csv"
        
        row = run_once(
            mode="baseline",
            dataset_csv=None,
            out_path=str(out_path),
            threshold=200,
            defer_seconds=0,
            assumed_kw=0.1,
            notes="Test run",
            use_codecarbon=True
        )
        
        assert "CodeCarbon" in row["notes"] or "Test run" in row["notes"]

    def test_invalid_mode_raises_error(self, tmp_path):
        """Test that invalid mode raises assertion error."""
        out_path = tmp_path / "evidence.csv"
        
        with pytest.raises(AssertionError):
            run_once(
                mode="invalid",
                dataset_csv=None,
                out_path=str(out_path),
                threshold=200,
                defer_seconds=0,
                assumed_kw=0.1,
                use_codecarbon=False
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
