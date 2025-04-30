# temporal-worker-python

This repository contains TogetherCrew's Temporal Python workflows for data processing and analysis. It leverages the Temporal workflow engine to orchestrate ETL processes and data summarization tasks.

## Project Components

### Hivemind ETL

- **Website Ingestion**: Extracts, transforms, and loads data from websites defined in the platform configuration.
- **MediaWiki Ingestion**: Processes content from MediaWiki instances, including extraction of pages, revisions, and content.

### Hivemind Summarizer

- **Platform Summaries**: Retrieves and processes summaries from Platform data stored in Qdrant, with options to fetch by date or date range.

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

To fetch summaries for a specific community and date range:

```python
from temporalio.client import Client
from hivemind_summarizer.workflows import PlatformSummariesWorkflow
from hivemind_summarizer.schema import PlatformFetchSummariesWorkflowInput

async def run_okatfirn_workflow():
    client = await Client.connect("localhost:7233")
    
    # Create workflow input
    input_data = PlatformFetchSummariesWorkflowInput(
        platform_id="your_platform_id",
        community_id="your_community_id",
        start_date="2023-05-01",
        end_date="2023-05-07",
        extract_text_only=True
    )
    
    # Execute workflow
    result = await client.execute_workflow(
        PlatformSummariesWorkflow.run,
        input_data,
        id="platform-summaries-workflow",
        task_queue="your_task_queue"
    )
    
    return result
```

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
