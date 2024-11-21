import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

from temporalio import activity, workflow
from hivemind_etl.website.module import ModulesWebsite
from hivemind_etl.website.website_etl import WebsiteETL

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Activities
@activity.defn
async def get_communities() -> List[Dict[str, Any]]:
    """Fetch all communities that need to be processed."""
    try:
        communities = ModulesWebsite().get_learning_platforms()
        logger.info(f"Found {len(communities)} communities to process")
        return communities
    except Exception as e:
        logger.error(f"Error fetching communities: {str(e)}")
        raise


@activity.defn
async def extract_website(urls: List[str], community_id: str) -> List[Dict]:
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
async def transform_data(raw_data: List[Dict], community_id: str) -> List[Dict]:
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
async def load_data(documents: List[Dict], community_id: str) -> None:
    """Load the transformed data into the database."""
    try:
        logger.info(f"Starting data load for community {community_id}")
        website_etl = WebsiteETL(community_id=community_id)
        website_etl.load(documents=documents)
        logger.info(f"Completed data load for community {community_id}")
    except Exception as e:
        logger.error(f"Error in data load for community {community_id}: {str(e)}")
        raise


# Individual community workflow
@workflow.defn
class CommunityWebsiteWorkflow:
    @workflow.run
    async def run(self, community_info: Dict) -> None:
        community_id = community_info["community_id"]
        platform_id = community_info["platform_id"]
        urls = community_info["urls"]

        logger.info(
            f"Starting workflow for community {community_id} | platform {platform_id}"
        )

        # Execute activities in sequence with retries
        raw_data = await workflow.execute_activity(
            extract_website,
            args=[urls, community_id],
            start_to_close_timeout=timedelta(minutes=10),
            retry_policy=workflow.RetryPolicy(
                initial_interval=timedelta(seconds=10),
                maximum_interval=timedelta(minutes=5),
                maximum_attempts=3,
            ),
        )

        documents = await workflow.execute_activity(
            transform_data,
            args=[raw_data, community_id],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=workflow.RetryPolicy(
                initial_interval=timedelta(seconds=5),
                maximum_interval=timedelta(minutes=2),
                maximum_attempts=3,
            ),
        )

        await workflow.execute_activity(
            load_data,
            args=[documents, community_id],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=workflow.RetryPolicy(
                initial_interval=timedelta(seconds=5),
                maximum_interval=timedelta(minutes=2),
                maximum_attempts=3,
            ),
        )


# Main scheduler workflow
@workflow.defn
class WebsiteIngestionSchedulerWorkflow:
    @workflow.run
    async def run(self) -> None:
        # Get all communities
        communities = await workflow.execute_activity(
            get_communities,
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=workflow.RetryPolicy(
                maximum_attempts=3,
            ),
        )

        # Start a child workflow for each community
        child_workflows = []
        for community in communities:
            child_handle = await workflow.start_child_workflow(
                CommunityWebsiteWorkflow.run,
                args=[community],
                id=f"website-ingest-{community['community_id']}-{datetime.utcnow().strftime('%Y%m%d%H%M')}",
                retry_policy=workflow.RetryPolicy(
                    maximum_attempts=3,
                ),
            )
            child_workflows.append(child_handle)

        # Wait for all child workflows to complete
        await asyncio.gather(*[workflow.wait(handle) for handle in child_workflows])
