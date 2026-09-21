"""结构化日志：structlog JSON 输出。

输出形如：
{"event": "server.started", "level": "info", "time": "2026-09-21T15:00:00", "port": 8000}

每条日志都是合法 JSON 且必含 time / level / event 三字段，
后续排查"这次问答为什么答得烂"就靠它们（迭代 6 TracePanel 的地基）。
"""

import logging

import structlog


def configure_logging(level: str = "INFO") -> None:
    level_num = getattr(logging, level.upper(), logging.INFO)

    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", key="time"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level_num),
        logger_factory=structlog.PrintLoggerFactory(),
        # 测试会多次重配不同 level，不能缓存
        cache_logger_on_first_use=False,
    )
