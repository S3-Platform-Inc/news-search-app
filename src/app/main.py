from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Optional

from app.api.endpoints.news import get_news
from app.core.config import settings
from app.schemas.news import NewsBase
from app.api.endpoints import news, keywords
from src.repositories.databases.remote.schema import S3PDocumentCard

app = FastAPI(title=settings.PROJECT_NAME)

# Настройка директории шаблонов
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / 'templates'))

# Mount
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")

# Routers
app.include_router(news.router, prefix=f'{settings.API_V1_STR}/news', tags=["news"])
app.include_router(keywords.router, prefix=f'{settings.API_V1_STR}/keywords', tags=["keywords"])

seen_news_ids = set()
favorite_news_ids = set()

def convert_doc_to_news_item(doc: S3PDocumentCard) -> NewsBase:
    # Build keyword_matches dictionary
    keyword_matches = {
        kd.id: list(kd.elements.keys())  # Extract keywords from elements dict
        for kd in doc.keywords
    }

    # Derive category (example: use source name; adjust as needed)
    category = doc.refer.name or "Uncategorized"

    return NewsBase(
        id=doc.document.id,
        title=doc.document.title,
        abstract=doc.document.abstract or "",
        published_at=doc.document.published,
        category=category,
        source=doc.refer.name or "Unknown",
        link=doc.document.link,
        seen=doc.document.id in seen_news_ids,  # Check against seen set
        favorite=doc.document.id in favorite_news_ids,  # Add favorite status
        keyword_matches=keyword_matches
    )

@app.post("/mark-favorite/{news_id}")
async def mark_as_favorite(news_id: int):
    if news_id in favorite_news_ids:
        favorite_news_ids.remove(news_id)
    else:
        favorite_news_ids.add(news_id)
    return {"status": "success", "favorite": news_id in favorite_news_ids}

@app.post("/mark-seen/{news_id}")
async def mark_as_seen(news_id: int):
    seen_news_ids.add(news_id)
    return {"status": "success"}

@app.get("/", response_class=HTMLResponse)
async def read_news(
        request: Request,
        category: Optional[str] = Query(None),
        source: Optional[str] = Query(None),
        search: Optional[str] = Query(None),
        seen_filter: Optional[str] = Query(None),  # "seen", "unseen", or None
        favorite_filter: Optional[str] = Query(None),
        sort_by: Optional[str] = Query(None),
):
    docs = await get_news(10)
    all_news_items = [convert_doc_to_news_item(doc) for doc in docs]

    # Step 3: Extract all unique categories and sources
    all_categories = list(set(n.category for n in all_news_items))
    all_sources = list(set(n.source for n in all_news_items))

    # Step 4: Apply filters to a separate list for display
    filtered_news = all_news_items.copy()

    if category:
        filtered_news = [n for n in filtered_news if n.category == category]
    if source:
        filtered_news = [n for n in filtered_news if n.source == source]
    if search:
        filtered_news = [n for n in filtered_news if
                         search.lower() in n.title.lower() or search.lower() in n.abstract.lower()]

    keyword_lists = await keywords.get_keywordlist_names()

    # Dynamic keyword-based filters
    for category_name, min_count in request.query_params.items():
        if category_name.endswith("_min"):
            keyword_category = category_name.replace("_min", "")
            if keyword_category in keyword_lists.keys():
                try:
                    min_val = int(min_count)
                    if min_val > 0:
                        filtered_news = [
                            n for n in filtered_news
                            if len(n.keyword_matches.get(keyword_category, [])) >= min_val
                        ]
                except ValueError:
                    pass  # invalid value, skip

    # Apply seen filter
    if seen_filter == "seen":
        filtered_news = [n for n in filtered_news if n.seen]
    elif seen_filter == "unseen":
        filtered_news = [n for n in filtered_news if not n.seen]

    # New favorite filter
    if favorite_filter == "favorited":
        filtered_news = [n for n in filtered_news if n.favorite]
    elif favorite_filter == "not_favorited":
        filtered_news = [n for n in filtered_news if not n.favorite]

    # Apply sorting
    if sort_by == "newest":
        filtered_news.sort(key=lambda x: x.published_at, reverse=True)
    elif sort_by == "oldest":
        filtered_news.sort(key=lambda x: x.published_at)

    return templates.TemplateResponse("index.html", {
        "request": request,
        "news_items": filtered_news,
        "categories": all_categories,
        "sources": all_sources,
        "keyword_categories": keyword_lists.keys(),
        "keyword_categories_dict": keyword_lists,
        "sort_by": sort_by,
        "favorite_filter": favorite_filter,
        "seen_filter": seen_filter
    })
