"""Redis adapter of the production log port: one list per run, kept until
Redis is cleared (SRS DSM-DVE req 6, 8)."""

from __future__ import annotations

from typing import List

import redis

from dve.ports.production_log import IProductionLog


class RedisProductionLog(IProductionLog):
    """Appends with RPUSH and reads with LRANGE on <key_prefix><run_id>."""

    def __init__(self, url: str, key_prefix: str = "dsm:production-log:"):
        self._client = redis.Redis.from_url(url, decode_responses=True)
        self._key_prefix = key_prefix

    def append(self, run_id: str, line: str) -> None:
        self._client.rpush(self._key_prefix + run_id, line)

    def lines_since(self, run_id: str, index: int) -> List[str]:
        return self._client.lrange(self._key_prefix + run_id, max(index, 0), -1)
