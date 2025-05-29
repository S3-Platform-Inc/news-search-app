import dataclasses
from datetime import datetime

from s3p_sdk.types import S3PDocument, S3PRefer


@dataclasses.dataclass
class KeywordDict:
    id: str
    elements: dict[str, int]


@dataclasses.dataclass
class S3PDocumentCard:
    document: S3PDocument
    refer: S3PRefer
    keywords: list[KeywordDict]
    anal_time: datetime
    ...
