"""Sensitive-data detectors.

Detection is deliberately treated as IMPERFECT. Structured, high-precision
detectors produce redactable findings with typed placeholders. A separate
high-entropy detector flags unknown long tokens it cannot classify and marks
them NOT redactable, so the gateway can fail closed and request correction.
"""
import re

from app.schemas.privacy import Finding, SensitiveCategory as C

# Luhn check keeps credit-card detection honest (reduces false positives).
def _luhn_ok(digits: str) -> bool:
    total = 0
    for i, ch in enumerate(reversed(digits)):
        d = ord(ch) - 48
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


_PRIVATE_KEY = re.compile(
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----"
)
_AWS = re.compile(r"\bAKIA[0-9A-Z]{16}\b")
_API_SK = re.compile(r"\bsk-[A-Za-z0-9_\-]{16,}\b")
_BEARER = re.compile(r"(?i)\bbearer\s+([A-Za-z0-9._\-]{8,})")
_EMAIL = re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")
_CREDENTIAL = re.compile(
    r"(?i)\b(api[_-]?key|secret|password|passwd|token)\b\s*[=:]\s*(\S+)"
)
_SSN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
_CC = re.compile(r"\b(?:\d[ -]?){13,19}\b")
_PHONE = re.compile(r"(?<!\w)\+?\d[\d\s().\-]{7,}\d(?!\w)")
_HIGH_ENTROPY = re.compile(r"[A-Za-z0-9+/=_\-]{25,}")


def _overlaps(a_start, a_end, spans) -> bool:
    return any(not (a_end <= s or a_start >= e) for s, e in spans)


def detect(text: str) -> list[Finding]:
    findings: list[Finding] = []
    covered: list[tuple[int, int]] = []

    def add(start, end, category, confidence, redactable, placeholder):
        if _overlaps(start, end, covered):
            return
        covered.append((start, end))
        findings.append(Finding(
            category=category, start=start, end=end, confidence=confidence,
            redactable=redactable, placeholder=placeholder,
        ))

    # Order matters: most specific / highest severity first.
    for m in _PRIVATE_KEY.finditer(text):
        add(m.start(), m.end(), C.PRIVATE_KEY, 0.99, True, "[PRIVATE_KEY_REDACTED]")
    for m in _AWS.finditer(text):
        add(m.start(), m.end(), C.AWS_ACCESS_KEY, 0.97, True, "[AWS_KEY_REDACTED]")
    for m in _API_SK.finditer(text):
        add(m.start(), m.end(), C.API_KEY, 0.95, True, "[API_KEY_REDACTED]")
    for m in _BEARER.finditer(text):
        # redact only the token part (group 1); keep the word "Bearer"
        add(m.start(1), m.end(1), C.BEARER_TOKEN, 0.9, True, "[TOKEN_REDACTED]")
    for m in _EMAIL.finditer(text):
        add(m.start(), m.end(), C.EMAIL, 0.95, True, "[EMAIL_REDACTED]")
    for m in _CREDENTIAL.finditer(text):
        value = text[m.start(2):m.end(2)]
        # Do not re-flag an already-inserted placeholder (keeps the
        # residual re-scan from treating redacted output as a new secret).
        if re.fullmatch(r"\[[A-Z_]+\]", value):
            continue
        # redact only the value (group 2); keep the key for context
        add(m.start(2), m.end(2), C.CREDENTIAL_ASSIGNMENT, 0.9, True, "[REDACTED]")
    for m in _SSN.finditer(text):
        add(m.start(), m.end(), C.SSN, 0.9, True, "[SSN_REDACTED]")
    for m in _CC.finditer(text):
        digits = re.sub(r"\D", "", m.group())
        if 13 <= len(digits) <= 19 and _luhn_ok(digits):
            add(m.start(), m.end(), C.CREDIT_CARD, 0.92, True, "[CARD_REDACTED]")
    for m in _PHONE.finditer(text):
        add(m.start(), m.end(), C.PHONE, 0.6, True, "[PHONE_REDACTED]")

    # High-entropy unknown tokens: cannot classify -> NOT redactable (fail closed).
    for m in _HIGH_ENTROPY.finditer(text):
        s, e = m.start(), m.end()
        if _overlaps(s, e, covered):
            continue
        tok = m.group()
        has_alpha = any(ch.isalpha() for ch in tok)
        has_digit = any(ch.isdigit() for ch in tok)
        if has_alpha and has_digit:  # looks secret-ish, unknown structure
            covered.append((s, e))
            findings.append(Finding(
                category=C.UNKNOWN_SECRET, start=s, end=e, confidence=0.5,
                redactable=False, placeholder="[UNVERIFIED_SECRET]",
            ))

    findings.sort(key=lambda f: f.start)
    return findings
