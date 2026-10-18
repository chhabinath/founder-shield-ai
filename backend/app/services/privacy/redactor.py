"""Apply redactions to text using detected findings.

Only `redactable` findings are applied. Replacement is done right-to-left so
earlier offsets remain valid. Surrounding business context is preserved.
"""
from app.schemas.privacy import Finding


def apply_redactions(text: str, findings: list[Finding]) -> str:
    redactable = sorted(
        [f for f in findings if f.redactable],
        key=lambda f: f.start,
        reverse=True,
    )
    out = text
    for f in redactable:
        out = out[: f.start] + f.placeholder + out[f.end :]
    return out
