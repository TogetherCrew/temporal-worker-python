# Simple Ingestion Workflows

This module provides Temporal workflows for ingesting documents into the vector database (Qdrant) using the TC Hivemind backend.

## Available Workflows

### 1. VectorIngestionWorkflow

A workflow for processing single document ingestion requests.

**Usage:**
```python
from hivemind_etl.simple_ingestion.schema import IngestionRequest
from temporalio.client import Client

# Create single ingestion request
request = IngestionRequest(
    communityId="my_community",
    platformId="my_platform", 
    text="Document content here...",
    metadata={
        "title": "Document Title",
        "author": "Author Name"
    }
)

# Execute workflow
client = await Client.connect("localhost:7233")
await client.execute_workflow(
    "VectorIngestionWorkflow",
    request,
    id="single-ingestion-123",
    task_queue="hivemind-etl"
)
```

### 2. BatchVectorIngestionWorkflow

A workflow for processing multiple document ingestion requests in parallel batches for improved efficiency.

**Key Features:**
- **Automatic Chunking**: Large batches are automatically split into smaller parallel chunks
- **Parallel Processing**: Multiple `process_documents_batch` activities run simultaneously 
- **Configurable Batch Size**: Control the size of each processing chunk (default: 10 documents)
- **Same Collection**: All documents in a batch request must belong to the same community and collection
- **Error Handling**: Same retry policy as single document workflow but with longer timeout for batch processing

**Usage:**
```python
from hivemind_etl.simple_ingestion.schema import BatchIngestionRequest, BatchDocument
from temporalio.client import Client

# Create batch ingestion request
batch_request = BatchIngestionRequest(
    communityId="my_community",
    platformId="my_platform",
    collectionName="optional_custom_collection",  # Optional
    document=[
        BatchDocument(
            docId="doc_1",
            text="First document content...",
            metadata={"title": "Document 1"},
            excludedEmbedMetadataKeys=["some_key"],
            excludedLlmMetadataKeys=["other_key"]
        ),
        BatchDocument(
            docId="doc_2", 
            text="Second document content...",
            metadata={"title": "Document 2"}
        ),
        # ... more documents
    ]
)

# Execute batch workflow
client = await Client.connect("localhost:7233")
await client.execute_workflow(
    "BatchVectorIngestionWorkflow",
    batch_request,
    10,  # batch_size: optional, default is 10
    id="batch-ingestion-123", 
    task_queue="hivemind-etl"
)
```

## Schema Reference

### IngestionRequest (Single Document)

```python
class IngestionRequest(BaseModel):
    communityId: str                          # Community identifier
    platformId: str                           # Platform identifier  
    text: str                                # Document text content
    metadata: dict                           # Document metadata
    docId: str = str(uuid4())               # Unique document ID (auto-generated)
    excludedEmbedMetadataKeys: list[str] = [] # Keys to exclude from embedding
    excludedLlmMetadataKeys: list[str] = []   # Keys to exclude from LLM processing
    collectionName: str | None = None        # Optional custom collection name
```

### BatchIngestionRequest (Multiple Documents)

```python
class BatchIngestionRequest(BaseModel):
    communityId: str                          # Community identifier
    platformId: str                           # Platform identifier
    collectionName: str | None = None        # Optional custom collection name
    document: list[BatchDocument]            # List of documents to process

class BatchDocument(BaseModel):
    docId: str                               # Unique document ID
    text: str                                # Document text content
    metadata: dict                           # Document metadata
    excludedEmbedMetadataKeys: list[str] = [] # Keys to exclude from embedding
    excludedLlmMetadataKeys: list[str] = []   # Keys to exclude from LLM processing
```

## Collection Naming

- **Default**: `{communityId}_{platformId}`
- **Custom**: `{communityId}_{collectionName}` (when `collectionName` is provided)

The collection name reconstruction is handled automatically by the `CustomIngestionPipeline`.

## Performance Considerations

### When to Use Batch vs Single Workflows

**Use BatchVectorIngestionWorkflow when:**
- Processing multiple documents from the same community/collection
- Bulk importing large datasets
- You have 10+ documents to process together
- You want to maximize throughput with parallel processing

**Use VectorIngestionWorkflow when:**
- Processing single documents in real-time
- Documents arrive individually
- You need immediate processing
- Simple use cases with occasional documents

### Batch Processing Optimizations

The batch workflow automatically optimizes performance by:

1. **Parallel Chunking**: Large batches are split into smaller chunks that process simultaneously
2. **Configurable Batch Size**: Tune chunk size based on your system resources (default: 10)
3. **Pipeline Reuse**: One `CustomIngestionPipeline` instance per chunk
4. **Bulk Operations**: All documents in a chunk are processed together
5. **Concurrent Execution**: Multiple chunks can run in parallel using asyncio.gather()

## Error Handling

Both workflows implement the same retry policy:
- **Initial retry interval**: 1 second
- **Maximum retry interval**: 1 minute  
- **Maximum attempts**: 3
- **Timeout**: 5 minutes (single), 10 minutes (batch)

## Testing

Use the provided test script to verify functionality:

```bash
python test_batch_workflow.py
```

The test script demonstrates:
- Batch processing with multiple documents
- Mixed collection handling
- Comparison between single and batch workflows

## Integration

Both workflows are automatically registered in the Temporal worker through `registry.py`. Ensure your worker includes:

```python
from registry import WORKFLOWS, ACTIVITIES

# Worker setup includes both workflows and activities
worker = Worker(
    client=client,
    task_queue="hivemind-etl", 
    workflows=WORKFLOWS,
    activities=ACTIVITIES
)
``` 