from temporalio import workflow
from temporalio.common import RetryPolicy
from datetime import timedelta

with workflow.unsafe.imports_passed_through():
    from .activities import fetch_and_summarize_realtime_data
    from .schema import RealTimeSummaryWorkflowInput


@workflow.defn
class RealTimeSummaryWorkflow:
    """
    A Temporal workflow that fetches and summarizes recent data in real-time.
    """

    @workflow.run
    async def run(self, input: RealTimeSummaryWorkflowInput) -> str:
        """
        Run the workflow to fetch and summarize recent data.

        Parameters
        ----------
        input : RealTimeSummaryWorkflowInput
            Input containing period, collection_name or platform_id/community_id, and extract_text_only

        Returns
        -------
        str
            A summarized text of the recent data
        """
        # Execute the activity with retry policy
        summary = await workflow.execute_activity(
            fetch_and_summarize_realtime_data,
            input,
            schedule_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(
                maximum_attempts=3,
                initial_interval=timedelta(seconds=1),
                maximum_interval=timedelta(minutes=1),
                backoff_coefficient=2.0,
            ),
        )

        return summary
