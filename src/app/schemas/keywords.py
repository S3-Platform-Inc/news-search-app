from datetime import datetime

from pydantic import BaseModel

class KeywordBase(BaseModel):
    """Keywords Metadata"""
    id: str
    name: str

class KeywordList(KeywordBase):
    """Keywords"""
    words: list[str]

class KeywordDict(KeywordBase):
    """Found Keywords"""
    elements: dict[str, int]

class KeywordsFilter(BaseModel):
    sources: list[str] | list | None
    dates: tuple[datetime | None, datetime | None]
    kws: dict[str, int] | None = None
    total_words: int | None = None
    limit: int | None = None
    offset: int | None = None

    def has(self) -> bool:
        return bool(self.sources or self.dates or self.kws or self.total_words)
