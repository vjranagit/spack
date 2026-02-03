"""Tests for health diagnostics."""

import pytest
from pathlib import Path

from spack_ext.health import HealthChecker, HealthReport, HealthStatus


def test_health_checker_init():
    """Test health checker initialization."""
    checker = HealthChecker()
    assert checker.spack_root is not None


def test_run_all_checks():
    """Test running all health checks."""
    checker = HealthChecker()
    report = checker.run_all_checks()
    
    assert isinstance(report, HealthReport)
    assert len(report.checks) > 0
    assert report.total_pass + report.total_warn + report.total_fail + report.total_skip > 0


def test_check_python_version():
    """Test Python version check."""
    checker = HealthChecker()
    check = checker.check_python_version()
    
    assert check.name == "Python Version"
    assert check.status in [HealthStatus.PASS, HealthStatus.WARN, HealthStatus.FAIL]
    assert "Python" in check.message


def test_check_compilers():
    """Test compiler check."""
    checker = HealthChecker()
    check = checker.check_compilers()
    
    assert check.name == "Compilers"
    assert check.status in [HealthStatus.PASS, HealthStatus.FAIL]


def test_check_disk_space():
    """Test disk space check."""
    checker = HealthChecker()
    check = checker.check_disk_space()
    
    assert check.name == "Disk Space"
    assert check.status in [HealthStatus.PASS, HealthStatus.WARN, HealthStatus.FAIL]
    
    if check.details:
        assert "free_gb" in check.details


def test_check_git_available():
    """Test git availability check."""
    checker = HealthChecker()
    check = checker.check_git_available()
    
    assert check.name == "Git"
    assert check.status in [HealthStatus.PASS, HealthStatus.WARN]


def test_check_build_tools():
    """Test build tools check."""
    checker = HealthChecker()
    check = checker.check_build_tools()
    
    assert check.name == "Build Tools"
    assert check.status in [HealthStatus.PASS, HealthStatus.WARN, HealthStatus.FAIL]
    
    if check.details:
        assert "tools" in check.details


def test_check_module_system():
    """Test module system check."""
    checker = HealthChecker()
    check = checker.check_module_system()
    
    assert check.name == "Module System"
    assert check.status in [HealthStatus.PASS, HealthStatus.SKIP]


def test_check_config_files():
    """Test config files check."""
    checker = HealthChecker()
    check = checker.check_config_files()
    
    assert check.name == "Config Files"
    assert check.status in [HealthStatus.PASS, HealthStatus.WARN]


def test_health_report_counters():
    """Test health report counter updates."""
    report = HealthReport()
    
    from spack_ext.health.models import HealthCheck
    
    report.add_check(HealthCheck(name="Test1", status=HealthStatus.PASS, message="OK"))
    assert report.total_pass == 1
    assert report.overall_status == HealthStatus.PASS
    
    report.add_check(HealthCheck(name="Test2", status=HealthStatus.WARN, message="Warning"))
    assert report.total_warn == 1
    assert report.overall_status == HealthStatus.WARN
    
    report.add_check(HealthCheck(name="Test3", status=HealthStatus.FAIL, message="Failed"))
    assert report.total_fail == 1
    assert report.overall_status == HealthStatus.FAIL
