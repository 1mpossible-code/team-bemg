import security.security as sec


def test_read():
    recs = sec.read()
    assert isinstance(recs, dict)
    for feature in recs:
        assert isinstance(feature, str)
        assert len(feature) > 0


def test_read_feature_legacy_shape_is_preserved():
    feature = sec.read_feature(sec.PEOPLE)
    assert feature == sec.temp_recs[sec.PEOPLE]


def test_read_protocol_builds_richer_protocol_view():
    protocol = sec.read_protocol(sec.PEOPLE)
    assert protocol is not None
    assert protocol.name == sec.PEOPLE
    assert protocol.create.login is True
    assert sec.is_permitted(sec.PEOPLE, sec.CREATE, user_id='ejc369@nyu.edu')
    assert not sec.is_permitted(sec.PEOPLE, sec.CREATE, user_id='someone-else@nyu.edu')
