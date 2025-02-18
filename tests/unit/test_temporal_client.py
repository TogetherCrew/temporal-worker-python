import unittest
from unittest.mock import AsyncMock, patch

from temporalio.client import Client
from tc_temporal_backend.client import TemporalClient


class TestTemporalClient(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        """Set up test environment before each test"""
        self.default_env = {
            "TEMPORAL_HOST": "test-host",
            "TEMPORAL_API_KEY": "test-api-key",
            "TEMPORAL_PORT": "8080",
        }
        self.env_patcher = patch.dict("os.environ", self.default_env)
        self.env_patcher.start()
        self.client = TemporalClient()

    def tearDown(self):
        """Clean up test environment after each test"""
        self.env_patcher.stop()

    def test_initialization(self):
        """Test class initialization and load_dotenv call"""
        with patch("utils.temporal_client.load_dotenv") as mock_load_dotenv:
            client = TemporalClient()
            mock_load_dotenv.assert_called_once()

    def test_load_credentials_success(self):
        """Test successful loading of credentials"""
        credentials = self.client._load_credentials()

        self.assertIsInstance(credentials, dict)
        self.assertEqual(credentials["host"], "test-host")
        self.assertEqual(credentials["api_key"], "test-api-key")
        self.assertEqual(credentials["port"], "8080")

    def test_load_credentials_missing_host(self):
        """Test handling of missing host"""
        with patch.dict("os.environ", {"TEMPORAL_HOST": ""}):
            with self.assertRaises(ValueError) as context:
                self.client._load_credentials()
            self.assertIn("TEMPORAL_HOST", str(context.exception))

    def test_load_credentials_missing_api_key(self):
        """Test handling of missing API key"""
        with patch.dict(
            "os.environ", {"TEMPORAL_HOST": "", "TEMPORAL_PORT": ""}, clear=True
        ):
            with self.assertRaises(ValueError) as context:
                self.client._load_credentials()
            self.assertNotIn("TEMPORAL_API_KEY", str(context.exception))

    def test_load_credentials_missing_port(self):
        """Test handling of missing port"""
        with patch.dict("os.environ", {"TEMPORAL_PORT": ""}):
            with self.assertRaises(ValueError) as context:
                self.client._load_credentials()
            self.assertIn("TEMPORAL_PORT", str(context.exception))

    def test_load_credentials_empty_env(self):
        """Test behavior with completely empty environment"""
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(ValueError) as context:
                self.client._load_credentials()
            self.assertIn("TEMPORAL_HOST", str(context.exception))

    async def test_get_client_success(self):
        """Test successful client connection"""
        mock_client = AsyncMock(spec=Client)

        with patch(
            "temporalio.client.Client.connect", new_callable=AsyncMock
        ) as mock_connect:
            mock_connect.return_value = mock_client

            result = await self.client.get_client()

            # Verify the connection was attempted with correct parameters
            mock_connect.assert_called_once_with(
                "test-host:8080", api_key="test-api-key"
            )
            self.assertEqual(result, mock_client)

    async def test_get_client_connection_error(self):
        """Test handling of connection errors"""
        with patch(
            "temporalio.client.Client.connect", new_callable=AsyncMock
        ) as mock_connect:
            mock_connect.side_effect = Exception("Connection failed")

            with self.assertRaises(Exception) as context:
                await self.client.get_client()
            self.assertIn("Connection failed", str(context.exception))


if __name__ == "__main__":
    unittest.main()
