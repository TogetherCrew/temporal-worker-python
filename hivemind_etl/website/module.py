import logging

from tc_hivemind_backend.db.modules_base import ModulesBase


class ModulesWebsite(ModulesBase):
    def __init__(self) -> None:
        super().__init__()
        self.platform_name = "website"

    def get_learning_platforms(
        self,
        filter_platform_id: str | None = None,
    ) -> list[dict[str, str | list[str]]]:
        """
        Get all the website communities with their page titles.

        Parameters
        -----------
        filter_platform_id : str | None
            A platform's community to be fetched
            for default it is as `None` meaning to get all communities information

        Returns
        ---------
        community_orgs : list[dict[str, str | list[str]]] = []
            a list of website data information

            example data output:
            ```
            [{
                "community_id": "xxxx",
                "platform_id": "xxxxxxx",
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

                # if we needed to get specific platforms
                if filter_platform_id and filter_platform_id != str(platform_id):
                    continue

                try:
                    website_links = self.get_platform_metadata(
                        platform_id=platform_id,
                        metadata_name="resources",
                    )
                    if platform["metadata"]["activated"]:
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
