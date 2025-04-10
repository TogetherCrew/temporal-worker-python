from hivemind_etl.activities import (
    extract_website,
    get_hivemind_website_comminities,
    load_website_data,
    say_hello,
    transform_website_data,
)
from workflows import (
    CommunityWebsiteWorkflow,
    SayHello,
    WebsiteIngestionSchedulerWorkflow,
)

WORKFLOWS = [
    CommunityWebsiteWorkflow,
    SayHello,
    WebsiteIngestionSchedulerWorkflow,
]

ACTIVITIES = [
    get_hivemind_website_comminities,
    extract_website,
    transform_website_data,
    load_website_data,
    say_hello,
]
