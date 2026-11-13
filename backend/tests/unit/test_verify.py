from app.agents.verify import excerpt_in_source, verify_item

HIT = {"id": "x", "text": "Every agreement by which anyone is restrained from exercising a lawful profession is void.",
       "meta": {"source_id": "S1", "section": "s.27"}}


def test_verified_when_excerpt_is_real():
    item = {"evidence_label": "L1", "legal_excerpt": "restrained from exercising a lawful profession"}
    status, cit = verify_item(item, [HIT])
    assert status == "verified" and cit["legal_section"] == "s.27"


def test_rejected_when_excerpt_fabricated():
    item = {"evidence_label": "L1", "legal_excerpt": "this sentence was invented by the model entirely"}
    assert verify_item(item, [HIT])[0] == "rejected"


def test_rejected_when_label_never_retrieved():
    assert verify_item({"evidence_label": "L9", "legal_excerpt": "anything at all goes here"}, [HIT])[0] == "rejected"


def test_flagged_when_no_citation():
    assert verify_item({"evidence_label": None}, [HIT])[0] == "flagged"


def test_short_excerpt_not_accepted():
    assert not excerpt_in_source("void", HIT["text"])
