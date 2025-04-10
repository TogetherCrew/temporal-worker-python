from typing import Optional

from pydantic import BaseModel


class Contributor(BaseModel):
    username: Optional[str] = None
    user_id: Optional[str] = None


class Revision(BaseModel):
    revision_id: Optional[str] = None
    parent_revision_id: Optional[str] = None
    timestamp: Optional[str] = None
    comment: str = ""
    contributor: Contributor = Contributor()
    model: Optional[str] = None
    format: Optional[str] = None
    text: str = ""
    sha1: Optional[str] = None


class Page(BaseModel):
    title: Optional[str] = None
    namespace: Optional[str] = None
    page_id: Optional[str] = None
    revision: Optional[Revision] = None


class SiteInfo(BaseModel):
    sitename: Optional[str] = None
    dbname: Optional[str] = None
    base: Optional[str] = None
    generator: Optional[str] = None
