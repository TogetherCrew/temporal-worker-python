import logging
import asyncio
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

from hivemind_etl.website.activities import (
    extract_website,
    get_hivemind_website_comminities,
    load_website_data,
    transform_website_data,
)


# Individual community workflow
@workflow.defn
class CommunityWebsiteWorkflow:
    @workflow.run
    async def run(self, community_info: dict) -> None:
        community_id = community_info["community_id"]
        platform_id = community_info["platform_id"]
        urls = community_info["urls"]

        logging.info(
            f"Starting workflow for community {community_id} | platform {platform_id}"
        )

        # Execute activities in sequence with retries
        raw_data = await workflow.execute_activity(
            extract_website,
            args=[urls, community_id],
            start_to_close_timeout=timedelta(minutes=30),
            retry_policy=RetryPolicy(
                initial_interval=timedelta(seconds=10),
                maximum_interval=timedelta(minutes=5),
                maximum_attempts=3,
            ),
        )

        documents = await workflow.execute_activity(
            transform_website_data,
            args=[raw_data, community_id],
            start_to_close_timeout=timedelta(minutes=10),
            retry_policy=RetryPolicy(
                initial_interval=timedelta(seconds=5),
                maximum_interval=timedelta(minutes=2),
                maximum_attempts=1,
            ),
        )

        await workflow.execute_activity(
            load_website_data,
            args=[documents, community_id],
            start_to_close_timeout=timedelta(minutes=60),
            retry_policy=RetryPolicy(
                initial_interval=timedelta(seconds=5),
                maximum_interval=timedelta(minutes=2),
                maximum_attempts=3,
            ),
        )


# Main scheduler workflow
@workflow.defn
class WebsiteIngestionSchedulerWorkflow:
    @workflow.run
    async def run(self, platform_id: str | None = None) -> None:
        # Get all communities
        communities = await workflow.execute_activity(
            get_hivemind_website_comminities,
            platform_id,
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(
                maximum_attempts=3,
            ),
        )

        # Start a child workflow for each community
        child_workflows = []
        for community in communities:
            child_handle = await workflow.start_child_workflow(
                CommunityWebsiteWorkflow.run,
                args=[community],
                id=f"website:ingestor:{community['community_id']}",
                retry_policy=RetryPolicy(
                    maximum_attempts=1,
                ),
            )
            child_workflows.append(child_handle)

        # Wait for all child workflows to complete
        await asyncio.gather(*[handle for handle in child_workflows])
