import logging
from typing import Any

from hivemind_etl.website.activities import (
    get_hivemind_website_comminities,
    extract_website,
    transform_website_data,
    load_website_data,
)
from hivemind_etl.mediawiki.activities import (
    get_hivemind_mediawiki_platforms,
    extract_mediawiki,
    transform_mediawiki_data,
    load_mediawiki_data,
)
from hivemind_etl.simple_ingestion.pipeline import (
    process_document,
)

from temporalio import activity


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@activity.defn
async def say_hello():
    return 7
