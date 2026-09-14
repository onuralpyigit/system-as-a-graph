"""The dsm command: starts the Redis container, the worker and the API
together, and stops all three on Ctrl+C or when one of them exits
(SRS DSM-DVE req 6).

Run with: dsm [-c N]  (or: python -m dve)
"""

from __future__ import annotations

import argparse
import socket
import subprocess
import sys
import time
from typing import List, Optional

import docker
import docker.errors

from dve.config import RedisConfig, config

READY_TIMEOUT_SECONDS = 30
STOP_TIMEOUT_SECONDS = 5


class RedisContainer:
    """The Redis container behind the worker's broker and result backend;
    started if it exists, created with a port mapping otherwise, never removed."""

    def __init__(self, settings: RedisConfig):
        self._settings = settings
        self._container = None

    def start(self) -> None:
        """Starts or creates the container and waits until its port answers."""
        client = docker.from_env()
        settings = self._settings
        try:
            self._container = client.containers.get(settings.container)
            self._container.start()
        except docker.errors.NotFound:
            self._container = client.containers.run(
                settings.image, name=settings.container, detach=True, ports={"6379/tcp": settings.port},
            )
        self._wait_until_ready()

    def stop(self) -> None:
        if self._container is not None:
            self._container.stop()

    def _wait_until_ready(self) -> None:
        deadline = time.monotonic() + READY_TIMEOUT_SECONDS
        while True:
            try:
                socket.create_connection(("localhost", self._settings.port), timeout=1).close()
                return
            except OSError:
                if time.monotonic() >= deadline:
                    raise RuntimeError(f"redis did not answer on port {self._settings.port} within {READY_TIMEOUT_SECONDS}s")
                time.sleep(0.5)


def _stop(children: List[subprocess.Popen]) -> None:
    """Terminates the children still running, killing any that ignore the request."""
    for child in children:
        if child.poll() is None:
            child.terminate()
    for child in children:
        try:
            child.wait(STOP_TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait()


def main(argv: Optional[List[str]] = None) -> int:
    """Starts Redis, the worker and the API; returns the exit code of the child that ended the run, 0 on Ctrl+C."""
    parser = argparse.ArgumentParser(prog="dsm", description="Start the DSM Redis container, worker and API.")
    parser.add_argument("-c", "--concurrency", type=int, default=None, metavar="N", help="worker process count (default: CPU count)")
    args = parser.parse_args(argv)

    redis = RedisContainer(config().redis)
    try:
        redis.start()
    except (docker.errors.DockerException, RuntimeError) as exc:
        sys.exit(f"dsm: cannot start redis: {exc}")

    worker_argv = [sys.executable, "-m", "dve.worker"]
    if args.concurrency:
        worker_argv.append(f"--concurrency={args.concurrency}")
    children: List[subprocess.Popen] = []
    code = 0
    try:
        children.append(subprocess.Popen(worker_argv))
        children.append(subprocess.Popen([sys.executable, "-m", "dve.api"]))
        while all(child.poll() is None for child in children):
            time.sleep(0.5)
        code = max(child.returncode or 0 for child in children)
    except KeyboardInterrupt:
        pass
    finally:
        _stop(children)
        redis.stop()
    return code


if __name__ == "__main__":
    sys.exit(main())
