import logging
from typing import Any
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from .activities import (
        fetch_platform_summaries_by_date,
        fetch_platform_summaries_by_date_range,
    )
    from .schema import (
        PlatformSummariesActivityInput,
        PlatformSummariesRangeActivityInput,
        PlatformFetchSummariesWorkflowInput,
    )


@workflow.defn
class PlatformSummariesWorkflow:
    """
    A Temporal workflow that fetches summaries for a specified date.
    """

    @workflow.run
    async def run(
        self, input: PlatformFetchSummariesWorkflowInput
    ) -> list[dict[str, Any]]:
        """
        Run the workflow to fetch summaries for the specified date.

        Parameters
        ----------
        input : PlatformFetchSummariesWorkflowInput
            Input containing platform_id, community_id, start_date, end_date, extract_text_only and platform_name

        Returns
        -------
        list[dict[str, Any]]
            A list of summary objects for the specified date
        """
        logging.info("Started PlatformSummariesWorkflow!")
        logging.info(
            (
                f" Platform ID: {input.platform_id}. "
                f" Community ID: {input.community_id}. "
                f" Start Date: {input.start_date}. "
                f" End Date: {input.end_date}"
            )
        )

        # if end_date is not provided, the workflow will fetch summaries just for the start_date
        if input.end_date is None:
            logging.info("Getting summaries by date!")
            summaries = await workflow.execute_activity(
                fetch_platform_summaries_by_date,
                PlatformSummariesActivityInput(
                    date=input.start_date,
                    platform_id=input.platform_id,
                    community_id=input.community_id,
                    extract_text_only=input.extract_text_only,
                ),
                schedule_to_close_timeout=timedelta(minutes=2),
                retry_policy=RetryPolicy(maximum_attempts=3),
            )
            return summaries
        else:
            logging.info("Getting summaries by date range!")
            summaries = await workflow.execute_activity(
                fetch_platform_summaries_by_date_range,
                PlatformSummariesRangeActivityInput(
                    start_date=input.start_date,
                    end_date=input.end_date,
                    platform_id=input.platform_id,
                    community_id=input.community_id,
                    extract_text_only=input.extract_text_only,
                ),
                schedule_to_close_timeout=timedelta(minutes=2),
                retry_policy=RetryPolicy(maximum_attempts=3),
            )
            return summaries
