from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock

from dotenv import load_dotenv
from hivemind_etl.website.website_etl import WebsiteETL
from llama_index.core import Document


class TestWebsiteETL(IsolatedAsyncioTestCase):
    def setUp(self):
        """
        Setup for the test cases. Initializes a WebsiteETL instance with mocked dependencies.
        """
        load_dotenv()
        self.community_id = "test_community"
        self.website_etl = WebsiteETL(self.community_id)
        self.website_etl.crawlee_client = AsyncMock()
        self.website_etl.ingestion_pipeline = MagicMock()

    async def test_extract(self):
        """
        Test the extract method.
        """
        urls = ["https://example.com"]
        mocked_data = [
            {
                "url": "https://example.com",
                "inner_text": "Example text",
                "title": "Example",
            }
        ]
        self.website_etl.crawlee_client.crawl.return_value = mocked_data

        extracted_data = await self.website_etl.extract(urls)

        self.assertEqual(extracted_data, mocked_data)
        self.website_etl.crawlee_client.crawl.assert_awaited_once_with(links=urls)

    def test_transform(self):
        """
        Test the transform method.
        """
        raw_data = [
            {
                "url": "https://example.com",
                "inner_text": "Example text",
                "title": "Example",
            }
        ]
        expected_documents = [
            Document(
                doc_id="https://example.com",
                text="Example text",
                metadata={"title": "Example", "url": "https://example.com"},
            )
        ]

        documents = self.website_etl.transform(raw_data)

        self.assertEqual(len(documents), len(expected_documents))
        self.assertEqual(documents[0].doc_id, expected_documents[0].doc_id)
        self.assertEqual(documents[0].text, expected_documents[0].text)
        self.assertEqual(documents[0].metadata, expected_documents[0].metadata)

    def test_load(self):
        """
        Test the load method.
        """
        documents = [
            Document(
                doc_id="https://example.com",
                text="Example text",
                metadata={"title": "Example", "url": "https://example.com"},
            )
        ]

        self.website_etl.load(documents)

        self.website_etl.ingestion_pipeline.run_pipeline.assert_called_once_with(
            docs=documents
        )
