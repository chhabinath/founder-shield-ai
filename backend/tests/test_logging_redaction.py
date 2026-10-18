import logging

from app.logging import RedactionFilter, redact


def test_redacts_email_phone_key_token():
    raw = (
        "contact jane.doe@example.com or +1 (415) 555-2671 "
        "api_key=supersecret123 Bearer abc.def.ghi sk-ABCDEF123456"
    )
    out = redact(raw)
    assert "jane.doe@example.com" not in out
    assert "supersecret123" not in out
    assert "abc.def.ghi" not in out
    assert "sk-ABCDEF123456" not in out
    assert "[REDACTED_EMAIL]" in out


def test_filter_mutates_record_in_place():
    f = RedactionFilter()
    rec = logging.LogRecord(
        "t", logging.INFO, __file__, 1,
        "login for user@example.com", None, None,
    )
    assert f.filter(rec) is True
    assert "user@example.com" not in rec.getMessage()
