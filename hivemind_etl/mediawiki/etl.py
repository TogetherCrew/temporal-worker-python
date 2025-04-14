import logging
import os
import shutil

from llama_index.core import Document
from tc_hivemind_backend.ingest_qdrant import CustomIngestionPipeline
from hivemind_etl.mediawiki.transform_xml import parse_mediawiki_xml
from hivemind_etl.mediawiki.wikiteam_crawler import WikiteamCrawler


class MediawikiETL:
    def __init__(
        self,
        community_id: str,
        namespaces: list[int],
        delete_dump_after_load: bool = True,
    ) -> None:
        self.community_id = community_id

        self.proxy_url = os.getenv("MEDIAWIKI_PROXY_URL", "")
        if self.proxy_url:
            logging.info(f"Proxy is set to be used!")

        self.wikiteam_crawler = WikiteamCrawler(
            community_id, namespaces=namespaces, proxy_url=self.proxy_url
        )

        self.dump_dir = f"dump_{self.community_id}"
        self.delete_dump_after_load = delete_dump_after_load

    def extract(self, api_url: str, dump_dir: str | None = None) -> None:
        if dump_dir is None:
            dump_dir = self.dump_dir
        else:
            self.dump_dir = dump_dir

        self.wikiteam_crawler.crawl(api_url, dump_dir)

    def transform(self) -> list[Document]:
        pages = parse_mediawiki_xml(file_dir=self.dump_dir)

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
            shutil.rmtree(self.dump_dir)
