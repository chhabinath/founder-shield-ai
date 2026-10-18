"""Deterministic mock interview driver (no voice provider).

Runs a full interview from start to READY_FOR_BRIEF using scripted answers,
so the end-to-end flow and the Phase 06 reasoning service can be exercised
without any external provider.
"""
from app.services.interview import questions as Q

# Substantive canned answers (all fictional) keyed by topic.
DEFAULT_ANSWERS = {
    "problem": "Support tickets pile up overnight and nobody triages them until noon.",
    "affected_users": "Our 6 support agents and about 400 waiting customers each day.",
    "current_process": "Agents manually read every email inbox and copy items into a sheet.",
    "impact": "Roughly 15 agent-hours per week lost and slower first responses.",
    "evidence": "Our helpdesk export shows median first-response time above eight hours.",
    "constraints": "Small team, limited budget, must keep data on our own servers.",
    "desired_outcome": "Tickets auto-triaged by priority so urgent ones surface first.",
}


def run_mock_interview(engine, owner_id: str, answers: dict | None = None,
                       locale: str = "en"):
    """Drive the engine to completion. Returns (session, records)."""
    answers = {**DEFAULT_ANSWERS, **(answers or {})}
    session = engine.start(owner_id, locale=locale, provider="mock")

    # Safety bound so a logic bug can never loop forever.
    for _ in range(100):
        nxt = engine.next_question(session.id, owner_id)
        if not nxt.has_question:
            break
        q = nxt.question
        text = answers.get(q.topic, "A clear and sufficiently detailed answer.")
        engine.submit_answer(session.id, owner_id, q.key, text)

    session = engine.get_session(session.id, owner_id)
    records = engine.records.list_for_session(session.id, owner_id)
    return session, records
