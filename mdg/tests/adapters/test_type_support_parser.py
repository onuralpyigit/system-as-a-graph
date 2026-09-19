"""The mock type support parser over a run directory (SRS DSM-MDG req 19)."""

from fakes import seed
from mdg.adapters.source_data.type_support_parser import TypeSupportParser


def test_topics_are_the_seeded_manifests_topics_with_qos(tmp_path):
    parser = TypeSupportParser(tmp_path)

    topics = parser.get_topic_list()

    assert parser.run_dir == tmp_path
    assert isinstance(topics, set)
    assert {t.name for t in topics} == {seed.NAV_POSITION, seed.SENSOR_DATA}
    assert all(t.size and t.durability and t.reliability and t.transport_priority for t in topics)
