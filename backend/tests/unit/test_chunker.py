from app.ingestion.chunker import chunk_segments, segment_clauses

DOC = """RENTAL AGREEMENT between A and B made on 12-03-2024 for the premises at Bhopal.
1. Term
The tenancy begins on 1 April 2024 and continues for eleven months unless terminated earlier.
1.1 The tenant may renew by written notice.
2. Rent
The tenant shall pay Rs. 15,000 per month on or before the fifth day of each month.
3. Termination
Either party may terminate this agreement by giving thirty days notice in writing.
"""


def test_segments_top_level_clauses_only():
    segs = segment_clauses([(1, DOC)])
    heads = [s.heading for s in segs]
    assert "Term" in heads and "Rent" in heads and "Termination" in heads
    term = next(s for s in segs if s.heading == "Term")
    assert "1.1 The tenant may renew" in term.text  # sub-clause stays with parent
    assert [s.ref for s in segs] == [f"CL-{i:03d}" for i in range(1, len(segs) + 1)]


def test_long_clause_is_split_with_limit():
    long = "1. Big\n" + " ".join(f"Sentence number {i} is here." for i in range(300))
    chunks = chunk_segments(segment_clauses([(1, long)]), max_chars=500)
    assert len(chunks) > 1 and all(len(c.text) <= 800 for c in chunks)


def test_unnumbered_document_falls_back_to_paragraphs():
    text = "\n\n".join("This is a paragraph of text. " * 20 for _ in range(4))
    assert len(segment_clauses([(1, text)])) >= 2
