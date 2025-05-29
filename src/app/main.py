# main.py
from pathlib import Path

from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="News Feed API")
templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))


# Mock database
class NewsItem(BaseModel):
    id: int
    title: str
    content: str
    category: str
    source: str
    seen: bool = False  # New field


# Sample news data
news_db = [
    NewsItem(id=1, title="AI Breakthrough", content="New developments in AI...", category="Technology",
             source="TechCrunch", seen=False),
    NewsItem(id=2, title="Global Warming", content="Climate summit concludes...", category="Science", source="BBC", seen=False),
    NewsItem(id=3, title="Stock Market", content="Markets rally on new data...", category="Finance",
             source="Bloomberg", seen=False),
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
        search: Optional[str] = Query(None)
):
    # Filter logic
    filtered_news = news_db

    if category:
        filtered_news = [n for n in filtered_news if n.category == category]
    if source:
        filtered_news = [n for n in filtered_news if n.source == source]
    if search:
        filtered_news = [n for n in filtered_news if
                         search.lower() in n.title.lower() or search.lower() in n.content.lower()]

    return templates.TemplateResponse("index.html", {
        "request": request,
        "news_items": filtered_news,
        "categories": list(set(n.category for n in news_db)),
        "sources": list(set(n.source for n in news_db))
    })