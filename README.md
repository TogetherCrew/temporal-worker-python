# temporal-worker-python

This repository contains TogetherCrew's Temporal Python workflows for data processing and analysis. It leverages the Temporal workflow engine to orchestrate ETL processes and data summarization tasks.

## Project Components

### Hivemind ETL

- **Website Ingestion**: Extracts, transforms, and loads data from websites defined in the platform configuration.
- **MediaWiki Ingestion**: Processes content from MediaWiki instances, including extraction of pages, revisions, and content.

### Hivemind Summarizer

- **Platform Summaries**: Retrieves and processes summaries from Platform data stored in Qdrant, with options to fetch by date or date range.
- **Real-Time Summaries**: Generates new summaries for recent data across platforms or specific communities.

## Architecture

The project uses Temporal for workflow orchestration with the following components:

- **Temporal Server**: Manages workflow execution and task queues
- **MongoDB**: Stores platform and community configuration
- **Qdrant**: Vector database for storing and retrieving summary content
- **Redis**: Caching and state management
- **PostgreSQL**: Used by Temporal for workflow history and state

## Setup Instructions

1. Configure Environment Variables
   - Copy the example environment file:

   ```bash
   cp .env.example .env
   ```

   Update the `.env` file with your own values, referencing the services defined in `docker-compose.dev.yml`.

   Required variables:
   - `TEMPORAL_TASK_QUEUE`: Queue name for the worker
   - Database connection parameters for MongoDB, Qdrant, etc.

2. Start Services
   - Use the following command to set up and run the required services:

   ```bash
   docker compose -f docker-compose.dev.yml up -d
   ```

3. Open [localhost:8080](http://localhost:8080/) to access the Temporal dashboard.

## Usage Examples

### Running a Platform Summary Workflow

To fetch existing summaries for a specific community and date range from Qdrant:

```python
from temporalio.client import Client
from hivemind_summarizer.workflows import PlatformSummariesWorkflow
from hivemind_summarizer.schema import PlatformFetchSummariesWorkflowInput

async def run_platform_summaries_workflow():
    client = await Client.connect("localhost:7233")
    
    # Create workflow input
    input_data = PlatformFetchSummariesWorkflowInput(
        platform_id="your_platform_id",  # Required: the platform to fetch summaries from
        community_id="your_community_id",  # Required: the community to fetch summaries from
        start_date="2023-05-01",  # Optional: fetch summaries from this date
        end_date="2023-05-07",    # Optional: fetch summaries until this date
        extract_text_only=True    # Optional: whether to extract only text content
    )
    
    # Execute workflow
    result = await client.execute_workflow(
        PlatformSummariesWorkflow.run,
        input_data,
        id="platform-summaries-workflow",
        task_queue="your_task_queue"
    )
    
    # Returns a list of existing summaries from Qdrant
    return result
```

Note: This workflow only retrieves existing summaries that have already been generated and stored in Qdrant. It does not generate new summaries. Use this when you want to access previously generated summaries for a specific platform and community.

### Running a Real-Time Summary Workflow

To generate new summaries for recent data:

```python
from temporalio.client import Client
from hivemind_summarizer.workflows import RealTimeSummaryWorkflow
from hivemind_summarizer.schema import RealTimeSummaryWorkflowInput

async def run_realtime_summary_workflow():
    client = await Client.connect("localhost:7233")
    
    # Create workflow input
    input_data = RealTimeSummaryWorkflowInput(
        period="4h",  # Optional: time period (e.g., "1h", "4h") or date in %Y-%m-%d format
        platform_id="your_platform_id",  # Optional: filter by platform
        community_id="your_community_id",  # Optional: filter by community
        collection_name="your_collection"  # Optional: filter by collection
    )
    
    # Execute workflow
    result = await client.execute_workflow(
        RealTimeSummaryWorkflow.run,
        input_data,
        id="realtime-summary-workflow",
        task_queue="your_task_queue"
    )
    
    # Returns newly generated summary text
    return result
```

Note: This workflow actively generates new summaries for recent data. Use this when you want to create fresh summaries for the specified time period and filters.
Note 2: Either one of the filter by collection or filter by platform and community should be given. (to identify the collection to access tha raw data)

### Running a MediaWiki ETL Workflow

To process MediaWiki content for all communities or a specific platform:

```python
from temporalio.client import Client
from hivemind_etl.mediawiki.workflows import MediaWikiETLWorkflow

async def run_mediawiki_workflow(platform_id=None):
    client = await Client.connect("localhost:7233")
    
    # Execute workflow for all platforms or a specific one
    await client.execute_workflow(
        MediaWikiETLWorkflow.run,
        platform_id,  # Pass None to process all platforms
        id="mediawiki-etl-workflow",
        task_queue="your_task_queue"
    )
```

### Running a Website Ingestion Workflow

To ingest content from websites:

```python
from temporalio.client import Client
from hivemind_etl.website.workflows import WebsiteIngestionSchedulerWorkflow

async def run_website_workflow(platform_id=None):
    client = await Client.connect("localhost:7233")
    
    # Execute workflow for all communities or a specific one
    await client.execute_workflow(
        WebsiteIngestionSchedulerWorkflow.run,
        platform_id,  # Pass None to process all platforms
        id="website-ingestion-workflow",
        task_queue="your_task_queue"
    )
```

## Development

To run the worker locally:

```bash
python worker.py
```

This will start a worker that connects to Temporal and listens for tasks on the configured task queue.
