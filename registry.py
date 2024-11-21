from workflow import (
    CommunityWebsiteWorkflow,
    WebsiteIngestionSchedulerWorkflow,
    get_communities,
    extract_website,
    transform_data,
    load_data,
)


WORKFLOWS = [CommunityWebsiteWorkflow, WebsiteIngestionSchedulerWorkflow]

ACTIVITIES = [
    get_communities,
    extract_website,
    transform_data,
    load_data,
]
