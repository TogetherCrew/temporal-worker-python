import logging
from typing import Any

from hivemind_etl.website.crawlee_client import CrawleeClient
from llama_index.core import Document
from tc_hivemind_backend.ingest_qdrant import CustomIngestionPipeline


class WebsiteETL:
    def __init__(
        self,
        community_id: str,
    ) -> None:
        """
        Parameters
        -----------
        community_id : str
            the community to save its data
        """
        if not community_id or not isinstance(community_id, str):
            raise ValueError("community_id must be a non-empty string")

        self.community_id = community_id
        collection_name = "website"

        # preparing the ingestion pipeline
        self.ingestion_pipeline = CustomIngestionPipeline(
            self.community_id, collection_name=collection_name
        )

    async def extract(
        self,
        urls: list[str],
    ) -> list[dict[str, Any]]:
        """
        Extract given urls

        Parameters
        -----------
        urls : list[str]
            a list of urls

        Returns
        ---------
        extracted_data : list[dict[str, Any]]
            The crawled data from urls
        """
        if not urls:
            raise ValueError("No URLs provided for crawling")

        extracted_data = []
        for url in urls:
            self.crawlee_client = CrawleeClient()
            logging.info(f"Crawling {url} and its routes!")
            data = await self.crawlee_client.crawl(links=[url])
            logging.info(f"{len(data)} data is extracted for route: {url}")
            extracted_data.extend(data)

        logging.info(f"Extracted {len(extracted_data)} documents!")

        if not extracted_data:
            raise ValueError(f"No data extracted from URLs: {urls}")

        return extracted_data

    def transform(self, raw_data: list[dict[str, Any]]) -> list[Document]:
        """
        transform raw data to llama-index documents

        Parameters
        ------------
        raw_data : list[dict[str, Any]]
            crawled data

        Returns
        ---------
        documents : list[llama_index.Document]
            list of llama-index documents
        """
        documents: list[Document] = []

        for data in raw_data:
            doc_id = data["url"]
            doc = Document(
                doc_id=doc_id,
                text=data["inner_text"],
                metadata={
                    "title": data["title"],
                    "url": data["url"],
                },
            )
            documents.append(doc)

        return documents

    def load(self, documents: list[Document]) -> None:
        """
        load the documents into the vector db

        Parameters
        -------------
        documents: list[llama_index.Document]
            the llama-index documents to be ingested
        """
        # loading data into db
        self.ingestion_pipeline.run_pipeline(docs=documents)
