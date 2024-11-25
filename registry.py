from hivemind_etl.activities import (
    extract_website,
    get_communities,
    load_data,
    say_hello,
    transform_data,
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

ACTIVITIES = [get_communities, extract_website, transform_data, load_data, say_hello]
