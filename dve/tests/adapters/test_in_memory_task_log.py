"""The in-memory task log (SRS DSM-DVE req 8)."""

from fakes import seed
from dve.adapters.in_memory_task_log import InMemoryTaskLog


def test_lines_since_returns_the_tail_and_empty_for_unknown_tasks():
    log = InMemoryTaskLog()
    log.append(seed.RUN_1, "one")
    log.append(seed.RUN_1, "two")
    log.append(seed.RUN_1, "three")

    assert log.lines_since(seed.RUN_1, 0) == ["one", "two", "three"]
    assert log.lines_since(seed.RUN_1, 2) == ["three"]
    assert log.lines_since(seed.RUN_1, -5) == ["one", "two", "three"]
    assert log.lines_since(seed.RUN_1, 3) == []
    assert log.lines_since(seed.RUN_2, 0) == []


def test_a_longer_run_stops_collecting_and_says_so_once():
    log = InMemoryTaskLog(max_lines=3)
    for index in range(6):
        log.append(seed.RUN_1, f"line {index}")

    assert log.lines_since(seed.RUN_1, 0) == ["line 0", "line 1", "line 2", "... log truncated at 3 lines"]
    assert log.lines_since(seed.RUN_1, 3) == ["... log truncated at 3 lines"]
