"""The mandatory field presence check and its error records (SRS DSM-MDG req 17-18)."""

from datetime import datetime

from fakes import seed
from mdg.domain.acquired_file import AcquiredFile
from mdg.domain.data_source import DataSourceConfig, SourceType
from mdg.domain.error_record import ErrorStatus
from mdg.domain.source_data import RelationKind, Topic, UnitRelation
from mdg.services.check_mandatory_fields import CheckMandatoryFields, MandatoryFieldRule


def test_complete_records_pass():
    records = [
        AcquiredFile(seed.NAV_APP, "Makefile", "/ws/Makefile", seed.VERSION, datetime.now()),
        UnitRelation(seed.NAV_APP, seed.NAV_POSITION, RelationKind.PUBLISHES),
        Topic(seed.NAV_POSITION),
    ]
    rules = [MandatoryFieldRule("file_name", AcquiredFile), MandatoryFieldRule("target", UnitRelation), MandatoryFieldRule("name", Topic)]

    assert CheckMandatoryFields(rules).execute(records, seed.CONTEXT) == []


def test_missing_field_yields_the_required_record():
    errors = CheckMandatoryFields([MandatoryFieldRule("name", Topic)]).execute([Topic("")], seed.CONTEXT)

    assert len(errors) == 1
    assert errors[0].status is ErrorStatus.MISSING_DATA
    assert errors[0].reason == "'name' is missing on Topic"
    assert errors[0].source_type == "source_code_repo"
    assert errors[0].project_platform == "skywatch/nftw"
    assert errors[0].occurred_at is not None


def test_rule_applies_only_to_its_record_type():
    rules = [MandatoryFieldRule("user_info", DataSourceConfig)]
    relation = UnitRelation(seed.NAV_APP, "", RelationKind.PUBLISHES)
    source = DataSourceConfig(SourceType.CONFIG_MGMT_DB, "mysql", "mysql", seed.CONFIG_DB_ADDRESS, "")

    errors = CheckMandatoryFields(rules).execute([relation, source], seed.CONTEXT)

    assert [(e.source_name, e.source_type) for e in errors] == [("mysql", "config_mgmt_db")]
