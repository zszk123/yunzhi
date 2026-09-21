"""T4 结构化日志：structlog JSON 输出测试。"""

import json

import structlog

from app.core.logging import configure_logging


def _last_log_line(capsys) -> dict:
    out = capsys.readouterr().out.strip()
    assert out, "应有日志输出"
    return json.loads(out.splitlines()[-1])


def test_logs_are_json_with_required_fields(capsys):
    configure_logging("INFO")
    structlog.get_logger().info("server.started", port=8000)

    record = _last_log_line(capsys)
    assert record["event"] == "server.started"
    assert record["level"] == "info"
    assert "time" in record
    assert record["port"] == 8000


def test_log_level_filters_lower_levels(capsys):
    configure_logging("WARNING")
    structlog.get_logger().info("should.not.appear")

    assert capsys.readouterr().out == ""


def test_log_level_allows_configured_level(capsys):
    configure_logging("WARNING")
    structlog.get_logger().warning("disk.almost.full", usage=0.95)

    record = _last_log_line(capsys)
    assert record["event"] == "disk.almost.full"
    assert record["level"] == "warning"
