"""The Model Setup Data file payload and the listing record read back from it
(SRS DSM-MDG req 14, 18, 19; DSM-DVE req 5)."""

from datetime import datetime
from pathlib import Path

import pytest

from fakes import seed
from mdg.domain.acquired_file import AcquiredFile
from mdg.domain.error_record import ErrorRecord, ErrorStatus
from mdg.domain.inventory import SoftwareUnitVersionInventory
from mdg.domain.model_setup_data import (
    InvalidModelSetupData,
    ModelSetupData,
    ModelSetupDataRecord,
    check_payload,
)


def test_to_dict_carries_context_inventory_files_errors_and_graph():
    inventory = SoftwareUnitVersionInventory(seed.CONTEXT, seed.inventory_rows())
    acquired = AcquiredFile(seed.NAV_APP, "Makefile", "/ws/nav_app/Makefile", seed.VERSION, datetime(2026, 9, 1, 9, 0))
    error = ErrorRecord(ErrorStatus.MISSING_DATA, "mandatory file 'nav_app.xml' is missing", seed.NAV_APP, "source_code_repo", "skywatch/nftw")
    data = ModelSetupData(seed.CONTEXT, inventory, [acquired], [error], {"metadata": {"scale": {"apps": 2}}}, produced_by=seed.PRODUCER)

    payload = data.to_dict()

    assert set(payload) == {"context", "inventory", "acquired_files", "errors", "generated_at", "produced_by", "graph"}
    assert payload["context"]["project"]["name"] == seed.PROJECT
    assert payload["inventory"]["units"][0]["unit_name"] == seed.COMMON_LIB
    assert payload["acquired_files"] == [{
        "unit_name": seed.NAV_APP, "file_name": "Makefile", "file_path": "/ws/nav_app/Makefile",
        "package_version": seed.VERSION, "updated_at": "2026-09-01T09:00:00",
    }]
    assert payload["errors"][0]["status"] == "MISSING_DATA"
    assert set(payload["errors"][0]) == {"status", "reason", "source_name", "source_type", "project_platform", "occurred_at"}
    assert payload["produced_by"] == seed.PRODUCER
    assert data.scale == {"apps": 2}


def _record(payload):
    return ModelSetupDataRecord.from_payload(payload, seed.RUN_1, seed.PROJECT, seed.PLATFORM, seed.VERSION, Path("/ws/f.json"))


def test_record_reads_the_header_and_the_candidates_from_the_inventory():
    payload = {
        "generated_at": "2026-09-02T14:15:30",
        "produced_by": seed.PRODUCER,
        "inventory": {"units": [
            {"unit_name": seed.COMMON_LIB, "version": seed.VERSION, "is_candidate": False},
            {"unit_name": seed.NAV_APP, "version": "2.0.0", "is_candidate": True},
            {"unit_name": seed.SENSOR_APP, "version": seed.CANDIDATE_VERSION, "is_candidate": True},
        ]},
        "graph": {"metadata": {"scale": {"apps": 2}}},
    }

    record = _record(payload)

    assert record.to_dict() == {
        "run_id": seed.RUN_1, "project_id": seed.PROJECT, "platform_id": seed.PLATFORM, "version_id": seed.VERSION,
        "generated_at": "2026-09-02T14:15:30", "produced_by": seed.PRODUCER, "scale": {"apps": 2},
        "candidates": [
            {"unit_name": seed.NAV_APP, "version": "2.0.0"},
            {"unit_name": seed.SENSOR_APP, "version": seed.CANDIDATE_VERSION},
        ],
    }


def test_record_tolerates_an_unexpected_inventory_shape():
    assert _record({"generated_at": "2026-09-02T14:15:30", "inventory": {"units": "x"}}).candidates == []
    assert _record({"generated_at": "2026-09-02T14:15:30", "inventory": {"units": ["x"]}}).candidates == []


def test_record_is_none_for_a_payload_that_is_not_a_model_setup_data_file():
    assert _record({"nodes": []}) is None
    assert _record(["not", "a", "dict"]) is None


def _payload(**fields):
    payload = {
        "context": seed.CONTEXT.to_dict(), "inventory": {"units": []}, "acquired_files": [], "errors": [],
        "generated_at": "2026-09-02T14:15:30", "produced_by": seed.PRODUCER, "graph": {},
    }
    payload.update(fields)
    return payload


def test_check_accepts_a_produced_files_payload_for_its_selection():
    data = ModelSetupData(seed.CONTEXT, SoftwareUnitVersionInventory(seed.CONTEXT), [], [], {})

    check_payload(data.to_dict(), seed.PROJECT, seed.PLATFORM, seed.VERSION)
    check_payload({k: v for k, v in _payload().items() if k not in ("acquired_files", "errors")}, seed.PROJECT, seed.PLATFORM, seed.VERSION)


@pytest.mark.parametrize("payload, reason", [
    (["not", "a", "dict"], "a JSON object is expected"),
    (_payload(generated_at=None), "'generated_at' is missing"),
    (_payload(context=None), "'context' is missing"),
    (_payload(context={"project": {"project_id": seed.PROJECT}, "platform": {}, "version": {}}), "'context.platform.platform_id' is missing"),
    (_payload(inventory={"units": "x"}), "'inventory.units' is missing"),
    (_payload(graph=[]), "'graph' is missing"),
    (_payload(errors={}), "'errors' must be a list"),
])
def test_check_refuses_a_payload_without_the_files_shape(payload, reason):
    with pytest.raises(InvalidModelSetupData, match=reason):
        check_payload(payload, seed.PROJECT, seed.PLATFORM, seed.VERSION)


def test_check_refuses_a_file_of_another_selection():
    with pytest.raises(InvalidModelSetupData, match="file is for skywatch/nftw/1.0.0, not the selected skywatch/nftw/0.9.0"):
        check_payload(_payload(), seed.PROJECT, seed.PLATFORM, seed.OLD_VERSION)
