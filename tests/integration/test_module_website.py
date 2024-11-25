import unittest
from datetime import datetime

from bson import ObjectId
from hivemind_etl.website.module import ModulesWebsite
from tc_hivemind_backend.db.mongo import MongoSingleton


class TestQueryWebsiteModulesDB(unittest.TestCase):
    def setUp(self):
        client = MongoSingleton.get_instance().get_client()
        client["Core"].drop_collection("modules")
        client["Core"].drop_collection("platforms")
        self.modules_website = ModulesWebsite()

        self.client = client

    def test_get_website_communities_data_empty_data(self):
        result = self.modules_website.get_learning_platforms()
        self.assertEqual(result, [])

    def test_get_website_communities_data_single_modules(self):
        """
        single website platform for one community
        """
        platform_id = ObjectId("6579c364f1120850414e0dc6")
        community_id = ObjectId("6579c364f1120850414e0dc5")

        self.client["Core"]["platforms"].insert_one(
            {
                "_id": platform_id,
                "name": "website",
                "metadata": {"resources": ["link1", "link2"]},
                "community": community_id,
                "disconnectedAt": None,
                "connectedAt": datetime.now(),
                "createdAt": datetime.now(),
                "updatedAt": datetime.now(),
            }
        )

        self.client["Core"]["modules"].insert_one(
            {
                "name": "hivemind",
                "community": community_id,
                "options": {
                    "platforms": [
                        {
                            "platform": platform_id,
                            "name": "website",
                            "metadata": {},
                        }
                    ]
                },
            }
        )

        result = self.modules_website.get_learning_platforms()

        # Assertions
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)

        self.assertEqual(
            result[0],
            {
                "community_id": "6579c364f1120850414e0dc5",
                "platform_id": str(platform_id),
                "urls": ["link1", "link2"],
            },
        )

    def test_get_website_communities_data_module_multiple_platforms(self):
        """
        Test get_learning_platforms when a community has multiple platforms.
        Verifies that only website platform data is returned even when
        other platform types exist.
        """
        platform_id = ObjectId("6579c364f1120850414e0dc6")
        platform_id2 = ObjectId("6579c364f1120850414e0dc7")
        community_id = ObjectId("6579c364f1120850414e0dc5")

        self.client["Core"]["platforms"].insert_one(
            {
                "_id": platform_id,
                "name": "website",
                "metadata": {"resources": ["link1", "link2"]},
                "community": community_id,
                "disconnectedAt": None,
                "connectedAt": datetime.now(),
                "createdAt": datetime.now(),
                "updatedAt": datetime.now(),
            }
        )

        self.client["Core"]["modules"].insert_one(
            {
                "name": "hivemind",
                "community": community_id,
                "options": {
                    "platforms": [
                        {
                            "platform": platform_id,
                            "name": "website",
                            "metadata": {},
                        },
                        {
                            "platform": platform_id2,
                            "name": "discord",
                            "metadata": {},
                        },
                    ]
                },
            }
        )

        result = self.modules_website.get_learning_platforms()

        # Assertions
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)

        self.assertEqual(
            result[0],
            {
                "community_id": "6579c364f1120850414e0dc5",
                "platform_id": str(platform_id),
                "urls": ["link1", "link2"],
            },
        )
