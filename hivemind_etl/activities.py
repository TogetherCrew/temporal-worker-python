import logging
from typing import Any
from temporalio import activity, workflow
from llama_index.core import Document

with workflow.unsafe.imports_passed_through():
    from hivemind_etl.website.module import ModulesWebsite
    from hivemind_etl.website.website_etl import WebsiteETL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@activity.defn
async def get_communities() -> list[dict[str, Any]]:
    """Fetch all communities that need to be processed."""
    try:
        communities = ModulesWebsite().get_learning_platforms()
        logger.info(f"Found {len(communities)} communities to process")
        return communities
    except Exception as e:
        logger.error(f"Error fetching communities: {str(e)}")
        raise


@activity.defn
async def extract_website(urls: list[str], community_id: str) -> list[dict]:
    """Extract data from website URLs."""
    try:
        logger.info(
            f"Starting extraction for community {community_id} with {len(urls)} URLs"
        )
        website_etl = WebsiteETL(community_id=community_id)
        result = await website_etl.extract(urls=urls)
        logger.info(f"Completed extraction for community {community_id}")
        return result
    except Exception as e:
        logger.error(f"Error in extraction for community {community_id}: {str(e)}")
        raise


@activity.defn
async def transform_data(raw_data: list[dict], community_id: str) -> list[Document]:
    """Transform the extracted raw data."""
    try:
        logger.info(f"Starting transformation for community {community_id}")
        website_etl = WebsiteETL(community_id=community_id)
        result = website_etl.transform(raw_data=raw_data)
        logger.info(f"Completed transformation for community {community_id}")
        return result
    except Exception as e:
        logger.error(f"Error in transformation for community {community_id}: {str(e)}")
        raise


@activity.defn
async def load_data(documents: list[Document], community_id: str) -> None:
    """Load the transformed data into the database."""
    try:
        logger.info(f"Starting data load for community {community_id}")
        logger.info(f"Showing 3 documents: {documents[:3]}")
        website_etl = WebsiteETL(community_id=community_id)
        website_etl.load(documents=documents)
        logger.info(f"Completed data load for community {community_id}")
    except Exception as e:
        logger.error(f"Error in data load for community {community_id}: {str(e)}")
        raise


@activity.defn
async def say_hello():
    return 7