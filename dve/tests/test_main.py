"""The dsm command with the runtime and the server mocked (SRS DSM-DVE req 6)."""

import signal

import pytest

from dve import __main__ as dsm


@pytest.fixture
def world(monkeypatch):
    state = {"runtime": [], "served": [], "signals": {}}
    monkeypatch.setattr(dsm, "runtime", lambda: state["runtime"].append(True) or "the-runtime")
    monkeypatch.setattr(dsm, "serve", lambda runtime: state["served"].append(runtime))
    monkeypatch.setattr(dsm.signal, "signal", lambda signum, handler: state["signals"].__setitem__(signum, handler))
    return state


def test_serves_the_api_over_the_runtime(world):
    code = dsm.main([])

    assert world["runtime"] == [True]
    assert world["served"] == ["the-runtime"]
    assert code == 0


def test_concurrency_option_is_rejected(world):
    with pytest.raises(SystemExit):
        dsm.main(["-c", "4"])

    assert world["served"] == []


def test_sigterm_ends_the_command_like_ctrl_c(world):
    dsm.main([])

    with pytest.raises(SystemExit):
        world["signals"][signal.SIGTERM](signal.SIGTERM, None)
