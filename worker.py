import logging
import os
import asyncio
from dotenv import load_dotenv

from utils.temporal_client import TemporalClient
from temporalio.worker import Worker

from registry import ACTIVITIES, WORKFLOWS


async def main():
    # Initialize environment
    load_dotenv()
    task_queue = os.getenv("TEMPORAL_TASK_QUEUE")
    if not task_queue:
        raise ValueError("`TEMPORAL_TASK_QUEUE` is not properly set!")

    client = await TemporalClient().get_client()

    worker = Worker(
        client,
        task_queue=task_queue,
        workflows=WORKFLOWS,
        activities=ACTIVITIES,
    )

    logging.info("Starting worker...")
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())