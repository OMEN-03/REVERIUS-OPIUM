from pathlib import Path

from utils.project_health import (
    build_health_report,
    run_benchmark,
    run_doctor,
    run_repair,
    run_troubleshoot,
)


def test_doctor_creates_machine_readable_and_markdown_reports(tmp_path):
    report = run_doctor(tmp_path)

    assert (tmp_path / "doctor_report.json").exists()
    assert (tmp_path / "doctor_report.md").exists()
    assert report["status"] in {"healthy", "degraded"}


def test_doctor_report_contains_expected_sections():
    project_root = Path(__file__).resolve().parents[1]
    report = run_doctor(project_root)

    assert report["status"] in {"healthy", "degraded"}
    assert "checks" in report
    assert "recommendations" in report
    assert "health_score" in report


def test_repair_produces_repair_report():
    project_root = Path(__file__).resolve().parents[1]
    report = run_repair(project_root)

    assert report["status"] in {"success", "no_action"}
    assert "repair_summary" in report


def test_troubleshoot_generates_findings():
    project_root = Path(__file__).resolve().parents[1]
    report = run_troubleshoot(project_root)

    assert report["status"] in {"resolved", "investigate"}
    assert "findings" in report


def test_benchmark_returns_metrics():
    project_root = Path(__file__).resolve().parents[1]
    report = run_benchmark(project_root)

    assert "metrics" in report
    assert "overall_score" in report


def test_health_report_includes_diagnostics_summary():
    project_root = Path(__file__).resolve().parents[1]
    report = build_health_report(project_root)

    assert "diagnostics" in report
    assert "grade" in report
