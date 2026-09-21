"""T5 补充：应用启动事件日志测试——启动时应输出一条 JSON 结构化日志。"""

import json

from app.main import create_app


def test_create_app_logs_startup_event_as_json(capsys):
    create_app()

    out = capsys.readouterr().out.strip()
    assert out, "启动时应输出 server.started 日志"
    record = json.loads(out.splitlines()[-1])
    assert record["event"] == "server.started"
    assert record["level"] == "info"
    assert "time" in record
