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
from workflows import (
    CommunityWebsiteWorkflow,
    SayHello,
    WebsiteIngestionSchedulerWorkflow,
    MediaWikiETLWorkflow,
)

WORKFLOWS = [
    CommunityWebsiteWorkflow,
    SayHello,
    WebsiteIngestionSchedulerWorkflow,
    MediaWikiETLWorkflow,
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
]
