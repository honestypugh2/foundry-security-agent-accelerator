"""Deterministic boundaries; injection signatures are a heuristic, not a proof."""

import re
from contextlib import ExitStack
from typing import Protocol, cast
from urllib.parse import urlsplit

from azure.ai.contentsafety import ContentSafetyClient
from azure.ai.contentsafety.models import AnalyzeTextOptions, AnalyzeTextResult
from azure.identity import DefaultAzureCredential

from .config import Settings
from .contracts import RetrievedEvidence, SecurityDecision
from .identity import TenantCredential

_INJECTION = re.compile(
    r"ignore\s+(?:all\s+)?(?:previous|prior|system)|"
    r"(?:system|developer)\s*(?:prompt|message)\s*:|"
    r"exfiltrat|send\s+(?:the\s+)?(?:secret|token)|override\s+(?:the\s+)?policy",
    re.IGNORECASE,
)
_SECRET = re.compile(
    r"(?i)(?:bearer\s+[a-z0-9._~+/-]+|"
    r"(?:api[_-]?key|password|token|secret)\s*[:=]\s*[^\s,;]+|"
    r"\b(?:ghp_|gho_|sk-)[a-z0-9_-]+)"
)
_EMAIL = re.compile(r"\b[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}\b")


def redact(text: str) -> str:
    return _EMAIL.sub("[REDACTED_EMAIL]", _SECRET.sub("[REDACTED]", text))


def inspect_content(text: str) -> SecurityDecision:
    blocked = bool(_INJECTION.search(text))
    return SecurityDecision(
        allowed=not blocked,
        reason="INJECTION_SIGNATURE" if blocked else "NO_KNOWN_SIGNATURE",
        control="untrusted-content",
    )


def check_citations(answer: str, documents: tuple[RetrievedEvidence, ...]) -> SecurityDecision:
    sources = {document.source_id for document in documents}
    citations = set(re.findall(r"\[([A-Za-z0-9._-]+)\]", answer))
    allowed = (
        bool(citations) and citations <= sources
    ) or answer.strip() == "I could not find this in approved policy sources."
    return SecurityDecision(
        allowed=allowed,
        reason="APPROVED_SOURCE_OR_ABSTENTION" if allowed else "OUT-01_CITATION_REQUIRED",
        control="output-provenance",
    )


def check_egress(url: str, allowed_hosts: frozenset[str]) -> SecurityDecision:
    parsed = urlsplit(url)
    allowed = (
        parsed.scheme == "https"
        and parsed.hostname in allowed_hosts
        and not parsed.username
        and not parsed.password
        and parsed.port in (None, 443)
    )
    return SecurityDecision(
        allowed=allowed, reason="ALLOWLIST" if allowed else "EGRESS_DENIED", control="egress"
    )


def check_delegation(target: str, allowed: frozenset[str]) -> SecurityDecision:
    ok = target in allowed
    return SecurityDecision(
        allowed=ok,
        reason="EXPLICIT_DELEGATE" if ok else "DELEGATION_DENIED",
        control="delegation",
    )


class ContentInspector(Protocol):
    def inspect(self, text: str) -> SecurityDecision: ...


class LocalInspector:
    def inspect(self, text: str) -> SecurityDecision:
        return inspect_content(text)


class AzureHeuristicInspector(LocalInspector):
    """Explicit Azure baseline when supplemental Content Safety is not configured."""

    def inspect(self, text: str) -> SecurityDecision:
        result = inspect_content(text)
        return result.model_copy(update={"control": "azure-baseline-heuristic-only"})


class SafetyQuery(Protocol):
    def __call__(self, body: AnalyzeTextOptions) -> AnalyzeTextResult: ...


class AzureContentInspector:
    """Content moderation supplements injection checks; it is NOT Prompt Shields or DLP."""

    def __init__(self, settings: Settings, analyze: SafetyQuery | None = None) -> None:
        if settings.mode != "azure" or not settings.content_safety_endpoint:
            raise ValueError("Azure Content Safety requires Azure mode and endpoint")
        self.settings = settings
        self.analyze = analyze

    def inspect(self, text: str) -> SecurityDecision:
        heuristic = inspect_content(text)
        if not heuristic.allowed:
            return heuristic
        with ExitStack() as stack:
            analyze = self.analyze
            if analyze is None:
                credential = stack.enter_context(
                    DefaultAzureCredential(authority=self.settings.authority)
                )
                client = stack.enter_context(
                    ContentSafetyClient(
                        self.settings.content_safety_endpoint,
                        TenantCredential(credential, self.settings.tenant_id),
                        credential_scopes=[self.settings.cognitive_scope],
                        retry_total=2,
                        connection_timeout=15,
                        read_timeout=30,
                        logging_enable=False,
                    )
                )
                analyze = cast(SafetyQuery, client.analyze_text)
            options = AnalyzeTextOptions(text=text)
            result = analyze(cast(AnalyzeTextOptions, options))
            categories = {str(item.category): item.severity for item in result.categories_analysis}
            if set(categories) != {"Hate", "SelfHarm", "Sexual", "Violence"} or any(
                value is None for value in categories.values()
            ):
                raise RuntimeError("Content Safety category evidence incomplete")
            denied = any(
                value is not None and value >= self.settings.content_safety_threshold
                for value in categories.values()
            )
            return SecurityDecision(
                allowed=not denied,
                reason="CONTENT_SAFETY_BLOCK" if denied else "CONTENT_SAFETY_WITHIN_THRESHOLD",
                control="azure-content-safety",
            )


def build_inspector(settings: Settings) -> ContentInspector:
    if settings.mode == "azure":
        if settings.content_safety_endpoint:
            return AzureContentInspector(settings)
        return AzureHeuristicInspector()
    return LocalInspector()
