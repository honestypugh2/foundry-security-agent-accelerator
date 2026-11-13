"""Explicit create-only setup for the separately reviewed live presentation profile."""

from contextlib import ExitStack
from typing import Protocol, cast

from azure.core.exceptions import ResourceNotFoundError
from azure.identity import DefaultAzureCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchField,
    SearchFieldDataType,
    SearchIndex,
)
from azure.search.documents.models import IndexingResult

from .agent import project_client
from .azure_ops import whoami
from .config import Settings
from .identity import TenantCredential
from .presentation_data import (
    PresentationRecord,
    approved_records,
    search_client,
    validate_presentation_settings,
)
from .presentation_live import ARGUMENTS, agent_definition, verify_definition


class UploadDocuments(Protocol):
    def upload_documents(self, documents: list[dict[str, object]]) -> list[IndexingResult]: ...


def create_resources(settings: Settings) -> dict[str, object]:
    validate_presentation_settings(settings, pinned=False)
    if whoami(settings)["status"] != "PASS":
        raise PermissionError("Selected Azure account does not match explicit configuration")
    if settings.presentation_agent_version:
        raise PermissionError(
            "Setup is create-only; review an explicit new agent/index before reuse"
        )
    with ExitStack() as stack:
        project = project_client(settings, stack)
        credential = stack.enter_context(DefaultAzureCredential(authority=settings.authority))
        indexes = stack.enter_context(
            SearchIndexClient(
                endpoint=settings.search_endpoint,
                credential=TenantCredential(credential, settings.tenant_id),
                audience=settings.search_audience,
                retry_total=0,
                connection_timeout=15,
                read_timeout=30,
                logging_enable=False,
            )
        )
        try:
            project.agents.get(agent_name=settings.presentation_agent_name)
        except ResourceNotFoundError:
            pass
        else:
            raise PermissionError("Presentation agent already exists; refusing an implicit update")
        try:
            indexes.get_index(settings.presentation_search_index)
        except ResourceNotFoundError:
            pass
        else:
            raise PermissionError("Presentation index already exists; refusing to overwrite data")
        fields = [
            SearchField(name="id", type=SearchFieldDataType.String, key=True),
            *[
                SearchField(name=name, type=SearchFieldDataType.String, filterable=True)
                for name in ("source_id", "section_id", "classification", "kind", "corpus_sha256")
            ],
            SearchField(name="text", type=SearchFieldDataType.String, searchable=True),
        ]
        indexes.create_index(SearchIndex(name=settings.presentation_search_index, fields=fields))
        client = search_client(settings, stack)
        records = approved_records()
        uploader = cast(UploadDocuments, client)
        results = uploader.upload_documents([record.model_dump() for record in records])
        if (
            len(results) != len(records)
            or any(not item.succeeded for item in results)
            or {item.key for item in results} != {record.id for record in records}
        ):
            raise RuntimeError("Synthetic upload incomplete; inspect index before retrying setup")
        # Point reads verify actual persisted content without relying on search-indexing latency.
        for expected in records:
            actual = client.get_document(
                expected.id, selected_fields=list(PresentationRecord.model_fields)
            )
            if (
                PresentationRecord.model_validate(
                    {key: actual[key] for key in PresentationRecord.model_fields}
                )
                != expected
            ):
                raise RuntimeError(
                    "Persisted synthetic Search content differs from approved corpus"
                )
        agent = project.agents.create_version(
            agent_name=settings.presentation_agent_name,
            definition=agent_definition(settings),
            description="Synthetic workshop only; four client-governed tools; DRY_RUN-only queue.",
        )
        pinned = project.agents.get_version(agent_name=agent.name, agent_version=str(agent.version))
        verify_definition(pinned.definition, settings)
        return {
            "status": "CREATED_AND_DEFINITION_VERIFIED_NOT_INVOCATION_PROOF",
            "agent": agent.name,
            "version": str(agent.version),
            "index": settings.presentation_search_index,
            "tools": list(ARGUMENTS),
            "records_verified": len(records),
            "next_step": "Pin FSA_PRESENTATION_AGENT_VERSION privately; authorize live scenarios",
            "publication": "NOT_PERFORMED",
            "native_integrations": "NOT_VALIDATED",
        }
