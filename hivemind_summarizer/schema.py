from pydantic import BaseModel


class PlatformSummariesActivityInput(BaseModel):
    date: str | None = None
    extract_text_only: bool = True
    platform_id: str | None = None
    community_id: str | None = None


class PlatformSummariesRangeActivityInput(BaseModel):
    start_date: str
    end_date: str
    extract_text_only: bool = True
    platform_id: str | None = None
    community_id: str | None = None


class PlatformFetchSummariesWorkflowInput(BaseModel):
    platform_id: str
    community_id: str
    start_date: str | None = None
    end_date: str | None = None
    extract_text_only: bool = True


class RealTimeSummaryWorkflowInput(BaseModel):
    period: str | None = (
        None  # could be in format of hour (1h, 4h, ...) or day %Y-%m-%d
    )
    extract_text_only: bool = True
    platform_id: str | None = None
    community_id: str | None = None
    collection_name: str | None = None
