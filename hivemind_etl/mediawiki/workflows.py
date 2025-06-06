import logging
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from hivemind_etl.mediawiki.activities import (
        get_hivemind_mediawiki_platforms,
    )


@workflow.defn
class ExtractMediaWikiWorkflow:
    @workflow.run
    async def run(self, mediawiki_platform: dict) -> None:
        """
        Extract data from MediaWiki and store in S3.

        Parameters
        -----------
        mediawiki_platform : dict
            Dictionary containing platform information
        """
        from hivemind_etl.mediawiki.activities import extract_mediawiki

        await workflow.execute_activity(
            extract_mediawiki,
            mediawiki_platform,
            start_to_close_timeout=timedelta(days=5),
            retry_policy=RetryPolicy(
                initial_interval=timedelta(minutes=1),
                maximum_attempts=3,
            ),
        )


@workflow.defn
class TransformMediaWikiWorkflow:
    @workflow.run
    async def run(self, mediawiki_platform: dict) -> str:
        """
        Transform the extracted data and store in S3.

        Parameters
        -----------
        mediawiki_platform : dict
            Dictionary containing platform information

        Returns
        --------
        str
            The key where transformed data is stored in S3
        """
        from hivemind_etl.mediawiki.activities import transform_mediawiki_data

        return await workflow.execute_activity(
            transform_mediawiki_data,
            mediawiki_platform,
            start_to_close_timeout=timedelta(hours=6),
            retry_policy=RetryPolicy(
                initial_interval=timedelta(minutes=5),
                maximum_attempts=3,
            ),
        )


@workflow.defn
class LoadMediaWikiWorkflow:
    @workflow.run
    async def run(self, mediawiki_platform: dict) -> None:
        """
        Load the transformed data from S3.

        Parameters
        -----------
        mediawiki_platform : dict
            Dictionary containing platform information and transformed data key
        """
        from hivemind_etl.mediawiki.activities import load_mediawiki_data

        await workflow.execute_activity(
            load_mediawiki_data,
            mediawiki_platform,
            start_to_close_timeout=timedelta(days=3),
            retry_policy=RetryPolicy(
                initial_interval=timedelta(minutes=1),
                maximum_attempts=3,
            ),
        )


@workflow.defn
class MediaWikiETLWorkflow:
    @workflow.run
    async def run(self, platform_id: str | None = None) -> None:
        """
        Run the MediaWiki ETL workflow for all communities or a specific one.

        Parameters
        -----------
        platform_id : str | None
            A platform's community to be processed
            for default it is as `None` meaning to process all communities
        """
        try:
            # Get all communities that need to be processed
            platforms = await workflow.execute_activity(
                get_hivemind_mediawiki_platforms,
                platform_id,
                start_to_close_timeout=timedelta(minutes=1),
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(minutes=1),
                    maximum_attempts=3,
                ),
            )

            for platform in platforms:
                try:
                    mediawiki_platform = {
                        "base_url": platform["base_url"],
                        "community_id": platform["community_id"],
                        "namespaces": platform["namespaces"],
                        "platform_id": platform["platform_id"],
                    }

                    # Extract data from MediaWiki and store in S3
                    await workflow.execute_child_workflow(
                        ExtractMediaWikiWorkflow.run,
                        mediawiki_platform,
                        id=f"mediawiki:extract:{platform['community_id']}",
                        execution_timeout=timedelta(days=6),
                    )

                    # Transform the extracted data and store in S3
                    transformed_data_key = await workflow.execute_child_workflow(
                        TransformMediaWikiWorkflow.run,
                        mediawiki_platform,
                        id=f"mediawiki:transform:{platform['community_id']}",
                        execution_timeout=timedelta(hours=6),
                    )

                    mediawiki_platform["transformed_data_key"] = transformed_data_key
                    # Load the transformed data from S3
                    await workflow.execute_child_workflow(
                        LoadMediaWikiWorkflow.run,
                        mediawiki_platform,
                        id=f"mediawiki:load:{platform['community_id']}",
                        execution_timeout=timedelta(days=3),
                    )

                    logging.info(
                        f"Successfully completed ETL for community id: {platform['community_id']}"
                    )
                except Exception as e:
                    logging.error(
                        f"Error processing community id: {platform['community_id']}: {str(e)}"
                    )
                    continue

        except Exception as e:
            logging.error(f"Error in MediaWiki ETL workflow: {str(e)}")
            raise
