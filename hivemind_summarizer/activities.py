import json
import logging
from typing import Any
from datetime import datetime, timedelta

from bson import ObjectId
from tc_hivemind_backend.db.qdrant import QdrantSingleton
from tc_hivemind_backend.db.mongo import MongoSingleton

from temporalio import activity, workflow
from qdrant_client.models import Filter, FieldCondition, MatchValue

with workflow.unsafe.imports_passed_through():
    from hivemind_summarizer.schema import (
        TelegramSummariesActivityInput,
        TelegramSummariesRangeActivityInput,
        TelegramGetCollectionNameInput,
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
async def get_collection_name(input: TelegramGetCollectionNameInput) -> str:
    """
    Activity that extracts collection name from MongoDB based on platform_id and community_id.

    Parameters
    ----------
    input: TelegramGetCollectionNameInput
        Input object containing platform_id and community_id

    Returns
    -------
    str
        The collection name in format [communityId]_[platformName]_summary

    Raises
    ------
    Exception
        If platform not found or error occurs during DB access
    """
    platform_id = input.platform_id
    community_id = input.community_id

    logging.info(
        f"Getting collection name for platform_id: {platform_id}, community_id: {community_id}"
    )

    try:
        # Get MongoDB client
        mongo_client = MongoSingleton.get_instance().get_client()

        # Query the platform from Core database
        platform = mongo_client["Core"]["platforms"].find_one(
            {"_id": ObjectId(platform_id)}
        )

        if not platform:
            raise Exception(f"Platform with ID {platform_id} not found")

        # Extract platform name
        platform_name = platform.get("name")
        if not platform_name:
            raise Exception(f"Platform name not found for platform_id {platform_id}")

        # Construct collection name
        collection_name = f"{community_id}_{platform_name}_summary"

        logging.info(f"Generated collection name: {collection_name}")
        return collection_name

    except Exception as e:
        logging.error(f"Error getting collection name: {str(e)}")
        raise


@activity.defn
async def fetch_telegram_summaries_by_date(
    input: TelegramSummariesActivityInput,
) -> list[dict[str, Any]] | str:
    """
    Activity that fetches Telegram summaries for a specific date from Qdrant.

    Parameters
    ----------
    input : TelegramSummariesActivityInput
        Input object containing date, collection_name and extract_text_only

    Returns
    -------
    list[dict[str, Any]] | str
        A list of summary objects for the specified date or a string of summaries
    """
    date = input.date
    extract_text_only = input.extract_text_only
    collection_name = input.collection_name

    logging.info("Started fetch_telegram_summaries_by_date!")
    if not collection_name:
        raise ValueError("Collection name is required but was not provided")

    logging.info(
        f"Fetching summaries for date: {date} from collection: {collection_name}"
    )

    try:
        # Get Qdrant client
        qdrant_client = QdrantSingleton.get_instance().get_client()

        # Create filter for the specified date
        filter_conditions = [FieldCondition(key="date", match=MatchValue(value=date))]

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
async def fetch_telegram_summaries_by_date_range(
    input: TelegramSummariesRangeActivityInput,
) -> dict[str, list[dict[str, Any] | str]]:
    """
    Activity that fetches Telegram summaries for a range of dates from Qdrant.

    Parameters
    ----------
    input : TelegramSummariesRangeActivityInput
        Input object containing start_date, end_date, collection_name and extract_text_only

    Returns
    -------
    dict[str, list[dict[str, Any] | str]]
        A dictionary mapping dates to lists of summary objects or a string of summaries

    Raises
    ------
    ValueError
        If end_date is before start_date or collection_name is not provided
    """
    start_date = input.start_date
    end_date = input.end_date
    extract_text_only = input.extract_text_only
    collection_name = input.collection_name

    if not collection_name:
        raise ValueError("Collection name is required but was not provided")

    logging.info(
        f"Fetching summaries for date range: {start_date} to {end_date} from collection: {collection_name}"
    )

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
            date_input = TelegramSummariesActivityInput(
                date=date,
                extract_text_only=extract_text_only,
                collection_name=collection_name,
            )
            summaries = await fetch_telegram_summaries_by_date(date_input)
            result[date] = summaries

        return result

    except Exception as e:
        logging.error(
            f"Error fetching summaries for date range {start_date} to {end_date} from collection {collection_name}: {str(e)}"
        )
        raise
