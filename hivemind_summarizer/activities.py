import json
import logging
from typing import Any
from datetime import datetime, timedelta, timezone

from tc_hivemind_backend.db.qdrant import QdrantSingleton
from tc_hivemind_backend.ingest_qdrant import CustomIngestionPipeline

from temporalio import activity, workflow
from qdrant_client.models import Filter, FieldCondition, MatchValue
from qdrant_client.http import models
from openai import AsyncOpenAI
import re

with workflow.unsafe.imports_passed_through():
    from hivemind_summarizer.schema import (
        PlatformSummariesActivityInput,
        PlatformSummariesRangeActivityInput,
        RealTimeSummaryWorkflowInput,
    )


def extract_summary_text(node_content: dict[str, Any]) -> str:
    """
    Extract the actual summary text from the node_content.

    Parameters
    ----------
    node_content : dict[str, Any]
        The parsed node_content object

    Returns
    -------
    str
        The extracted summary text
    """
    # Based on the example provided, the text is in the "text" field
    if isinstance(node_content, dict) and "text" in node_content:
        return node_content["text"]

    return "Summary text not found"


@activity.defn
async def fetch_platform_summaries_by_date(
    input: PlatformSummariesActivityInput,
) -> list[dict[str, Any]] | str:
    """
    Activity that fetches Platform summaries for a specific date from Qdrant.

    Parameters
    ----------
    input : PlatformSummariesActivityInput
        Input object containing date, collection_name and extract_text_only

    Returns
    -------
    list[dict[str, Any]] | str
        A list of summary objects for the specified date or a string of summaries
    """
    date = input.date
    extract_text_only = input.extract_text_only
    community_id = input.community_id
    collection_name = f"{community_id}_{input.platform_id}_summary"

    logging.info("Started fetch_platform_summaries_by_date!")

    if not input.platform_id:
        raise ValueError("Platform id is required but was not provided")

    logging.info(
        f"Fetching summaries for date: {date} from collection: {collection_name}"
    )

    try:
        # Get Qdrant client
        qdrant_client = QdrantSingleton.get_instance().get_client()

        # Create filter for the specified date
        if date is not None:
            filter_conditions = [
                FieldCondition(key="date", match=MatchValue(value=date))
            ]
            date_filter = Filter(must=filter_conditions)

            # Query Qdrant for all summaries matching the date using the provided collection name
            search_results = qdrant_client.search(
                collection_name=collection_name,
                query_vector=[0] * 1024,
                query_filter=date_filter,
                limit=100,
                with_payload=True,
                with_vectors=False,
            )
        else:
            # pipeline requires a different format for the collection name
            pipeline = CustomIngestionPipeline(
                community_id=community_id,
                collection_name=f"{input.platform_id}_summary",
            )
            # get the latest date from the collection
            latest_date = pipeline.get_latest_document_date(
                field_name="date", field_schema=models.PayloadSchemaType.DATETIME
            )

            filter_conditions = [
                FieldCondition(
                    key="date", match=MatchValue(value=latest_date.strftime("%Y-%m-%d"))
                )
            ]
            date_filter = Filter(must=filter_conditions)
            search_results = qdrant_client.search(
                collection_name=collection_name,
                query_vector=[0] * 1024,
                query_filter=date_filter,
                limit=100,
                with_payload=True,
                with_vectors=False,
            )

        summaries = []
        for point in search_results:
            # Extract the summary data from each point
            summary_data = point.payload

            # If _node_content is a JSON string, parse it
            if "_node_content" in summary_data and isinstance(
                summary_data["_node_content"], str
            ):
                try:
                    node_content = json.loads(summary_data["_node_content"])
                    if extract_text_only:
                        summary_data = extract_summary_text(node_content)
                    else:
                        summary_data["parsed_content"] = node_content
                        summary_data["summary_text"] = extract_summary_text(
                            node_content
                        )
                except json.JSONDecodeError:
                    logging.warning(
                        f"Failed to parse _node_content as JSON for point with date {date}"
                    )

            summaries.append(summary_data)

        logging.info(
            f"Found {len(summaries)} summaries for date {date} in collection {collection_name}"
        )
        return "\n".join(summaries) if extract_text_only else summaries

    except Exception as e:
        logging.error(
            f"Error fetching summaries for date {date} from collection {collection_name}: {str(e)}"
        )
        raise


