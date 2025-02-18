############ Script for showing how to set up a workflow #########


import asyncio
import os
from datetime import timedelta

from dotenv import load_dotenv
from tc_temporal_backend.client import TemporalClient
from temporalio.client import (
    Schedule,
    ScheduleActionStartWorkflow,
    ScheduleIntervalSpec,
    ScheduleSpec,
    ScheduleState,
)


async def start_workflow():
    """Start a new workflow and demonstrate various interactions."""
    load_dotenv()
    task_queue = os.getenv("TEMPORAL_TASK_QUEUE")

    client = await TemporalClient().get_client()

    try:
        # Start a workflow
        # handle = await client.start_workflow(
        #     "SayHello",  # Workflow name
        #     id=f"workflow-123456",  # Unique workflow ID
        #     task_queue=task_queue,
        #     retry_policy=RetryPolicy(
        #         initial_interval=timedelta(seconds=1),
        #         maximum_interval=timedelta(seconds=10),
        #         maximum_attempts=3
        #     ),
        #     execution_timeout=timedelta(minutes=5)
        # )
        handle = await client.create_schedule(
            id="website-ingestion-schedule",
            schedule=Schedule(
                action=ScheduleActionStartWorkflow(
                    # "SayHello",
                    "WebsiteIngestionSchedulerWorkflow",
                    # id="schedules-say-hello",
                    id="schedules-website-ingestion",
                    task_queue=task_queue,
                    args=["platform_id"],
                ),
                spec=ScheduleSpec(
                    intervals=[ScheduleIntervalSpec(every=timedelta(minutes=2))]
                ),
                state=ScheduleState(note="Here's a note on my Schedule."),
            ),
        )

        print(f"Started workflow {handle.id}")

        # # Wait for the workflow to complete
        # result = await handle.result()
        # print("Workflow result:", result)

        # # Query workflow state
        # state = await handle.query("getCurrentState")
        # print("Current state:", state)

        # # Signal the workflow
        # await handle.signal("signalName", "signal parameter")

        # Terminate workflow if needed
        # await handle.terminate("Termination reason")

    except Exception as e:
        print(f"Error executing workflow: {e}")


async def check_workflow_status(workflow_id: str):
    """Check the status of a specific workflow."""
    client = await TemporalClient().get_client()

    try:
        handle = client.get_workflow_handle(workflow_id)

        # Get workflow details
        desc = await handle.describe()
        print(f"Workflow status: {desc.status}")
        print(f"Start time: {desc.start_time}")
        print(f"Workflow type: {desc.workflow_type}")

        # Check if workflow is running
        workflow_desc = await handle.describe()
        print(f"Description: {workflow_desc.status}")

        return desc

    except Exception as e:
        print(f"Error checking workflow status: {e}")
        raise


async def list_workflows():
    """List all workflows of a specific type."""
    client = await TemporalClient().get_client()

    try:
        workflows = client.list_workflows(
            query="WorkflowType = 'WebsiteIngestionSchedulerWorkflow'",
        )

        async for workflow in workflows:
            print("Workflow ID:", workflow.id)
            print("Status:", workflow.status)
            print("Start Time:", workflow.start_time)
            print("Type:", workflow.workflow_type)
            print("-" * 50)

    except Exception as e:
        print(f"Error listing workflows: {e}")
        raise


async def main():
    """Main function to demonstrate workflow operations."""
    # Start a new workflow
    await start_workflow()

    # Check status of a specific workflow
    # await check_workflow_status("website-ingestion-schedule")

    # List all workflows
    await list_workflows()


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
