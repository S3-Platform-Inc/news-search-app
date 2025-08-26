from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Optional

from src.app.api.endpoints.news import get_news
from src.app.core.config import settings
from src.app.schemas.news import NewsBase
from src.app.api.endpoints import news, keywords
from src.repositories.databases.remote.schema import S3PDocumentCard

from datetime import datetime

import pickle

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

    test_run = False
    if test_run:
        test_all_news_items = [NewsBase(id=288,
                                        title='НБКИ: количество новых выданных кредиток за год сократилось на 49,7%',
                                        abstract='Показатель составил 1,11 млн, уточнили в бюро',
                                        published_at=datetime(2025, 8, 25, 6, 32, 25, 988222),
                                        category='tass',
                                        source='tass',
                                        link='https://tass.ru/ekonomika/24862999',
                                        seen=False,
                                        favorite=False,
                                        keyword_matches={'kw_fraud_1': ["Коррупция", "Мошенник"],
                                                         'kw_company_1': ["НСПК"]}),
                               NewsBase(id=261,
                                        title='В одном из камчатских вузов учебный год начнется в смешанном формате',
                                        abstract='Это связано с необходимостью завершения ремонта в здании учебного заведения, пострадавшем от землетрясения',
                                        published_at=datetime(2025, 8, 25, 6, 43, 25, 988222),
                                        category='tass',
                                        source='tass',
                                        link='https://tass.ru/obschestvo/24863209',
                                        seen=False,
                                        favorite=False,
                                        keyword_matches={'kw_fraud_1': [],
                                                         'kw_company_1': ["Система быстрых платежей"]}),
                               NewsBase(id=1,
                                        title='Шесть спортсменов получили травмы во время молодежного велокросса в Чехии',
                                        abstract='Как сообщает агентство CTK, один из спортсменов был доставлен в больницу вертолетом',
                                        published_at=datetime(2025, 8, 24, 6, 32, 25, 988222),
                                        category='tass',
                                        source='tass',
                                        link='https://tass.ru/sport/24860897',
                                        seen=False,
                                        favorite=False,
                                        keyword_matches={'kw_fraud_1': [], 'kw_company_1': []}),
                               NewsBase(id=394,
                                        title='В школы Подмосковья летом привлекли около 2,6 тыс. педагогов',
                                        abstract='С нового учебного года к работе приступят 100 лидеров образования из разных регионов',
                                        published_at=datetime(2025, 8, 25, 6, 32, 25, 988222),
                                        category='tass',
                                        source='tass',
                                        link='https://tass.ru/obschestvo/24868625',
                                        seen=False,
                                        favorite=False,
                                        keyword_matches={'kw_fraud_1': [],
                                                         'kw_company_1': ['Национальная Система Платежных Карт',
                                                                          'СБП']})
                               ]
        all_news_items = test_all_news_items

    # with open('test_all_news_items.pickle', 'rb') as handle:
    #     test_all_news_items = pickle.load(handle)
    #     all_news_items = test_all_news_items

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

    # # [OLD worked] Dynamic keyword-based filters
    # for category_name, min_count in request.query_params.items():
    #     if category_name.endswith("_min"):
    #         keyword_category = category_name.replace("_min", "")
    #         if keyword_category in keyword_lists.keys():
    #             try:
    #                 min_val = int(min_count)
    #                 if min_val > 0:
    #                     filtered_news = [
    #                         n for n in filtered_news
    #                         if len(n.keyword_matches.get(keyword_category, [])) >= min_val
    #                     ]
    #             except ValueError:
    #                 pass  # invalid value, skip

    # NEW works?
    # Determine keyword filter values (with defaults)
    keyword_filters = {}
    for cat in keyword_lists.keys():
        param_name = f"{cat}_min"
        param_value = request.query_params.get(param_name)

        if param_value is not None:
            try:
                keyword_filters[cat] = int(param_value)
            except ValueError:
                keyword_filters[cat] = 1  # Default to 1 for invalid values
        else:
            keyword_filters[cat] = 1  # Default to 1 for initial page load

    # Apply ALL keyword filters (including defaults)
    for cat, min_val in keyword_filters.items():
        if min_val > 0:
            filtered_news = [
                n for n in filtered_news
                if len(n.keyword_matches.get(cat, [])) >= min_val
            ]

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
