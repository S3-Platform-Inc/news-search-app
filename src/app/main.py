from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime

app = FastAPI(title="News Feed API")
templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")

keyword_lists = ['НСПК', 'Мошенничество']

class NewsItem(BaseModel):
    id: int
    title: str
    abstract: str
    published_at: datetime
    category: str
    source: str
    link: str
    seen: bool = False  # Просмотрено
    keyword_matches: Dict[str, List[str]] = {}  # e.g., {"Politics": ["government", "law"], ...}


# Sample news data
news_db = [
    NewsItem(id=1, title="AI Breakthrough", abstract="Windows: клиент PuTTY или OpenSSH. Например, в PuTTY нужно выбрать тип ключа (по умолчанию — RSA) и нажать кнопку Generate. Во время генерации рекомендуется двигать курсором по серой области окна, чтобы создать псевдослучайные данные.", category="Technology",
             link='https://example.com/', source="TechCrunch", seen=False, keyword_matches={
                                                                "НСПК": ["law"],
                                                                "Мошенничество": []
                                                            }, published_at=datetime(2025, 4, 3, 21, 00)),
    NewsItem(id=2, title="Global Warming", abstract="Climate summit concludes", category="Science", source="BBC",
             link='https://example.com/', seen=False, keyword_matches={
                                                                "НСПК": ["government"],
                                                                "Мошенничество": ["sport"]
                                                            }, published_at=datetime(2025, 3, 1, 19, 00)),
    NewsItem(id=3, title="Stock Market", abstract="Markets rally on new data", category="Finance",
             link='https://example.com/', source="Bloomberg", seen=False, keyword_matches={
                                                                "НСПК": [],
                                                                "Мошенничество": []
                                                            }, published_at=datetime(2025, 2, 2, 14, 00)),
    NewsItem(id=4, title="ex4", abstract="Example", category="Hello",
             link='https://example.com/', source="Hello", seen=False, keyword_matches={
                                                                "НСПК": [],
                                                                "Мошенничество": ['yes']
                                                            }, published_at=datetime(2025, 1, 1, 10, 00)),
]


@app.post("/mark-seen/{news_id}")
async def mark_as_seen(news_id: int):
    for news in news_db:
        if news.id == news_id:
            news.seen = True
            return {"status": "success"}
    return {"status": "not found"}


@app.get("/", response_class=HTMLResponse)
async def read_news(
        request: Request,
        category: Optional[str] = Query(None),
        source: Optional[str] = Query(None),
        search: Optional[str] = Query(None),
        seen_filter: Optional[str] = Query(None),  # "seen", "unseen", or None
        sort_by: Optional[str] = Query(None),
):
    # Filter logic
    filtered_news = news_db

    if category:
        filtered_news = [n for n in filtered_news if n.category == category]
    if source:
        filtered_news = [n for n in filtered_news if n.source == source]
    if search:
        filtered_news = [n for n in filtered_news if
                         search.lower() in n.title.lower() or search.lower() in n.abstract.lower()]

    # Dynamic keyword-based filters
    for category_name, min_count in request.query_params.items():
        if category_name.endswith("_min"):
            keyword_category = category_name.replace("_min", "")
            if keyword_category in keyword_lists:
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

    # Apply sorting
    if sort_by == "newest":
        filtered_news.sort(key=lambda x: x.published_at, reverse=True)
    elif sort_by == "oldest":
        filtered_news.sort(key=lambda x: x.published_at)

    return templates.TemplateResponse("index.html", {
        "request": request,
        "news_items": filtered_news,
        "categories": list(set(n.category for n in news_db)),
        "sources": list(set(n.source for n in news_db)),
        "keyword_categories": keyword_lists,
        "sort_by": sort_by,
        "seen_filter": seen_filter
    })
