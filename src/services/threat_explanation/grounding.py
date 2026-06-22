"""
Grounding check: verifies LLM claims appear in retrieved context.

This is a heuristic, not a semantic checker. It extracts named entities
(IPs, attack names, technique IDs) from LLM output and checks whether
each appears verbatim in the context string.
"""

import re
from dataclasses import dataclass, field
from typing import List


_IP_PATTERN = re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b")
_TECHNIQUE_PATTERN = re.compile(r"\bT\d{4}(?:\.\d{3})?\b")
_ATTACK_KEYWORDS = [
    "DDoS", "DoS", "Mirai", "botnet", "C&C", "brute force",
    "reconnaissance", "spoofing", "SQL injection", "flooding",
    "SYN", "UDP", "TCP flood",
]


@dataclass
class GroundingResult:
    grounded_claims: int = 0
    ungrounded_claims: int = 0
    grounding_ratio: float = 0.0
    ungrounded_entities: List[str] = field(default_factory=list)


def check_grounding(llm_output: str, context: str) -> GroundingResult:
    """
    Check what fraction of entity mentions in llm_output appear in context.

    Entities checked: IP addresses, MITRE technique IDs, attack keywords.
    """
    if not llm_output.strip():
        return GroundingResult()

    entities = []
    entities.extend(_IP_PATTERN.findall(llm_output))
    entities.extend(_TECHNIQUE_PATTERN.findall(llm_output))
    for kw in _ATTACK_KEYWORDS:
        if kw.lower() in llm_output.lower():
            entities.append(kw)

    if not entities:
        return GroundingResult(grounded_claims=0, ungrounded_claims=0, grounding_ratio=1.0)

    context_lower = context.lower()
    grounded = [e for e in entities if e.lower() in context_lower]
    ungrounded = [e for e in entities if e.lower() not in context_lower]

    ratio = len(grounded) / len(entities) if entities else 1.0

    return GroundingResult(
        grounded_claims=len(grounded),
        ungrounded_claims=len(ungrounded),
        grounding_ratio=round(ratio, 3),
        ungrounded_entities=ungrounded,
    )
