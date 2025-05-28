from hivemind_etl.activities import (
    extract_website,
    get_hivemind_website_comminities,
    load_website_data,
    say_hello,
    transform_website_data,
    extract_mediawiki,
    get_hivemind_mediawiki_platforms,
    transform_mediawiki_data,
    load_mediawiki_data,
    process_document,
)
from hivemind_summarizer.activities import (
    fetch_platform_summaries_by_date,
    fetch_platform_summaries_by_date_range,
    fetch_and_summarize_realtime_data,
)
from workflows import (
    CommunityWebsiteWorkflow,
    WebsiteIngestionSchedulerWorkflow,
    MediaWikiETLWorkflow,
    PlatformSummariesWorkflow,
    VectorIngestionWorkflow,
    RealTimeSummaryWorkflow,
)

WORKFLOWS = [
    CommunityWebsiteWorkflow,
    WebsiteIngestionSchedulerWorkflow,
    MediaWikiETLWorkflow,
    PlatformSummariesWorkflow,
    VectorIngestionWorkflow,
    RealTimeSummaryWorkflow,
]

ACTIVITIES = [
    get_hivemind_website_comminities,
    extract_website,
    transform_website_data,
    load_website_data,
    get_hivemind_mediawiki_platforms,
    extract_mediawiki,
    transform_mediawiki_data,
    load_mediawiki_data,
    say_hello,
    fetch_platform_summaries_by_date,
    fetch_platform_summaries_by_date_range,
    process_document,
    fetch_and_summarize_realtime_data,
]
