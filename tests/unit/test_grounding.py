from src.services.threat_explanation.grounding import check_grounding, GroundingResult


def test_grounding_finds_grounded_claims():
    context = "Device 192.168.1.195 was involved in Mirai botnet attack. Protocol TCP was used."
    llm_output = "The device at 192.168.1.195 used TCP and was part of the Mirai campaign."
    result = check_grounding(llm_output, context)
    assert isinstance(result, GroundingResult)
    assert result.grounding_ratio > 0.5


def test_grounding_flags_hallucinated_ips():
    context = "Device 192.168.1.195 communicated with 10.0.0.1."
    llm_output = "The attacker used IP 172.16.99.99 to launch the attack from Germany."
    result = check_grounding(llm_output, context)
    assert result.grounding_ratio < 1.0
    assert "172.16.99.99" in result.ungrounded_entities


def test_grounding_empty_output():
    result = check_grounding("", "some context")
    assert result.grounded_claims == 0
    assert result.ungrounded_claims == 0
