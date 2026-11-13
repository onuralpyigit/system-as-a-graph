"""The mock message file parser over a run directory (SRS DSM-MDG req 19)."""

from fakes import seed
from mdg.adapters.source_data.message_file_parser import MessageFileParser
from mdg.domain.source_data import RelationKind


def test_messages_are_the_seeded_messages_with_their_fields(tmp_path):
    parser = MessageFileParser(tmp_path)

    messages = parser.get_message_list()

    assert parser.run_dir == tmp_path
    assert isinstance(messages, set)
    assert {m.name for m in messages} == {seed.MSG_NAV_POSITION, seed.MSG_SENSOR_DATA}
    assert all(m.id and m.size and m.frequency for m in messages)


def test_message_relations_are_send_or_receive_to_a_known_message(tmp_path):
    parser = MessageFileParser(tmp_path)

    relations = parser.get_message_relations()
    names = {m.name for m in parser.get_message_list()}

    assert relations
    assert all(r.kind in (RelationKind.SEND, RelationKind.RECEIVE) for r in relations)
    assert {r.target for r in relations} <= names
