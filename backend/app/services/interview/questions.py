"""Static question plan for the interview.

Deterministic and provider-independent. No LLM is used in Phase 04; the
reasoning service (Phase 06) is a separate concern. Each required topic has
one core question and at most one scripted follow-up.
"""

# Order matters: this is the order topics are asked in.
REQUIRED_TOPICS = [
    "problem",
    "affected_users",
    "current_process",
    "impact",
    "evidence",
    "constraints",
    "desired_outcome",
]

CORE_QUESTIONS = {
    "problem": "What is the core operational problem you are trying to solve?",
    "affected_users": "Who is affected by this problem, and how many people?",
    "current_process": "How is this handled today, step by step?",
    "impact": "What is the impact of this problem in time, money, or risk?",
    "evidence": "What concrete evidence shows this is a real, recurring problem?",
    "constraints": "What constraints exist (budget, tech, team, timeline, policy)?",
    "desired_outcome": "What would a successful outcome look like for you?",
}

FOLLOW_UP_QUESTIONS = {
    "problem": "Can you be more specific about exactly what goes wrong, and when?",
    "affected_users": "Which specific roles or teams feel this the most?",
    "current_process": "Where in that process does the most time or effort get lost?",
    "impact": "Can you quantify that impact even roughly (hours/week, cost/month)?",
    "evidence": "Do you have any numbers, tickets, or examples that back this up?",
    "constraints": "Which of those constraints is the hardest to work around?",
    "desired_outcome": "How would you measure whether that outcome was achieved?",
}

_FOLLOWUP_SUFFIX = ".followup"


def core_key(topic: str) -> str:
    return topic


def followup_key(topic: str) -> str:
    return topic + _FOLLOWUP_SUFFIX


def is_followup_key(key: str) -> bool:
    return key.endswith(_FOLLOWUP_SUFFIX)


def topic_for_key(key: str) -> str:
    if key.endswith(_FOLLOWUP_SUFFIX):
        return key[: -len(_FOLLOWUP_SUFFIX)]
    return key


def is_known_key(key: str) -> bool:
    topic = topic_for_key(key)
    if topic not in REQUIRED_TOPICS:
        return False
    if is_followup_key(key):
        return topic in FOLLOW_UP_QUESTIONS
    return topic in CORE_QUESTIONS
