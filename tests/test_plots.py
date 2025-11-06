#!/usr/bin/env python3
"""
Unit tests for greenai.plots module.
Tests visualization generation and file I/O.
"""
import pytest
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from greenai.plots import plot_energy_co2_bars


class TestPlotEnergyCO2Bars:
    """Test energy and CO2 bar chart generation."""

    def test_plot_creation(self, tmp_path):
        """Test that plot is created successfully."""
        evidence_csv = tmp_path / "evidence.csv"
        evidence_csv.write_text(
            "phase,kWh,kgCO2e\n"
            "baseline,0.001,0.0002\n"
            "optimized,0.0005,0.0001\n"
        )
        
        out_dir = tmp_path / "plots"
        
        result_path = plot_energy_co2_bars(str(evidence_csv), str(out_dir))
        
        assert os.path.exists(result_path)
        assert result_path.endswith("energy_co2_bars.png")

    def test_plot_output_directory_created(self, tmp_path):
        """Test that output directory is created if missing."""
        evidence_csv = tmp_path / "evidence.csv"
        evidence_csv.write_text(
            "phase,kWh,kgCO2e\n"
            "baseline,0.001,0.0002\n"
            "optimized,0.0005,0.0001\n"
        )
        
        out_dir = tmp_path / "nonexistent" / "plots"
        
        result_path = plot_energy_co2_bars(str(evidence_csv), str(out_dir))
        
        assert os.path.exists(out_dir)
        assert os.path.exists(result_path)

    def test_plot_with_multiple_runs(self, tmp_path):
        """Test plotting with multiple runs per phase."""
        evidence_csv = tmp_path / "evidence.csv"
        evidence_csv.write_text(
            "phase,kWh,kgCO2e\n"
            "baseline,0.001,0.0002\n"
            "baseline,0.0012,0.00022\n"
            "optimized,0.0005,0.0001\n"
            "optimized,0.0006,0.00012\n"
        )
        
        out_dir = tmp_path / "plots"
        
        result_path = plot_energy_co2_bars(str(evidence_csv), str(out_dir))
        
        assert os.path.exists(result_path)

    def test_missing_csv_raises_error(self, tmp_path):
        """Test error handling for missing evidence CSV."""
        out_dir = tmp_path / "plots"
        
        with pytest.raises(FileNotFoundError):
            plot_energy_co2_bars("/nonexistent/evidence.csv", str(out_dir))

    def test_malformed_csv_data(self, tmp_path):
        """Test handling of malformed CSV data."""
        evidence_csv = tmp_path / "evidence.csv"
        evidence_csv.write_text(
            "wrong,columns,here\n"
            "baseline,0.001,0.0002\n"
        )
        
        out_dir = tmp_path / "plots"
        
        # Should raise KeyError due to missing expected columns
        with pytest.raises(KeyError):
            plot_energy_co2_bars(str(evidence_csv), str(out_dir))

    def test_plot_returns_correct_path(self, tmp_path):
        """Test that function returns correct output path."""
        evidence_csv = tmp_path / "evidence.csv"
        evidence_csv.write_text(
            "phase,kWh,kgCO2e\n"
            "baseline,0.001,0.0002\n"
            "optimized,0.0005,0.0001\n"
        )
        
        out_dir = tmp_path / "plots"
        
        result_path = plot_energy_co2_bars(str(evidence_csv), str(out_dir))
        expected_path = os.path.join(str(out_dir), "energy_co2_bars.png")
        
        assert result_path == expected_path

    def test_plot_with_string_numeric_values(self, tmp_path):
        """Test that plot handles string numeric values correctly."""
        evidence_csv = tmp_path / "evidence.csv"
        evidence_csv.write_text(
            "phase,kWh,kgCO2e\n"
            "baseline,0.00100000,0.00020000\n"
            "optimized,0.00050000,0.00010000\n"
        )
        
        out_dir = tmp_path / "plots"
        
        # Should handle conversion to float
        result_path = plot_energy_co2_bars(str(evidence_csv), str(out_dir))
        assert os.path.exists(result_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
