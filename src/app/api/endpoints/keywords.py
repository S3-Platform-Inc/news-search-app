from fastapi import APIRouter

from app.schemas.keywords import KeywordList
from app.services.keywords_service import test_keywords

router = APIRouter()

@router.get('/', response_model=list[KeywordList])
async def get_keywords():
    return test_keywords()

@router.get('/names', response_model=dict[str, str])
async def get_keywordlist_names():
    return {kw.id:kw.name for kw in test_keywords()}
