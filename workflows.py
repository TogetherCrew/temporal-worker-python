import asyncio
import logging
from datetime import timedelta

from hivemind_etl.activities import say_hello
from hivemind_etl.website.workflows import (
    CommunityWebsiteWorkflow,
    WebsiteIngestionSchedulerWorkflow,
)
from hivemind_etl.mediawiki.workflows import (
    MediaWikiETLWorkflow,
)
from hivemind_etl.simple_ingestion.pipeline import (
    IngestionWorkflow,
)
from hivemind_summarizer.workflows import PlatformSummariesWorkflow

from temporalio import workflow

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
