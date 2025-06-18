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
