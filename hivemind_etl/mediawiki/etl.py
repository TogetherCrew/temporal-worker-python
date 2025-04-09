import logging
import os

from llama_index.core import Document
from tc_hivemind_backend.ingest_qdrant import CustomIngestionPipeline
from hivemind_etl.mediawiki.transform_xml import parse_mediawiki_xml
from hivemind_etl.mediawiki.wikiteam_crawler import WikiteamCrawler


class MediawikiETL:
    def __init__(self, community_id: str, delete_dump_after_load: bool = True) -> None:
        self.community_id = community_id
        self.wikiteam_crawler = WikiteamCrawler(community_id)

        self.dump_path = f"dumps/{self.community_id}.xml"
        self.delete_dump_after_load = delete_dump_after_load

    def extract(self, api_url: str, dump_path: str | None = None) -> None:
        if dump_path is None:
            dump_path = self.dump_path
        else:
            self.dump_path = dump_path

        self.wikiteam_crawler.crawl(api_url, dump_path)

    def transform(self) -> list[Document]:
        pages = parse_mediawiki_xml(self.dump_path)

        documents: list[Document] = []
        for page in pages:
            try:
                documents.append(
                    Document(
                        doc_id=page.page_id,
                        text=page.revision.text,
                        metadata={
                            "title": page.title,
                            "namespace": page.namespace,
                            "revision_id": page.revision.revision_id,
                            "parent_revision_id": page.revision.parent_revision_id,
                            "timestamp": page.revision.timestamp,
                            "comment": page.revision.comment,
                            "contributor_username": page.revision.contributor.username,
                            "contributor_user_id": page.revision.contributor.user_id,
                            "sha1": page.revision.sha1,
                            "model": page.revision.model,
                        },
                        excluded_embed_metadata_keys=[
                            "namespace",
                            "revision_id",
                            "parent_revision_id",
                            "sha1",
                            "model",
                            "contributor_user_id",
                            "comment",
                            "timestamp",
                        ],
                        excluded_llm_metadata_keys=[
                            "namespace",
                            "revision_id",
                            "parent_revision_id",
                            "sha1",
                            "model",
                            "contributor_user_id",
                        ],
                    )
                )
            except Exception as e:
                logging.error(f"Error transforming page {page.page_id}: {e}")

        return documents

    def load(self, documents: list[Document]) -> None:
        ingestion_pipeline = CustomIngestionPipeline(
            self.community_id, collection_name="mediawiki"
        )
        ingestion_pipeline.run_pipeline(documents)

        if self.delete_dump_after_load:
            os.remove(self.dump_path)
