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
    ExtractMediaWikiWorkflow,
    TransformMediaWikiWorkflow,
    LoadMediaWikiWorkflow,
)
from hivemind_etl.simple_ingestion.pipeline import (
    VectorIngestionWorkflow,
)
from hivemind_summarizer.summarizer_workflow import PlatformSummariesWorkflow
from hivemind_summarizer.real_time_summary_workflow import RealTimeSummaryWorkflow

from temporalio import workflow

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
