"""Checks mandatory field presence over all acquired and parsed source data
and records each failure (SRS DSM-MDG req 17-18)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, List, Tuple

from mdg.domain.acquired_file import AcquiredFile
from mdg.domain.data_source import DataSourceConfig, SourceType
from mdg.domain.error_record import ErrorRecord, ErrorStatus
from mdg.domain.project_context import ProjectContext
from mdg.domain.source_data import Topic, UnitRelation


@dataclass(frozen=True)
class MandatoryFieldRule:
    """A field that must be present and non-empty on records of one type (req 17)."""
    field_name: str
    applies_to: type


class CheckMandatoryFields:
    """Applies the rules to every record and records reason, source name,
    source type, project/platform and time for each failure (req 18)."""

    def __init__(self, rules: List[MandatoryFieldRule]):
        self._rules = rules

    def execute(self, records: Iterable[Any], context: ProjectContext) -> List[ErrorRecord]:
        errors = []
        for record in records:
            for rule in self._rules:
                if isinstance(record, rule.applies_to) and getattr(record, rule.field_name, None) in (None, ""):
                    source_name, source_type = self._source(record)
                    errors.append(ErrorRecord(
                        ErrorStatus.MISSING_DATA,
                        f"'{rule.field_name}' is missing on {type(record).__name__}",
                        source_name, source_type, context.project_platform,
                    ))
        return errors

    @staticmethod
    def _source(record: Any) -> Tuple[str, str]:
        if isinstance(record, DataSourceConfig):
            return record.source_name, record.source_type.value
        if isinstance(record, (AcquiredFile, UnitRelation)):
            return record.unit_name, SourceType.SOURCE_CODE_REPO.value
        if isinstance(record, Topic):
            return record.name, SourceType.SOURCE_CODE_REPO.value
        return type(record).__name__, "unknown"
