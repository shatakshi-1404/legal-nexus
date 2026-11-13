from app.core.redact import redact
from app.core.security import create_access_token, decode_token, hash_password, verify_password


def test_password_roundtrip():
    h = hash_password("correct horse battery")
    assert verify_password("correct horse battery", h) and not verify_password("wrong", h)


def test_token_roundtrip_and_tamper():
    t = create_access_token("user-1")
    assert decode_token(t) == "user-1" and decode_token(t + "x") is None


def test_redaction():
    r = redact("mail a.b@x.com phone 9876543210 PAN ABCDE1234F aadhaar 1234 5678 9012")
    for token in ("a.b@x.com", "9876543210", "ABCDE1234F", "1234 5678 9012"):
        assert token not in r
