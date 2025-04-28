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
)
from hivemind_summarizer.activities import (
    fetch_telegram_summaries_by_date,
    fetch_telegram_summaries_by_date_range,
    get_platform_name,
)
from workflows import (
    CommunityWebsiteWorkflow,
    SayHello,
    WebsiteIngestionSchedulerWorkflow,
    MediaWikiETLWorkflow,
    TelegramSummariesWorkflow,
)

WORKFLOWS = [
    CommunityWebsiteWorkflow,
    SayHello,
    WebsiteIngestionSchedulerWorkflow,
    MediaWikiETLWorkflow,
    TelegramSummariesWorkflow,
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
    fetch_telegram_summaries_by_date,
    fetch_telegram_summaries_by_date_range,
    get_platform_name,
]
