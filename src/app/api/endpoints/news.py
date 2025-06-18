from fastapi import APIRouter
from app.schemas.news import NewsCard
from repositories.databases.remote.analysis import grouped_docs_with_anal
from repositories.databases.remote.schema import S3PDocumentCard

router = APIRouter()

@router.get('/', response_model=list[S3PDocumentCard])
async def get_news(limit: int):
    docs = grouped_docs_with_anal(limit)
    return docs

@router.get('/{id}', response_model=NewsCard)
async def get_one_piece_of_news(id: int):
    raise NotImplementedError()
