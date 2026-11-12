from .contracts import ActionProposal, PolicyDecision


def decide(proposal: ActionProposal) -> PolicyDecision:
    if proposal.amount > 1500:
        return PolicyDecision(outcome="DENY", reason="LIMIT_EXCEEDED")
    return PolicyDecision(outcome="REQUIRE_APPROVAL", reason="CONSEQUENTIAL_ACTION")
