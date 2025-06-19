import json

from s3p_sdk.types import S3PDocument, S3PRefer

from app.schemas.keywords import KeywordsFilter
from src.repositories.databases.base import ps_connection, load_database_settings
from src.repositories.databases.remote.schema import S3PDocumentCard, KeywordDict


def grouped_docs_with_anal(filter: KeywordsFilter) -> list[S3PDocumentCard]:
    with ps_connection(load_database_settings()) as connection:
        with connection.cursor() as cursor:
            query = """
                    SELECT doc_id,
                           doc_title,
                           doc_link,
                           doc_published,
                           doc_abstract,
                           src_id,
                           src_name,
                           analysis_time,
                           grouped_keywords
                    FROM ml.material_analytics
                    WHERE 1 = %(is_filter)s
                      -- Фильтрация по нескольким источникам
                      AND (%(src_names)s IS NULL OR src_name = ANY (%(src_names)s::text[]))

                      -- Фильтрация по диапазону дат публикации
                      AND (%(date_from)s IS NULL OR doc_published >= %(date_from)s::timestamp)
                      AND (%(date_to)s IS NULL OR doc_published <= %(date_to)s::timestamp)

                      -- Фильтрация по количеству слов в конкретном списке ключевых слов
                      AND (%(kws)s IS NULL OR
                           (SELECT bool_and(
                                           CASE
                                               WHEN grouped_keywords::jsonb ? filter_key
                        THEN (SELECT count(*) FROM jsonb_object_keys(grouped_keywords::jsonb->filter_key)) >= \
                             filter_value::int
                        ELSE false
                      END
                                   )
                            FROM jsonb_each_text(%(kws)s::jsonb) AS t(filter_key, filter_value)))

                      -- Фильтрация по общему количеству слов во всех списках
                      AND (%(word_count)s IS NULL OR
                           (SELECT sum(cnt)
                            FROM (SELECT count(*) AS cnt \
                                  FROM jsonb_each(grouped_keywords::jsonb) \
                                           CROSS JOIN LATERAL jsonb_object_keys(value) \
                                  GROUP BY key) t) >= %(word_count)s::int)

                    ORDER BY doc_published DESC
                        LIMIT %(limit)s \
                    OFFSET %(offset)s; \

                    """
            params = {
                "is_filter": 1 if filter.has() else 0,
                "src_names": filter.sources,
                "date_from": filter.dates[0] if filter.dates and filter.dates[0] else None,
                "date_to": filter.dates[1] if filter.dates and filter.dates[1] else None,
                "kws": json.dumps(filter.kws) if filter.kws else None,
                "word_count": filter.total_words,
                "limit": filter.limit if filter.limit else 100,
                "offset": filter.offset if filter.offset else 2,
            }
            cursor.execute(query, params)
            output = cursor.fetchall()
            if output:
                out = []

                for row in output:
                    out.append(S3PDocumentCard(
                        S3PDocument(id=row[0], title=row[1], link=row[2], published=row[3], abstract=row[4], text=None, storage=None, other=None, loaded=None),
                        S3PRefer(id=row[5], name=row[6], type=None, loaded=None),
                        [
                            KeywordDict(key, elements)
                            for key, elements in dict(row[8]).items()
                        ],
                        row[7],
                    ))

                return out
            return []
