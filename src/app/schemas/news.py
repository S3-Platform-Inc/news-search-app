from datetime import datetime

from pydantic import BaseModel
from s3p_sdk.types import S3PDocument, S3PRefer

from app.schemas.keywords import KeywordDict


class NewsBase(BaseModel):
    id: int
    title: str
    abstract: str
    published_at: datetime
    category: str
    source: str
    link: str
    seen: bool = False  # Просмотрено
    favorite: bool = False  # Избранное
    keyword_matches: dict[str, list[str]] = {}  # e.g., {"Politics": ["government", "law"], ...}

class NewsCard(BaseModel):
    document: S3PDocument
    refer: S3PRefer
    keywords: list[KeywordDict]
    anal_time: datetime

class NewsFilter(BaseModel):
    ...
