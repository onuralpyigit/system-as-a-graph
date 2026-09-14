"""The dsm command with the Docker SDK and the child processes mocked (SRS DSM-DVE req 6)."""

import sys

import docker.errors
import pytest

from dve import __main__ as dsm
from dve.config import RedisConfig


class FakeChild:
    def __init__(self, argv):
        self.argv = argv
        self.returncode = None
        self.terminated = False

    def poll(self):
        return self.returncode

    def terminate(self):
        self.terminated = True
        self.returncode = -15

    def wait(self, timeout=None):
        return self.returncode

    def kill(self):
        self.returncode = -9


class FakeDocker:
    """A docker client whose `existing` flag decides whether the container is found."""

    def __init__(self, existing=True):
        self.existing = existing
        self.container = _Container()
        self.run_kwargs = None

    def get(self, name):
        if not self.existing:
            raise docker.errors.NotFound(f"no container {name}")
        return self.container

    def run(self, image, **kwargs):
        self.run_kwargs = dict(kwargs, image=image)
        return self.container

    @property
    def containers(self):
        return self


class _Container:
    def __init__(self):
        self.started = False
        self.stopped = False

    def start(self):
        self.started = True

    def stop(self):
        self.stopped = True


@pytest.fixture
def world(monkeypatch):
    """Mocks docker, the children, the readiness socket and the wait loop; `interrupt` ends the loop with Ctrl+C."""
    state = {"docker": FakeDocker(), "children": [], "ticks": []}
    monkeypatch.setattr(dsm.docker, "from_env", lambda: state["docker"])
    monkeypatch.setattr(dsm.subprocess, "Popen", lambda argv: state["children"].append(FakeChild(argv)) or state["children"][-1])
    monkeypatch.setattr(dsm.socket, "create_connection", lambda *a, **k: _Socket())
    monkeypatch.setattr(dsm.time, "sleep", lambda seconds: state["ticks"].append(seconds) or state["on_tick"]())
    state["on_tick"] = lambda: (_ for _ in ()).throw(KeyboardInterrupt())
    return state


class _Socket:
    def close(self):
        pass


def test_starts_an_existing_container_then_both_children_and_stops_everything_on_ctrl_c(world):
    code = dsm.main([])

    assert world["docker"].container.started is True
    assert world["docker"].run_kwargs is None
    assert [child.argv for child in world["children"]] == [
        [sys.executable, "-m", "dve.worker"],
        [sys.executable, "-m", "dve.api"],
    ]
    assert all(child.terminated for child in world["children"])
    assert world["docker"].container.stopped is True
    assert code == 0


def test_concurrency_is_passed_to_the_worker(world):
    dsm.main(["-c", "4"])

    assert world["children"][0].argv == [sys.executable, "-m", "dve.worker", "--concurrency=4"]


def test_a_missing_container_is_created_with_a_port_mapping(world):
    world["docker"].existing = False

    dsm.main([])

    assert world["docker"].run_kwargs == {"image": "redis:8.4", "name": "dsm-redis", "detach": True, "ports": {"6379/tcp": 6379}}
    assert world["docker"].container.started is False


def test_the_configured_port_is_mapped(world):
    world["docker"].existing = False

    dsm.RedisContainer(RedisConfig(port=6380)).start()

    assert world["docker"].run_kwargs["ports"] == {"6379/tcp": 6380}


def test_a_child_exiting_ends_the_run_with_its_code(world):
    def child_exits():
        world["children"][1].returncode = 3
    world["on_tick"] = child_exits

    code = dsm.main([])

    assert code == 3
    assert world["children"][0].terminated is True
    assert world["docker"].container.stopped is True


def test_an_unreachable_docker_daemon_ends_the_command(world, monkeypatch):
    monkeypatch.setattr(dsm.docker, "from_env", lambda: (_ for _ in ()).throw(docker.errors.DockerException("no daemon")))

    with pytest.raises(SystemExit, match="cannot start redis: no daemon"):
        dsm.main([])

    assert world["children"] == []
