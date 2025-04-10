import logging
from typing import Any

from hivemind_etl.website.activities import (
    get_hivemind_website_comminities,
    extract_website,
    transform_website_data,
    load_website_data,
)

from temporalio import activity


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@activity.defn
async def say_hello():
    return 7
