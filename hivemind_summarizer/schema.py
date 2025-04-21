from pydantic import BaseModel


class TelegramSummariesActivityInput(BaseModel):
    date: str
    extract_text_only: bool = True
    collection_name: str | None = None


class TelegramSummariesRangeActivityInput(BaseModel):
    start_date: str
    end_date: str
    extract_text_only: bool = True
    collection_name: str | None = None


class TelegramGetCollectionNameInput(BaseModel):
    platform_id: str
    community_id: str


class TelegramFetchSummariesWorkflowInput(BaseModel):
    platform_id: str
    community_id: str
    start_date: str
    end_date: str | None = None
    extract_text_only: bool = True
