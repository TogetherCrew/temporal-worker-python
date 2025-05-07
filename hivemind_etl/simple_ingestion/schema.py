from pydantic import BaseModel
from uuid import uuid4


class IngestionRequest(BaseModel):
    """A model representing an ingestion request for document processing.

    Parameters
    ----------
    communityId : str
        The unique identifier of the community.
    platformId : str
        The unique identifier of the platform.
    text : str
        The text content to be processed.
    metadata : dict
        Additional metadata associated with the document.
    docId : str, optional
        Unique identifier for the document. If not provided, a UUID will be generated.
        Default is a new UUID.
    excludedEmbedMetadataKeys : list[str], optional
        List of metadata keys to exclude from embedding process.
        Default is an empty list.
    excludedLlmMetadataKeys : list[str], optional
        List of metadata keys to exclude from LLM processing.
        Default is an empty list.
    collectionName : str | None, optional
        The name of the collection to use for the document.
        Default is `None` means it would follow the default pattern of `[communityId]_[platformId]`
    """

    communityId: str
    platformId: str
    text: str
    metadata: dict
    docId: str = str(uuid4())
    excludedEmbedMetadataKeys: list[str] = []
    excludedLlmMetadataKeys: list[str] = []
    collectionName: str | None = None
