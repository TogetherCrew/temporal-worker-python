import logging
from typing import Any
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from .activities import (
        fetch_telegram_summaries_by_date,
        fetch_telegram_summaries_by_date_range,
        get_platform_name,
    )
    from .schema import (
        TelegramSummariesActivityInput,
        TelegramSummariesRangeActivityInput,
        TelegramGetCollectionNameInput,
        TelegramFetchSummariesWorkflowInput,
    )


@workflow.defn
class TelegramSummariesWorkflow:
    """
    A Temporal workflow that fetches Telegram summaries for a specified date.
    """

    @workflow.run
    async def run(
        self, input: TelegramFetchSummariesWorkflowInput
    ) -> list[dict[str, Any]]:
        """
        Run the workflow to fetch Telegram summaries for the specified date.

        Parameters
        ----------
        input : TelegramFetchSummariesWorkflowInput
            Input containing platform_id, community_id, start_date, end_date, extract_text_only and collection_name

        Returns
        -------
        list[dict[str, Any]]
            A list of summary objects for the specified date
        """
        logging.info("Started TelegramSummariesWorkflow!")
        logging.info(
            (
                f" Platform ID: {input.platform_id}. "
                f" Community ID: {input.community_id}. "
                f" Start Date: {input.start_date}. "
                f" End Date: {input.end_date}"
            )
        )

        logging.info("Getting collection name!")
        # First, get the collection name
        platform_name = await workflow.execute_activity(
            get_platform_name,
            TelegramGetCollectionNameInput(
                platform_id=input.platform_id, community_id=input.community_id
            ),
            schedule_to_close_timeout=timedelta(minutes=1),
            retry_policy=RetryPolicy(maximum_attempts=3),
        )

        # if end_date is not provided, the workflow will fetch summaries just for the start_date
        if input.end_date is None:
            logging.info("Getting summaries by date!")
            summaries = await workflow.execute_activity(
                fetch_telegram_summaries_by_date,
                TelegramSummariesActivityInput(
                    date=input.start_date,
                    platform_name=platform_name,
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
                fetch_telegram_summaries_by_date_range,
                TelegramSummariesRangeActivityInput(
                    start_date=input.start_date,
                    end_date=input.end_date,
                    platform_name=platform_name,
                    community_id=input.community_id,
                    extract_text_only=input.extract_text_only,
                ),
                schedule_to_close_timeout=timedelta(minutes=2),
                retry_policy=RetryPolicy(maximum_attempts=3),
            )
            return summaries
