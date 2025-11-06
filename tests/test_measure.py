#!/usr/bin/env python3
"""
Unit tests for greenai.measure module.
Tests energy/CO2 proxy calculations and execution tracking.
"""
import pytest
import sys
import time
from unittest.mock import patch, Mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from greenai.measure import energy_co2_proxy, track_execution


class TestEnergyCO2Proxy:
    """Test proxy-based energy and CO2 calculations."""

    def test_basic_calculation(self):
        """Test basic energy and CO2 calculation."""
        runtime_s = 1.0
        ci = 200.0
        kw = 0.1
        
        energy, co2 = energy_co2_proxy(runtime_s, ci, kw)
        
        expected_energy = 0.1 / 3600  # kWh
        expected_co2 = expected_energy * 200 / 1000  # kg
        
        assert abs(energy - expected_energy) < 1e-9
        assert abs(co2 - expected_co2) < 1e-9

    def test_one_hour_runtime(self):
        """Test calculation for exactly one hour."""
        runtime_s = 3600.0
        ci = 100.0
        kw = 0.2
        
        energy, co2 = energy_co2_proxy(runtime_s, ci, kw)
        
        assert abs(energy - 0.2) < 1e-9  # 0.2 kWh
        assert abs(co2 - 0.02) < 1e-9  # 0.02 kg

    def test_high_carbon_intensity(self):
        """Test with high carbon intensity."""
        runtime_s = 60.0
        ci = 500.0
        kw = 0.15
        
        energy, co2 = energy_co2_proxy(runtime_s, ci, kw)
        
        expected_energy = 0.15 * (60 / 3600)
        expected_co2 = expected_energy * 500 / 1000
        
        assert abs(energy - expected_energy) < 1e-9
        assert abs(co2 - expected_co2) < 1e-9

    def test_low_carbon_intensity(self):
        """Test with low carbon intensity (renewable-heavy grid)."""
        runtime_s = 100.0
        ci = 50.0
        kw = 0.1
        
        energy, co2 = energy_co2_proxy(runtime_s, ci, kw)
        
        expected_energy = 0.1 * (100 / 3600)
        expected_co2 = expected_energy * 50 / 1000
        
        assert abs(energy - expected_energy) < 1e-9
        assert abs(co2 - expected_co2) < 1e-9

    def test_zero_runtime(self):
        """Test edge case with zero runtime."""
        energy, co2 = energy_co2_proxy(0.0, 200.0, 0.1)
        
        assert energy == 0.0
        assert co2 == 0.0

    def test_custom_power_consumption(self):
        """Test with custom power consumption (GPU scenario)."""
        runtime_s = 1800.0  # 30 minutes
        ci = 300.0
        kw = 0.5  # 500W GPU
        
        energy, co2 = energy_co2_proxy(runtime_s, ci, kw)
        
        expected_energy = 0.5 * (1800 / 3600)  # 0.25 kWh
        expected_co2 = 0.25 * 300 / 1000  # 0.075 kg
        
        assert abs(energy - expected_energy) < 1e-9
        assert abs(co2 - expected_co2) < 1e-9


class TestTrackExecution:
    """Test execution tracking with energy measurement."""

    def test_basic_tracking(self):
        """Test basic function execution tracking."""
        def dummy_func():
            time.sleep(0.01)
            return {"result": "success"}
        
        result = track_execution(
            dummy_func,
            mean_ci_g_per_kwh=200.0,
            assumed_kw=0.1,
            use_codecarbon=False
        )
        
        assert "result" in result
        assert "runtime_s" in result
        assert "energy_kwh" in result
        assert "co2e_kg" in result
        assert result["runtime_s"] > 0
        assert result["result"]["result"] == "success"

    def test_runtime_measurement(self):
        """Test that runtime is measured accurately."""
        sleep_time = 0.05
        
        def slow_func():
            time.sleep(sleep_time)
            return "done"
        
        result = track_execution(
            slow_func,
            mean_ci_g_per_kwh=200.0,
            assumed_kw=0.1,
            use_codecarbon=False
        )
        
        # Runtime should be approximately sleep_time
        assert result["runtime_s"] >= sleep_time
        assert result["runtime_s"] < sleep_time + 0.1  # some tolerance

    def test_proxy_fallback_when_codecarbon_disabled(self):
        """Test that proxy is used when CodeCarbon is disabled."""
        def quick_func():
            return 42
        
        result = track_execution(
            quick_func,
            mean_ci_g_per_kwh=150.0,
            assumed_kw=0.1,
            use_codecarbon=False
        )
        
        assert result["co2e_kg_measured"] is None
        assert result["co2e_kg"] > 0  # proxy value

    def test_codecarbon_disabled_uses_proxy(self):
        """Test that proxy is used when CodeCarbon is explicitly disabled."""
        def dummy_func():
            return "result"
        
        result = track_execution(
            dummy_func,
            mean_ci_g_per_kwh=200.0,
            assumed_kw=0.1,
            use_codecarbon=False
        )
        
        # When codecarbon is disabled, measured value should be None
        assert result["co2e_kg_measured"] is None
        # But proxy value should still be calculated
        assert result["co2e_kg"] > 0

    def test_function_with_kwargs(self):
        """Test tracking function with keyword arguments."""
        def add_numbers(a, b):
            return a + b
        
        result = track_execution(
            add_numbers,
            mean_ci_g_per_kwh=200.0,
            assumed_kw=0.1,
            use_codecarbon=False,
            a=5,
            b=3
        )
        
        assert result["result"] == 8

    def test_function_exception_propagation(self):
        """Test that exceptions from tracked function are propagated."""
        def failing_func():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            track_execution(
                failing_func,
                mean_ci_g_per_kwh=200.0,
                use_codecarbon=False
            )

    def test_energy_calculation_consistency(self):
        """Test that energy calculation matches proxy formula."""
        def instant_func():
            return "done"
        
        result = track_execution(
            instant_func,
            mean_ci_g_per_kwh=250.0,
            assumed_kw=0.15,
            use_codecarbon=False
        )
        
        # Verify energy and CO2 match proxy calculation
        expected_energy = 0.15 * (result["runtime_s"] / 3600)
        expected_co2 = expected_energy * 250 / 1000
        
        assert abs(result["energy_kwh"] - expected_energy) < 1e-9
        assert abs(result["co2e_kg"] - expected_co2) < 1e-9


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
