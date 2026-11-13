from app.retrieval.fusion import rrf


def test_rrf_prefers_docs_ranked_high_in_both_lists():
    fused = rrf([["a", "b", "c"], ["b", "c", "d"]])
    assert fused[0][0] == "b"
    assert {i for i, _ in fused} == {"a", "b", "c", "d"}


def test_rrf_empty():
    assert rrf([[], []]) == []
