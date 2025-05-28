from datetime import timedelta

from temporalio import activity, workflow
from temporalio.common import RetryPolicy
from temporalio.workflow import execute_activity
from .schema import IngestionRequest

with workflow.unsafe.imports_passed_through():
    from tc_hivemind_backend.ingest_qdrant import CustomIngestionPipeline
    from llama_index.core import Document


@workflow.defn
class VectorIngestionWorkflow:
    """A Temporal workflow for processing document ingestion requests.

    This workflow handles the orchestration of document processing activities,
    including retry logic and timeout configurations.
    """

    @workflow.run
    async def run(self, ingestion_request: IngestionRequest) -> None:
        """Execute the ingestion workflow.

        Parameters
        ----------
        ingestion_request : IngestionRequest
            The request containing all necessary information for document processing,
            including community ID, platform ID, text content, and metadata.

        Notes
        -----
        The workflow implements a retry policy with the following configuration:
        - Initial retry interval: 1 second
        - Maximum retry interval: 1 minute
        - Maximum retry attempts: 3
        - Activity timeout: 5 minutes
        """
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(minutes=1),
            maximum_attempts=3,
        )

        await execute_activity(
            process_document,
            ingestion_request,
            retry_policy=retry_policy,
            start_to_close_timeout=timedelta(minutes=5),
        )


@activity.defn
async def process_document(
    ingestion_request: IngestionRequest,
) -> None:
    """Process the document according to the ingestion request specifications.

    Parameters
    ----------
    ingestion_request : IngestionRequest
        The request containing all necessary information for document processing,
        including community ID, platform ID, text content, and metadata.

    Notes
    -----
    This activity will be implemented by the user to handle the actual document
    processing logic, including any necessary embedding or LLM operations.
    """
    if ingestion_request.collectionName is None:
        collection_name = (
            f"{ingestion_request.communityId}_{ingestion_request.platformId}"
        )
    else:
        collection_name = ingestion_request.collectionName

    # Initialize the ingestion pipeline
    pipeline = CustomIngestionPipeline(
        community_id=ingestion_request.communityId,
        collection_name=collection_name,
    )

    document = Document(
        doc_id=ingestion_request.docId,
        text=ingestion_request.text,
        metadata=ingestion_request.metadata,
    )

    pipeline.run_pipeline(docs=[document])
