import asyncio
from datetime import timedelta

from temporalio import activity, workflow
from temporalio.common import RetryPolicy
from temporalio.workflow import execute_activity
from .schema import IngestionRequest, BatchIngestionRequest, BatchDocument

with workflow.unsafe.imports_passed_through():
    from tc_hivemind_backend.ingest_qdrant import CustomIngestionPipeline
    from llama_index.core import Document


class BatchChunk(BatchIngestionRequest):
    """A smaller chunk of a BatchIngestionRequest for parallel processing."""
    pass


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


@workflow.defn
class BatchVectorIngestionWorkflow:
    """A Temporal workflow for processing batch document ingestion requests.

    This workflow handles the orchestration of batch document processing activities,
    including retry logic and timeout configurations for multiple documents.
    """

    @workflow.run
    async def run(self, ingestion_requests: BatchIngestionRequest) -> None:
        """Execute the batch ingestion workflow.

        Parameters
        ----------
        ingestion_requests : BatchIngestionRequest
            The batch request containing all necessary information for document processing,
            including community ID, platform ID, text content, and metadata for each document.

        Notes
        -----
        The workflow splits documents into smaller batches and processes them in parallel.
        Each batch implements a retry policy with the following configuration:
        - Initial retry interval: 1 second
        - Maximum retry interval: 1 minute
        - Maximum retry attempts: 3
        - Activity timeout: 10 minutes
        """
        batch_size: int = 10
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(minutes=1),
            maximum_attempts=3,
        )

        # Split documents into smaller batches
        document_chunks = []
        for i in range(0, len(ingestion_requests.document), batch_size):
            chunk_documents = ingestion_requests.document[i:i + batch_size]
            
            # Create a BatchChunk for this subset of documents
            batch_chunk = BatchChunk(
                communityId=ingestion_requests.communityId,
                platformId=ingestion_requests.platformId,
                collectionName=ingestion_requests.collectionName,
                document=chunk_documents
            )
            document_chunks.append(batch_chunk)

        # Process all chunks in parallel
        batch_activities = []
        for i, chunk in enumerate(document_chunks):
            activity_task = workflow.execute_activity(
                process_documents_batch,
                chunk,
                retry_policy=retry_policy,
                start_to_close_timeout=timedelta(minutes=10),
            )
            batch_activities.append(activity_task)

        # Wait for all batches to complete
        await asyncio.gather(*batch_activities)


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
        collection_name = ingestion_request.platformId
    else:
        collection_name = ingestion_request.collectionName

    # Initialize the ingestion pipeline
    # the collection name will be reconstructed in `CustomIngestionPipeline`
    # in the format of `[communityId]_[collection_name]`
    pipeline = CustomIngestionPipeline(
        community_id=ingestion_request.communityId,
        collection_name=collection_name,
    )

    document = Document(
        doc_id=ingestion_request.docId,
        text=ingestion_request.text,
        metadata=ingestion_request.metadata,
        excluded_embed_metadata_keys=ingestion_request.excludedEmbedMetadataKeys,
        excluded_llm_metadata_keys=ingestion_request.excludedLlmMetadataKeys,
    )

    pipeline.run_pipeline(docs=[document])


@activity.defn
async def process_documents_batch(
    batch_chunk: BatchChunk,
) -> None:
    """Process a batch chunk of documents according to the ingestion request specifications.

    Parameters
    ----------
    batch_chunk : BatchChunk
        A chunk containing a subset of documents from the original batch request,
        including community ID, platform ID, text content, and metadata for each document.

    Notes
    -----
    This activity processes a subset of documents from the larger batch,
    allowing for parallel processing and better resource management.
    """
    if batch_chunk.collectionName is None:
        collection_name = batch_chunk.platformId
    else:
        collection_name = batch_chunk.collectionName

    # Initialize the ingestion pipeline
    # the collection name will be reconstructed in `CustomIngestionPipeline`
    # in the format of `[communityId]_[collection_name]`
    pipeline = CustomIngestionPipeline(
        community_id=batch_chunk.communityId,
        collection_name=collection_name,
    )

    # Convert all documents in this chunk to Document objects
    documents = []
    for doc in batch_chunk.document:
        document = Document(
            doc_id=doc.docId,
            text=doc.text,
            metadata=doc.metadata,
            excluded_embed_metadata_keys=doc.excludedEmbedMetadataKeys,
            excluded_llm_metadata_keys=doc.excludedLlmMetadataKeys,
        )
        documents.append(document)

    # Process all documents in this chunk as a batch
    pipeline.run_pipeline(docs=documents)
