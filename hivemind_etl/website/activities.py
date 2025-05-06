import logging
from typing import Any

from temporalio import activity, workflow

with workflow.unsafe.imports_passed_through():
    from hivemind_etl.website.module import ModulesWebsite
    from hivemind_etl.website.website_etl import WebsiteETL
    from llama_index.core import Document


@activity.defn
async def get_hivemind_website_comminities(
    platform_id: str | None = None,
) -> list[dict[str, Any]]:
    """
    Fetch all communities that need to be processed in case of no platform id given
    Else, just process for one platform

    Parameters
    -----------
    platform_id : str | None
        A platform's community to be fetched
        for default it is as `None` meaning to get all communities information

    Returns
    ---------
    communities : list[dict[str, Any]]
        a list of communities holding website informations
    """
    try:
        if platform_id:
            logging.info("Website ingestion is filtered for a single community!")
        communities = ModulesWebsite().get_learning_platforms(
            filter_platform_id=platform_id
        )
        logging.info(f"Found {len(communities)} communities to process")
        logging.info(f"communities: {communities}")
        return communities
    except Exception as e:
        logging.error(f"Error fetching communities: {str(e)}")
        raise


@activity.defn
async def extract_website(
    urls: list[str], community_id: str, platform_id: str
) -> list[dict]:
    """Extract data from website URLs."""
    try:
        logging.info(
            f"Starting extraction for community {community_id} | platform {platform_id} with {len(urls)} URLs"
        )
        website_etl = WebsiteETL(community_id=community_id, platform_id=platform_id)
        result = await website_etl.extract(urls=urls)
        logging.info(f"Completed extraction for community {community_id}")
        return result
    except Exception as e:
        logging.error(f"Error in extraction for community {community_id}: {str(e)}")
        raise


@activity.defn
async def transform_website_data(
    raw_data: list[dict], community_id: str, platform_id: str
) -> list[Document]:
    """Transform the extracted raw data."""
    try:
        logging.info(
            f"Starting transformation for community {community_id} | platform {platform_id}"
        )
        website_etl = WebsiteETL(community_id=community_id, platform_id=platform_id)
        result = website_etl.transform(raw_data=raw_data)
        logging.info(f"Completed transformation for community {community_id}")
        return result
    except Exception as e:
        logging.error(f"Error in transformation for community {community_id}: {str(e)}")
        raise


@activity.defn
async def load_website_data(
    documents: list[Document], community_id: str, platform_id: str
) -> None:
    """Load the transformed data into the database."""
    try:
        logging.info(
            f"Starting data load for community {community_id} | platform {platform_id}"
        )
        website_etl = WebsiteETL(community_id=community_id, platform_id=platform_id)
        website_etl.load(documents=documents)
        logging.info(f"Completed data load for community {community_id}")
    except Exception as e:
        logging.error(f"Error in data load for community {community_id}: {str(e)}")
        raise
