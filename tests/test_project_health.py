from pathlib import Path

from utils.project_health import build_health_report


def test_build_health_report_returns_perfect_score():
    project_root = Path(__file__).resolve().parents[1]
    report = build_health_report(project_root)

    assert report["score"] == 100
    assert report["status"] == "healthy"
    assert all(item["passed"] for item in report["checks"])
