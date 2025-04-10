import os
import unittest
from unittest.mock import Mock, patch
import shutil

from llama_index.core import Document
from hivemind_etl.mediawiki.etl import MediawikiETL


class TestMediawikiETL(unittest.TestCase):
    def setUp(self):
        self.community_id = "test_community"
        self.api_url = "https://example.com/api.php"
        self.custom_path = "custom/path"
        self.namespaces = [0, 1]  # Main and Talk namespaces

        # Create a temporary dumps directory
        os.makedirs(f"dump_{self.community_id}", exist_ok=True)

    def tearDown(self):
        # Clean up any created files
        if os.path.exists(f"dump_{self.community_id}"):
            shutil.rmtree(f"dump_{self.community_id}")
        if os.path.exists(self.custom_path):
            shutil.rmtree(self.custom_path)

    def test_mediawiki_etl_initialization(self):
        etl = MediawikiETL(community_id=self.community_id, namespaces=self.namespaces)
        self.assertEqual(etl.community_id, self.community_id)
        self.assertTrue(etl.delete_dump_after_load)
        self.assertEqual(etl.dump_dir, f"dump_{self.community_id}")

        etl = MediawikiETL(
            community_id=self.community_id,
            namespaces=self.namespaces,
            delete_dump_after_load=False
        )
        self.assertFalse(etl.delete_dump_after_load)

    def test_extract_with_default_path(self):
        # Create a ETL instance with mocked wikiteam_crawler
        etl = MediawikiETL(community_id=self.community_id, namespaces=self.namespaces)
        etl.wikiteam_crawler = Mock()

        etl.extract(self.api_url)

        etl.wikiteam_crawler.crawl.assert_called_once_with(
            self.api_url, f"dump_{self.community_id}"
        )

    def test_extract_with_custom_path(self):
        # Create a ETL instance with mocked wikiteam_crawler
        etl = MediawikiETL(community_id=self.community_id, namespaces=self.namespaces)
        etl.wikiteam_crawler = Mock()

        etl.extract(self.api_url, self.custom_path)

        self.assertEqual(etl.dump_dir, self.custom_path)
        etl.wikiteam_crawler.crawl.assert_called_once_with(
            self.api_url, self.custom_path
        )

    @patch("hivemind_etl.mediawiki.etl.parse_mediawiki_xml")
    def test_transform_success(self, mock_parse_mediawiki_xml):
        etl = MediawikiETL(community_id=self.community_id, namespaces=self.namespaces)

        # Mock page data
        mock_page = Mock()
        mock_page.page_id = "123"
        mock_page.title = "Test Page"
        mock_page.namespace = 0
        mock_page.revision = Mock(
            text="Test content",
            revision_id="456",
            parent_revision_id="455",
            timestamp="2024-01-01T00:00:00Z",
            comment="Test edit",
            contributor=Mock(username="testuser", user_id="789"),
            sha1="abc123",
            model="wikitext",
        )

        mock_parse_mediawiki_xml.return_value = [mock_page]

        documents = etl.transform()

        self.assertEqual(len(documents), 1)
        doc = documents[0]
        self.assertIsInstance(doc, Document)
        self.assertEqual(doc.doc_id, "123")
        self.assertEqual(doc.text, "Test content")
        self.assertEqual(doc.metadata["title"], "Test Page")
        self.assertEqual(doc.metadata["namespace"], 0)
        self.assertEqual(doc.metadata["revision_id"], "456")
        self.assertEqual(doc.metadata["contributor_username"], "testuser")

    @patch("hivemind_etl.mediawiki.etl.logging")
    @patch("hivemind_etl.mediawiki.etl.parse_mediawiki_xml")
    def test_transform_error_handling(self, mock_parse_mediawiki_xml, mock_logging):
        etl = MediawikiETL(community_id=self.community_id, namespaces=self.namespaces)

        # Mock page that will raise an exception
        mock_page = Mock()
        mock_page.page_id = "123"

        # Set up a side effect that raises an exception when accessing certain attributes
        def get_attribute_error(*args, **kwargs):
            raise Exception("Test error")

        # Configure the mock page to raise an exception
        type(mock_page).revision = property(get_attribute_error)

        mock_parse_mediawiki_xml.return_value = [mock_page]

        documents = etl.transform()

        self.assertEqual(len(documents), 0)
        mock_logging.error.assert_called_once_with(
            "Error transforming page 123: Test error"
        )

    @patch("hivemind_etl.mediawiki.etl.CustomIngestionPipeline")
    def test_load_with_dump_deletion(self, mock_ingestion_pipeline_class):
        etl = MediawikiETL(community_id=self.community_id, namespaces=self.namespaces)
        documents = [Document(text="Test content")]

        # Setup the mock
        mock_pipeline = Mock()
        mock_ingestion_pipeline_class.return_value = mock_pipeline

        # Create a temporary dump directory
        os.makedirs(etl.dump_dir, exist_ok=True)
        with open(os.path.join(etl.dump_dir, "test.xml"), "w") as f:
            f.write("test content")

        etl.load(documents)

        # Verify that methods were called correctly
        mock_ingestion_pipeline_class.assert_called_once_with(
            self.community_id, collection_name="mediawiki"
        )
        mock_pipeline.run_pipeline.assert_called_once_with(documents)
        self.assertFalse(os.path.exists(etl.dump_dir))

    @patch("hivemind_etl.mediawiki.etl.CustomIngestionPipeline")
    def test_load_without_dump_deletion(self, mock_ingestion_pipeline_class):
        etl = MediawikiETL(
            community_id=self.community_id,
            namespaces=self.namespaces,
            delete_dump_after_load=False
        )
        documents = [Document(text="Test content")]

        # Setup the mock
        mock_pipeline = Mock()
        mock_ingestion_pipeline_class.return_value = mock_pipeline

        # Create a temporary dump directory
        os.makedirs(etl.dump_dir, exist_ok=True)
        with open(os.path.join(etl.dump_dir, "test.xml"), "w") as f:
            f.write("test content")

        etl.load(documents)

        # Verify that methods were called correctly
        mock_ingestion_pipeline_class.assert_called_once_with(
            self.community_id, collection_name="mediawiki"
        )
        mock_pipeline.run_pipeline.assert_called_once_with(documents)
        self.assertTrue(os.path.exists(etl.dump_dir))
