import logging

from tc_hivemind_backend.db.modules_base import ModulesBase


class ModulesMediaWiki(ModulesBase):
    def __init__(self) -> None:
        self.platform_name = "mediaWiki"
        super().__init__()

    def get_learning_platforms(
        self,
        platform_id_filter: str | None = None,
    ) -> list[dict[str, str | list[str]]]:
        """
        Get all the MediaWiki communities with their page titles.

        Parameters
        -----------
        platform_id_filter : str | None
            the platform id to filter the results for

        Returns
        ---------
        community_orgs : list[dict[str, str | list[str]]] = []
            a list of MediaWiki data information

            example data output:
            ```
            [{
                "platform_id": "xxxx",
                "community_id": "xxxxxx",
                "base_url": "some_api_url",
                "namespaces": [1, 2, 3],
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

                if platform_id_filter is not None and platform_id_filter != str(
                    platform_id
                ):
                    continue

                try:
                    # TODO: retrieve baseURL and path in 1 db call
                    base_url = self.get_platform_metadata(
                        platform_id=platform_id,
                        metadata_name="baseURL",
                    )
                    path = self.get_platform_metadata(
                        platform_id=platform_id,
                        metadata_name="path",
                    )
                    namespaces = self.get_platform_metadata(
                        platform_id=platform_id,
                        metadata_name="namespaces",
                    )

                    if not isinstance(path, str) and not isinstance(base_url, str):
                        raise ValueError("Wrong format for `path` and `base_url`!")

                    modules_options = platform["metadata"]
                    activated = modules_options["activated"]

                    if not activated:
                        logging.warning(
                            f"Platform: {platform_id} is not activated! Skipping it..."
                        )
                        continue

                    if not namespaces:
                        logging.warning(
                            f"No namespaces found for platform: {platform_id}. Skipping it..."
                        )
                        continue

                    communities_data.append(
                        {
                            "platform_id": str(platform_id),
                            "community_id": str(community),
                            "namespaces": namespaces,
                            "base_url": base_url + path,  # type: ignore
                        }
                    )
                except Exception as exp:
                    logging.error(
                        "Exception while fetching mediaWiki modules "
                        f"for platform: {platform_id} | exception: {exp}"
                    )

        return communities_data
