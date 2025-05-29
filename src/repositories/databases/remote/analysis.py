from s3p_sdk.types import S3PDocument, S3PRefer

from src.repositories.databases.base import ps_connection, load_database_settings
from src.repositories.databases.remote.schema import S3PDocumentCard, KeywordDict


def grouped_docs_with_anal(limit: int) -> list[S3PDocumentCard]:
    with ps_connection(load_database_settings()) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                with anal as (SELECT document_id,
                                     event_id,
                                     MAX(analysis_time)                      as analysis_time,
                                     JSON_OBJECT_AGG(word_list_id, keywords) as grouped_keywords
                              FROM ml.keyword_analysis
                              GROUP BY document_id, event_id),
                     anal_docs as (select dd.id        as doc_id,
                                          dd.title     as doc_title,
                                          dd.weblink   as doc_link,
                                          dd.published as doc_published,
                                          dd.abstract  as doc_abstract,
                                          s.id         as src_id,
                                          s.name       as src_name,
                                          al.analysis_time,
                                          al.grouped_keywords
                                   from documents.document dd
                                            join anal al on dd.id = al.document_id
                                            join sources.source s on dd.sourceid = s.id)
                select doc_id,
                       doc_title,
                       doc_link,
                       doc_published,
                       doc_abstract,
                       src_id,
                       src_name,
                       analysis_time,
                       grouped_keywords
                from anal_docs LIMIT %s;
                """,
                (limit,)
            )

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