@activity.defn
async def fetch_platform_summaries_by_date_range(
    input: PlatformSummariesRangeActivityInput,
) -> dict[str, list[dict[str, Any] | str]]:
    """
    Activity that fetches summaries for a range of dates from Qdrant.

    Parameters
    ----------
    input : PlatformSummariesRangeActivityInput
        Input object containing start_date, end_date, platform_id and community_id

    Returns
    -------
    dict[str, list[dict[str, Any] | str]]
        A dictionary mapping dates to lists of summary objects or a string of summaries

    Raises
    ------
    ValueError
        If end_date is before start_date or platform_id is not provided
    """
    start_date = input.start_date
    end_date = input.end_date
    extract_text_only = input.extract_text_only
    platform_id = input.platform_id
    community_id = input.community_id
    if not platform_id:
        raise ValueError("Platform name is required but was not provided")

    logging.info(f"Fetching summaries for date range: {start_date} to {end_date}.")

    try:
        # Parse the date strings to datetime objects
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()

        # Validate that end_date is not before start_date
        if end < start:
            raise ValueError("End date cannot be before start date")

        # Calculate all dates in the range
        date_range = []
        current = start
        while current <= end:
            date_range.append(current.strftime("%Y-%m-%d"))
            current += timedelta(days=1)

        # Fetch summaries for each date
        result = {}
        for date in date_range:
            date_input = PlatformSummariesActivityInput(
                date=date,
                extract_text_only=extract_text_only,
                platform_id=input.platform_id,
                community_id=community_id,
            )
            summaries = await fetch_platform_summaries_by_date(date_input)
            result[date] = summaries

        return result

    except Exception as e:
        logging.error(
            f"Error fetching summaries for date range {start_date} to {end_date}: {str(e)}"
        )
        raise


@activity.defn
async def fetch_and_summarize_realtime_data(
    input: RealTimeSummaryWorkflowInput,
) -> str:
    """
    Activity that fetches recent data from Qdrant and generates a real-time summary.

    Parameters
    ----------
    input : RealTimeSummaryWorkflowInput
        Input containing period, collection_name or platform_id/community_id, and extract_text_only

    Returns
    -------
    str
        A summarized text of the recent data
    """
    try:
        # Get Qdrant client
        qdrant_client = QdrantSingleton.get_instance().get_client()

        # Determine collection name
        collection_name = input.collection_name
        if not collection_name and (input.platform_id and input.community_id):
            collection_name = f"{input.community_id}_{input.platform_id}"
        elif not collection_name:
            raise ValueError(
                "Either collection_name or both platform_id and community_id must be provided"
            )

        # Calculate time filter based on period
        now = datetime.now(tz=timezone.utc)
        if input.period:
            if re.match(r"^\d+h$", input.period):
                hours = int(input.period[:-1])
                time_threshold = now - timedelta(hours=hours)
            elif re.match(r"^\d{4}-\d{2}-\d{2}$", input.period):
                time_threshold = datetime.strptime(input.period, "%Y-%m-%d").replace(
                    tzinfo=timezone.utc
                )
            else:
                raise ValueError(
                    "Period must be in format 'Nh' (e.g., '1h', '4h') or 'YYYY-MM-DD'"
                )
        else:
            # Default to last hour if no period specified
            time_threshold = now - timedelta(hours=1)

        # Create filter for the time period
        filter_conditions = [
            FieldCondition(
                key="createdAt", range=models.Range(gt=time_threshold.timestamp())
            )
        ]
        time_filter = Filter(must=filter_conditions)

        # Query Qdrant for recent data
        search_results = qdrant_client.search(
            collection_name=collection_name,
            query_vector=[0]
            * 1024,  # Using zero vector since we only care about the filter
            query_filter=time_filter,
            limit=500,  # hard limit in case the data was a lot
            with_payload=True,
            with_vectors=False,
        )

        if not search_results:
            return "No recent data found for the specified period."

        logging.info(f"found {len(search_results)} raw data points!")

        # Extract text content from the results
        texts = []
        for point in search_results:
            if "_node_content" in point.payload:
                content = point.payload["_node_content"]
                if isinstance(content, str):
                    try:
                        content = json.loads(content)
                    except json.JSONDecodeError:
                        pass
                if isinstance(content, dict) and "text" in content:
                    if "author" in content["metadata"]:
                        texts.append(
                            content["metadata"]["author"] + ": " + content["text"]
                        )
                    else:
                        texts.append(content["text"])

        if not texts:
            return "No text content found in the recent data."

        # Combine all texts
        combined_text = "\n".join(texts)

        logging.info("Starting to summarize...")

        # Initialize OpenAI client
        client = AsyncOpenAI()

        # Generate summary using OpenAI
        prompt = (
            "Please provide a concise summary of the following content, focusing on the key points and main themes:"
            f"{combined_text}"
        )

        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that summarizes content concisely and accurately.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            n=1,
        )

        return response.choices[0].message.content

    except Exception as e:
        logging.error(f"Error in fetch_and_summarize_realtime_data: {str(e)}")
        raise
