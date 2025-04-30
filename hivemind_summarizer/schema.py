from pydantic import BaseModel


class PlatformSummariesActivityInput(BaseModel):
    date: str | None = None
    extract_text_only: bool = True
    platform_name: str | None = None
    community_id: str | None = None


class PlatformSummariesRangeActivityInput(BaseModel):
    start_date: str
    end_date: str
    extract_text_only: bool = True
    platform_name: str | None = None
    community_id: str | None = None


class PlatformGetCollectionNameInput(BaseModel):
    platform_id: str
    community_id: str


class PlatformFetchSummariesWorkflowInput(BaseModel):
    platform_id: str
    community_id: str
    start_date: str | None = None
    end_date: str | None = None
    extract_text_only: bool = True
