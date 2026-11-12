"""Azure Search and offline retrieval with identical entitlement boundaries.

Pattern adapted from ready-enterprise-ai-platform/packages/retrieval/azure_search.py
(MIT); see docs/reuse-and-attribution.md. No source-specific data is included.
"""

from collections.abc import Iterable, Mapping
from contextlib import ExitStack
from typing import Protocol, cast

from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient

from .config import Settings
from .contracts import RetrievedEvidence, UserRequest
from .identity import TenantCredential

DOCUMENTS = (
    RetrievedEvidence(
        source_id="equipment-001",
        title="Synthetic equipment policy",
        content="Equipment requests up to 1500 credits need independent human approval.",
        entitlement="employee",
    ),
    RetrievedEvidence(
        source_id="finance-001",
        title="Synthetic finance planning policy",
        content="Finance reserve is restricted to the finance group.",
        entitlement="finance",
    ),
)


def retrieve(
    request: UserRequest, documents: tuple[RetrievedEvidence, ...] = DOCUMENTS
) -> tuple[RetrievedEvidence, ...]:
    return tuple(doc for doc in documents if doc.entitlement in request.entitlements)


class Retriever(Protocol):
    def search(self, request: UserRequest) -> tuple[RetrievedEvidence, ...]: ...


class LocalRetriever:
    def search(self, request: UserRequest) -> tuple[RetrievedEvidence, ...]:
        return retrieve(request)


class SearchQuery(Protocol):
    def __call__(
        self, *, search_text: str, filter: str, select: list[str], top: int
    ) -> Iterable[Mapping[str, object]]: ...


class AzureSearchRetriever:
    def __init__(self, settings: Settings, query: SearchQuery | None = None) -> None:
        if settings.mode != "azure":
            raise ValueError("Azure Search requires Azure mode")
        self.settings = settings
        self.query = query

    @staticmethod
    def entitlement_filter(entitlements: frozenset[str]) -> str:
        if not entitlements:
            return "false"
        # Equality avoids delimiter injection into search.in; escape OData literals.
        return " or ".join(
            f"entitlement eq '{group.replace(chr(39), chr(39) * 2)}'"
            for group in sorted(entitlements)
        )

    def search(self, request: UserRequest) -> tuple[RetrievedEvidence, ...]:
        if not request.entitlements:
            return ()
        with ExitStack() as stack:
            query = self.query
            if query is None:
                credential = stack.enter_context(
                    DefaultAzureCredential(authority=self.settings.authority)
                )
                client = stack.enter_context(
                    SearchClient(
                        endpoint=self.settings.search_endpoint,
                        index_name=self.settings.search_index,
                        credential=TenantCredential(credential, self.settings.tenant_id),
                        audience=self.settings.search_audience,
                        retry_total=2,
                        connection_timeout=15,
                        read_timeout=30,
                        logging_enable=False,
                    )
                )
                query = cast(SearchQuery, client.search)
            results = query(
                search_text=request.text,
                filter=self.entitlement_filter(request.entitlements),
                select=["source_id", "title", "content", "entitlement", "classification"],
                top=5,
            )
            evidence: list[RetrievedEvidence] = []
            for result in results:
                fields = {
                    field: result[field]
                    for field in ("source_id", "title", "content", "entitlement", "classification")
                }
                document = RetrievedEvidence.model_validate(fields)
                if document.entitlement not in request.entitlements:
                    raise PermissionError("Search returned unauthorized evidence")
                evidence.append(document)
            return tuple(evidence)


def build_retriever(settings: Settings) -> Retriever:
    return LocalRetriever() if settings.mode == "local" else AzureSearchRetriever(settings)
