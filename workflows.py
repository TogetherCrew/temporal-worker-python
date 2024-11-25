import asyncio
import logging
from datetime import timedelta
from temporalio.common import RetryPolicy

from temporalio import workflow
from hivemind_etl.activities import (
    get_communities,
    extract_website,
    transform_data,
    load_data,
    say_hello,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Individual community workflow
@workflow.defn
class CommunityWebsiteWorkflow:
    @workflow.run
    async def run(self, community_info: dict) -> None:
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
            retry_policy=RetryPolicy(
                initial_interval=timedelta(seconds=10),
                maximum_interval=timedelta(minutes=5),
                maximum_attempts=1,
            ),
        )

        documents = await workflow.execute_activity(
            transform_data,
            args=[raw_data, community_id],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(
                initial_interval=timedelta(seconds=5),
                maximum_interval=timedelta(minutes=2),
                maximum_attempts=1,
            ),
        )

        await workflow.execute_activity(
            load_data,
            args=[documents, community_id],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(
                initial_interval=timedelta(seconds=5),
                maximum_interval=timedelta(minutes=2),
                maximum_attempts=1,
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
            retry_policy=RetryPolicy(
                maximum_attempts=1,
            ),
        )

        # Start a child workflow for each community
        child_workflows = []
        for community in communities:
            child_handle = await workflow.start_child_workflow(
                CommunityWebsiteWorkflow.run,
                args=[community],
                id=f"website-ingest-{community['community_id']}-{workflow.now().strftime('%Y%m%d%H%M')}",
                retry_policy=RetryPolicy(
                    maximum_attempts=1,
                ),
            )
            child_workflows.append(child_handle)

        # Wait for all child workflows to complete
        await asyncio.gather(*[handle for handle in child_workflows])


# For test purposes
# To be deleted in future
@workflow.defn
class SayHello:
    @workflow.run
    async def run(self) -> int:
        logger.info(f"Hello at time {workflow.now()}!")
        return await workflow.start_activity(
            say_hello, start_to_close_timeout=timedelta(seconds=5)
        )
