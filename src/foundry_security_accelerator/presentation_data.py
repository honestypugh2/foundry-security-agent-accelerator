"""Dedicated, content-pinned synthetic Search corpus; never reads an equipment/customer index."""

import hashlib
import json
from contextlib import ExitStack
from typing import Literal, cast

from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient

from .config import Settings
from .contracts import Contract
from .identity import TenantCredential
from .presentation_runtime import load_corpus
from .retrieval import SearchQuery


class PresentationRecord(Contract):
    id: str
    source_id: str
    section_id: str
    classification: Literal["Public", "Internal", "Confidential"]
    text: str
    kind: Literal["policy", "ticket"]
    corpus_sha256: str


def corpus_sha256() -> str:
    return hashlib.sha256(load_corpus().model_dump_json().encode()).hexdigest()


def approved_records() -> tuple[PresentationRecord, ...]:
    corpus = load_corpus()
    digest = corpus_sha256()
    return tuple(
        [
            PresentationRecord(
                id=f"{document.source_id}-{section.section_id}",
                source_id=document.source_id,
                section_id=section.section_id,
                classification=document.classification,
                text=f"{document.title}: {section.text}",
                kind="policy",
                corpus_sha256=digest,
            )
            for document in corpus.documents
            for section in document.sections
        ]
        + [
            PresentationRecord(
                id=ticket.ticket_id,
                source_id=ticket.ticket_id,
                section_id="status",
                classification=ticket.classification,
                text=f"{ticket.ticket_id}: {ticket.status}. {ticket.summary}",
                kind="ticket",
                corpus_sha256=digest,
            )
            for ticket in corpus.tickets
        ]
    )


def literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def validate_presentation_settings(settings: Settings, *, pinned: bool = True) -> None:
    if settings.mode != "azure":
        raise ValueError("Presentation services require Azure mode")
    if (
        not settings.presentation_agent_name
        or settings.presentation_agent_name == settings.agent_name
        or not settings.presentation_search_index
        or settings.presentation_search_index == settings.search_index
    ):
        raise ValueError("Presentation agent and index must be separate from equipment resources")
    if pinned and not settings.presentation_agent_version:
        raise ValueError("Pin FSA_PRESENTATION_AGENT_VERSION after reviewing setup output")


def search_client(settings: Settings, stack: ExitStack) -> SearchClient:
    credential = stack.enter_context(DefaultAzureCredential(authority=settings.authority))
    return stack.enter_context(
        SearchClient(
            endpoint=settings.search_endpoint,
            index_name=settings.presentation_search_index,
            credential=TenantCredential(credential, settings.tenant_id),
            audience=settings.search_audience,
            retry_total=0,
            connection_timeout=15,
            read_timeout=30,
            logging_enable=False,
        )
    )


class PresentationSearch:
    def __init__(self, settings: Settings, query: SearchQuery | None = None) -> None:
        validate_presentation_settings(settings)
        self.settings = settings
        self.query = query

    def search(
        self,
        text: str,
        classifications: frozenset[str],
        *,
        source_id: str = "",
        section_id: str = "",
        kind: str = "policy",
    ) -> tuple[PresentationRecord, ...]:
        allowed = classifications & frozenset({"Public", "Internal"})
        if not allowed:
            return ()
        conditions = [
            "(" + " or ".join(f"classification eq {literal(c)}" for c in sorted(allowed)) + ")",
            f"corpus_sha256 eq {literal(corpus_sha256())}",
            f"kind eq {literal(kind)}",
        ]
        if source_id:
            conditions.append(f"source_id eq {literal(source_id)}")
        if section_id:
            conditions.append(f"section_id eq {literal(section_id)}")
        expected = {record.id: record for record in approved_records()}
        with ExitStack() as stack:
            query = self.query or cast(SearchQuery, search_client(self.settings, stack).search)
            rows = query(
                search_text=text,
                filter=" and ".join(conditions),
                select=list(PresentationRecord.model_fields),
                top=8,
            )
            results: list[PresentationRecord] = []
            for row in rows:
                record = PresentationRecord.model_validate(
                    {key: row[key] for key in PresentationRecord.model_fields}
                )
                if (
                    record != expected.get(record.id)
                    or record.classification not in allowed
                    or record.kind != kind
                    or (source_id and record.source_id != source_id)
                    or (section_id and record.section_id != section_id)
                ):
                    raise PermissionError(
                        "Search returned unauthorized or modified synthetic evidence"
                    )
                results.append(record)
                if len(results) > 8:
                    raise RuntimeError("Search exceeded the bounded evidence limit")
        return tuple(results)


def definition_digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    ).hexdigest()
