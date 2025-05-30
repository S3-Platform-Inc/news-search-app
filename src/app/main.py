from dataclasses import asdict
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime

from src.repositories.databases.remote.analysis import grouped_docs_with_anal
from src.repositories.databases.remote.schema import S3PDocumentCard

app = FastAPI(title="News Feed API")
templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")

keyword_lists = ['НСПК', 'Мошенничество']

seen_news_ids = set()

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


def convert_doc_to_news_item(doc: S3PDocumentCard) -> NewsItem:
    # Build keyword_matches dictionary
    keyword_matches = {
        kd.id: list(kd.elements.keys())  # Extract keywords from elements dict
        for kd in doc.keywords
    }

    # Derive category (example: use source name; adjust as needed)
    category = doc.refer.name or "Uncategorized"

    return NewsItem(
        id=doc.document.id,
        title=doc.document.title,
        abstract=doc.document.abstract or "",
        published_at=doc.document.published,
        category=category,
        source=doc.refer.name or "Unknown",
        link=doc.document.link,
        seen=doc.document.id in seen_news_ids,  # Check against seen set
        keyword_matches=keyword_matches
    )


@app.post("/mark-seen/{news_id}")
async def mark_as_seen(news_id: int):
    seen_news_ids.add(news_id)
    return {"status": "success"}


@app.get("/app/documents")
async def api_documents(limit: int):
    docs = grouped_docs_with_anal(limit)
    # **docs:**
    # output = cursor.fetchall()
    # if output:
    #     out = []
    #
    #     for row in output:
    #         out.append(S3PDocumentCard(
    #             S3PDocument(id=row[0], title=row[1], link=row[2], published=row[3], abstract=row[4], text=None,
    #                         storage=None, other=None, loaded=None),
    #             S3PRefer(id=row[5], name=row[6], type=None, loaded=None),
    #             [
    #                 KeywordDict(key, elements)
    #                 for key, elements in dict(row[8]).items()
    #             ],
    #             row[7],
    #         ))
    #
    #     return out
    # return []
    # То есть возвращает список из элементов DataClass, где каждый док это:
    #     document: S3PDocument
    #     refer: S3PRefer
    #     keywords: list[KeywordDict]
    #     anal_time: datetime

    # Каждый из документов списка преобразует в JSON
    # Например:
    # @dataclass
    # class C:
    #     x: int
    #     y: int
    #
    # c = C(1, 2)
    # assert asdict(c) == {'x': 1, 'y': 2}
    # А что он сделает с объектом S3PDocument?
    # asdict(doc):
    #   {'document': S3PDocument???,
    #    'refer': S3PRefer???,
    #    'keywords': list[KeywordDict],
    #    'anal_time': datetime}
    return [asdict(doc) for doc in docs]

@app.get("/", response_class=HTMLResponse)
async def read_news(
        request: Request,
        category: Optional[str] = Query(None),
        source: Optional[str] = Query(None),
        search: Optional[str] = Query(None),
        seen_filter: Optional[str] = Query(None),  # "seen", "unseen", or None
        sort_by: Optional[str] = Query(None),
):
    # Step 1: Fetch all documents from the database
    docs = grouped_docs_with_anal(limit=100)  # Adjust limit as needed

    # Step 2: Convert all documents to NewsItem objects
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
        "categories": all_categories,
        "sources": all_sources,
        "keyword_categories": keyword_lists,
        "sort_by": sort_by,
        "seen_filter": seen_filter
    })
