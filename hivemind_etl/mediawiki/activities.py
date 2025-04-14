import logging
from typing import Any

from temporalio import activity, workflow

with workflow.unsafe.imports_passed_through():
    from hivemind_etl.mediawiki.module import ModulesMediaWiki
    from hivemind_etl.mediawiki.etl import MediawikiETL
    from llama_index.core import Document


@activity.defn
async def get_hivemind_mediawiki_platforms(
    platform_id: str | None = None,
) -> list[dict[str, Any]]:
    """
    Fetch all MediaWiki communities that need to be processed in case of no platform id given
    Else, just process for one platform

    Parameters
    -----------
    platform_id : str | None
        A platform's community to be fetched
        for default it is as `None` meaning to get all platforms information

        example data output:
        ```
        [{
            "community_id": "6579c364f1120850414e0dc5",
            "base_url": "some_api_url",
            "namespaces": [1, 2, 3],
        }]
        ```

    Returns
    ---------
    platforms : list[dict[str, Any]]
        a list of platforms holding MediaWiki informations
    """
    try:
        if platform_id:
            logging.info("MediaWiki ingestion is filtered for a single platform!")
        platforms = ModulesMediaWiki().get_learning_platforms(
            platform_id_filter=platform_id
        )
        logging.info(f"Found {len(platforms)} platforms to process")
        logging.info(f"platforms: {platforms}")
        return platforms
    except Exception as e:
        logging.error(f"Error fetching MediaWiki platforms: {str(e)}")
        raise


@activity.defn
async def extract_mediawiki(mediawiki_platform: dict[str, Any]) -> None:
    """Extract data from MediaWiki API URL."""
    try:
        community_id = mediawiki_platform["community_id"]
        api_url = mediawiki_platform["base_url"]
        namespaces = mediawiki_platform["namespaces"]

        logging.info(
            f"Starting extraction for community {community_id} with API URL: {api_url}"
        )
        mediawiki_etl = MediawikiETL(community_id=community_id, namespaces=namespaces)
        mediawiki_etl.extract(api_url=api_url)
        logging.info(f"Completed extraction for community {community_id}")
    except Exception as e:
        community_id = mediawiki_platform["community_id"]
        logging.error(f"Error in extraction for community {community_id}: {str(e)}")
        raise


@activity.defn
async def transform_mediawiki_data(mediawiki_platform: dict[str, Any]) -> list[Document]:
    """Transform the extracted MediaWiki data."""

    community_id = mediawiki_platform["community_id"]
    try:
        namespaces = mediawiki_platform["namespaces"]

        logging.info(f"Starting transformation for community {community_id}")
        mediawiki_etl = MediawikiETL(community_id=community_id, namespaces=namespaces)
        result = mediawiki_etl.transform()
        logging.info(f"Completed transformation for community {community_id}")
        return result
    except Exception as e:
        logging.error(f"Error in transformation for community {community_id}: {str(e)}")
        raise


@activity.defn
async def load_mediawiki_data(mediawiki_platform: dict[str, Any]) -> None:
    """Load the transformed MediaWiki data into the database."""
    community_id = mediawiki_platform["community_id"]
    try:
        documents = mediawiki_platform["documents"]

        logging.info(f"Starting data load for community {community_id}")
        mediawiki_etl = MediawikiETL(community_id=community_id)
        mediawiki_etl.load(documents=documents)
        logging.info(f"Completed data load for community {community_id}")
    except Exception as e:
        logging.error(f"Error in data load for community {community_id}: {str(e)}")
        raise
