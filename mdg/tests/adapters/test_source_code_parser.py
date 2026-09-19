"""The source code parser: topic relations from the unit manifest and library
uses from Java imports (SRS DSM-MDG req 13, 19)."""

from pathlib import Path

from fakes import seed
from mdg.adapters.source_code.mandatory_files import MandatoryFiles
from mdg.adapters.source_data.source_code_parser import SourceCodeParser
from mdg.config import SourceParserConfig
from mdg.domain.source_data import RelationKind, UnitRelation


def _parser(**settings) -> SourceCodeParser:
    config = SourceParserConfig(**{
        "import_domain_prefix": seed.IMPORT_PREFIX, "dependency_suffixes": [seed.DEPENDENCY_SUFFIX], **settings,
    })
    return SourceCodeParser(config, MandatoryFiles([seed.MAKEFILE_INCLUDE]))


def _unit(tmp_path: Path, manifest: str = None, java: str = None, manifest_dir: str = "src") -> Path:
    unit_dir = tmp_path / seed.NAV_APP
    unit_dir.mkdir()
    if manifest is not None:
        (unit_dir / manifest_dir).mkdir(parents=True)
        (unit_dir / manifest_dir / "nav_app.xml").write_text(manifest, encoding="utf-8")
    if java is not None:
        (unit_dir / "NavApp.java").write_text(java, encoding="utf-8")
    return unit_dir


def _relations(unit_dir: Path, parser: SourceCodeParser = None):
    return set((parser or _parser()).parse(unit_dir, seed.NAV_APP))


def test_manifest_topics_and_java_imports_become_relations(tmp_path: Path):
    unit_dir = _unit(tmp_path, seed.NAV_APP_MANIFEST, seed.NAV_APP_JAVA)

    assert _relations(unit_dir) == {
        UnitRelation(seed.NAV_APP, seed.NAV_POSITION, RelationKind.PUBLISHES),
        UnitRelation(seed.NAV_APP, seed.SENSOR_DATA, RelationKind.SUBSCRIBES),
        UnitRelation(seed.NAV_APP, seed.COMMON_LIB, RelationKind.USES),
    }


def test_manifest_is_found_anywhere_under_the_unit_dir(tmp_path: Path):
    unit_dir = _unit(tmp_path, seed.SENSOR_APP_MANIFEST, manifest_dir="generated/topics")

    assert _relations(unit_dir) == {UnitRelation(seed.NAV_APP, seed.SENSOR_DATA, RelationKind.PUBLISHES)}


def test_pubsub_expands_and_unknown_roles_and_dummy_topics_are_skipped(tmp_path: Path):
    manifest = (
        f'<unit><topic name="{seed.NAV_POSITION}" role="pubsub"/>'
        '<topic name="odd" role="broadcast"/><topic name="DummyTopic" role="pub"/></unit>'
    )
    unit_dir = _unit(tmp_path, manifest)

    assert _relations(unit_dir, _parser(dummy_topic_names=["DummyTopic"])) == {
        UnitRelation(seed.NAV_APP, seed.NAV_POSITION, RelationKind.PUBLISHES),
        UnitRelation(seed.NAV_APP, seed.NAV_POSITION, RelationKind.SUBSCRIBES),
    }


def test_topic_element_name_is_configurable(tmp_path: Path):
    unit_dir = _unit(tmp_path, f'<unit><mytopic name="{seed.NAV_POSITION}" role="pub"/><topic name="ignored" role="pub"/></unit>')

    assert {r.target for r in _relations(unit_dir, _parser(topic_element="mytopic"))} == {seed.NAV_POSITION}


def test_only_imports_under_the_prefix_with_a_dependency_suffix_count(tmp_path: Path):
    java = (
        f"package {seed.IMPORT_PREFIX}.{seed.NAV_APP};\n"
        f"import {seed.IMPORT_PREFIX}.common_utils.Helper;\n"
        f"import {seed.IMPORT_PREFIX}.{seed.NAV_APP}.Self;\n"
        f"import other.vendor.{seed.COMMON_LIB}.Utils;\n"
        f"// import {seed.IMPORT_PREFIX}.comment_lib.X;\n"
        f"import {seed.IMPORT_PREFIX}.{seed.COMMON_LIB}.Utils;\n"
    )
    unit_dir = _unit(tmp_path, java=java)

    assert _relations(unit_dir) == {UnitRelation(seed.NAV_APP, seed.COMMON_LIB, RelationKind.USES)}


def test_invalid_manifest_and_empty_unit_yield_nothing(tmp_path: Path):
    assert _relations(_unit(tmp_path, "<unit><topic")) == set()
    assert _parser().parse(tmp_path / "empty", seed.SENSOR_APP) == []
