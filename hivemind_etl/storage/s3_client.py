import os
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from llama_index.core import Document
from dotenv import load_dotenv


class S3Client:
    def __init__(self):
        load_dotenv()

        # Get AWS S3 environment variables
        # self.endpoint_url = os.getenv("AWS_ENDPOINT_URL")
        self.access_key = os.getenv("AWS_ACCESS_KEY_ID")
        self.secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.bucket_name = os.getenv("AWS_S3_BUCKET")
        self.region = os.getenv("AWS_REGION")

        # Check each required variable and log if missing
        missing_vars = []
        # if not self.endpoint_url:
        #     missing_vars.append("AWS_ENDPOINT_URL")
        if not self.access_key:
            missing_vars.append("AWS_ACCESS_KEY_ID")
        if not self.secret_key:
            missing_vars.append("AWS_SECRET_ACCESS_KEY")
        if not self.bucket_name:
            missing_vars.append("AWS_S3_BUCKET")
        if not self.region:
            missing_vars.append("AWS_REGION")

        if missing_vars:
            error_msg = (
                f"Missing required environment variables: {', '.join(missing_vars)}"
            )
            logging.error(error_msg)
            raise ValueError(error_msg)

        logging.info(
            f"Initializing S3 client with bucket: {self.bucket_name}, region: {self.region}"
        )

        # a region-agnostic client (no region_name) always works for GetBucketLocation
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            config=Config(signature_version="s3v4"),
        )

        resp = self.s3_client.get_bucket_location(Bucket=self.bucket_name)
        self.bucket_region = resp["LocationConstraint"] or "us-east-1"

        logging.info(f"Bucket region: {self.bucket_region}!")

        self.s3_client = boto3.client(
            "s3",
            region_name=self.bucket_region,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            config=Config(signature_version="s3v4"),
        )

        # Ensure bucket exists
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logging.info(f"Successfully connected to bucket: {self.bucket_name}")
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                logging.info(f"Creating bucket: {self.bucket_name}")
                self.s3_client.create_bucket(
                    Bucket=self.bucket_name,
                    CreateBucketConfiguration={"LocationConstraint": self.region},
                )
                logging.info(f"Successfully created bucket: {self.bucket_name}")
            else:
                logging.error(f"Error accessing bucket {self.bucket_name}: {str(e)}")
                raise

    def _get_key(self, community_id: str, activity_type: str, timestamp: str) -> str:
        """Generate a unique S3 key for the data."""
        return f"{community_id}/{activity_type}/{timestamp}.json"

    def store_extracted_data(self, community_id: str, data: Dict[str, Any]) -> str:
        """Store extracted data in S3."""
        timestamp = datetime.now(tz=timezone.utc).isoformat()
        key = self._get_key(community_id, "extracted", timestamp)

        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=json.dumps(data),
            ContentType="application/json",
        )
        return key

    def store_transformed_data(
        self, community_id: str, documents: List[Document]
    ) -> str:
        """Store transformed documents in S3."""
        timestamp = datetime.now(tz=timezone.utc).isoformat()
        key = self._get_key(community_id, "transformed", timestamp)

        # Convert Documents to dict for JSON serialization
        docs_data = [doc.to_dict() for doc in documents]

        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=json.dumps(docs_data),
            ContentType="application/json",
        )
        return key

    def get_data_by_key(self, key: str) -> Dict[str, Any]:
        """Get data from S3 using a specific key."""
        try:
            obj = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
            return json.loads(obj["Body"].read().decode("utf-8"))
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                logging.error(f"No data found for key: {key}")
                raise ValueError(f"No data found for key: {key}")
            logging.error(f"Error retrieving data for key {key}: {str(e)}")
            raise
