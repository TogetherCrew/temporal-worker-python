from hivemind_etl.activities import (
    get_communities,
    extract_website,
    transform_data,
    load_data,
    say_hello,
)
from workflows import (
    CommunityWebsiteWorkflow,
    WebsiteIngestionSchedulerWorkflow,
    SayHello,
)


WORKFLOWS = [
    CommunityWebsiteWorkflow,
    WebsiteIngestionSchedulerWorkflow,
    SayHello,
]

ACTIVITIES = [
    get_communities,
    extract_website,
    transform_data,
    load_data,
    say_hello
]
