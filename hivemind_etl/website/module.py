import logging

from tc_hivemind_backend.db.modules_base import ModulesBase


class ModulesWebsite(ModulesBase):
    def __init__(self) -> None:
        self.platform_name = "website"
        super().__init__()

    def get_learning_platforms(
        self,
    ) -> list[dict[str, str | list[str]]]:
        """
        Get all the website communities with their page titles.

        Returns
        ---------
        community_orgs : list[dict[str, str | list[str]]] = []
            a list of website data information

            example data output:
            ```
            [{
                "community_id": "6579c364f1120850414e0dc5",
                "platform_id": "6579c364f1120850414e0dc6",
                "urls": ["link1", "link2"],
            }]
            ```
        """
        modules = self.query(platform=self.platform_name, projection={"name": 0})
        communities_data: list[dict[str, str | list[str]]] = []

        for module in modules:
            community = module["community"]

            # each platform of the community
            for platform in module["options"]["platforms"]:
                if platform["name"] != self.platform_name:
                    continue

                platform_id = platform["platform"]

                try:
                    website_links = self.get_platform_metadata(
                        platform_id=platform_id,
                        metadata_name="resources",
                    )

                    communities_data.append(
                        {
                            "community_id": str(community),
                            "platform_id": str(platform_id),
                            "urls": website_links,
                        }
                    )
                except Exception as exp:
                    logging.error(
                        "Exception while fetching website modules "
                        f"for platform: {platform_id} | exception: {exp}"
                    )

        return communities_data
