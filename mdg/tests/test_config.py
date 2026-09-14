"""mdg.ini loading: the shipped file, a missing file and overriding options."""

from mdg.config import MDG_INI, PACKAGE_DIR, load


def test_shipped_mdg_ini_is_loaded():
    config = load(MDG_INI)

    assert config.workspace.path == "workspace"
    assert config.workspace.system_repo == "system_repo"
    assert config.workspace.root() == PACKAGE_DIR / "workspace"
    assert config.mandatory_files.makefile_include_patterns == ["include/Makefile_java.mk"]
    assert config.source_parser.dummy_topic_names == ["DummyTopic"]
    assert config.source_parser.import_domain_prefix == "a.b.c"
    assert config.source_parser.dependency_suffixes == ["_lib"]
    assert config.source_parser.topic_element == "topic"
    assert config.build.run_regenerate_code is False


def test_missing_file_yields_defaults(tmp_path):
    config = load(tmp_path / "absent.ini")

    assert config.workspace.system_repo == "system_repo"
    assert config.mandatory_files.makefile_include_patterns == []
    assert config.source_parser.import_domain_prefix == ""
    assert config.build.run_regenerate_code is False


def test_options_override_defaults(tmp_path):
    ini = tmp_path / "mdg.ini"
    ini.write_text(
        "[workspace]\npath = /custom/ws\nsystem_repo = sys\n"
        "[source_parser]\nimport_domain_prefix = x.y\ndependency_suffixes = _module, _core\n"
        "[build]\nrun_regenerate_code = true\n",
        encoding="utf-8",
    )

    config = load(ini)

    assert str(config.workspace.root()) == "/custom/ws"
    assert config.workspace.system_repo == "sys"
    assert config.source_parser.import_domain_prefix == "x.y"
    assert config.source_parser.dependency_suffixes == ["_module", "_core"]
    assert config.build.run_regenerate_code is True
