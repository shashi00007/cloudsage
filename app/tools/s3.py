"""
S3 Operational Tool for CloudSage.
Provides read-only inventory of S3 buckets and creation metadata.
Does not access or download bucket object contents.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
import boto3
from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError

from app.services import aws_session


def list_s3_buckets(session: Optional[boto3.Session] = None) -> Dict[str, Any]:
    """
    Lists all S3 buckets in the AWS account.
    Returns bucket names and creation dates in a structured format.
    """
    sess = session or aws_session.get_aws_session()

    try:
        s3_client = aws_session.get_aws_client("s3", session=sess)
        response = s3_client.list_buckets()

        buckets: List[Dict[str, Any]] = []
        for b in response.get("Buckets", []):
            creation_date = b.get("CreationDate")
            creation_date_str = (
                creation_date.isoformat()
                if isinstance(creation_date, datetime)
                else str(creation_date) if creation_date else None
            )

            buckets.append({
                "name": b.get("Name"),
                "creation_date": creation_date_str,
            })

        return {
            "success": True,
            "count": len(buckets),
            "buckets": buckets,
            "error": None
        }

    except NoCredentialsError:
        return {
            "success": False,
            "count": 0,
            "buckets": [],
            "error": "AWS credentials are not configured or are invalid"
        }
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "ClientError")
        error_msg = e.response.get("Error", {}).get("Message", str(e))
        return {
            "success": False,
            "count": 0,
            "buckets": [],
            "error": f"AWS S3 API error ({error_code}): {error_msg}"
        }
    except BotoCoreError as e:
        return {
            "success": False,
            "count": 0,
            "buckets": [],
            "error": f"AWS SDK error: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "count": 0,
            "buckets": [],
            "error": f"Unexpected error listing S3 buckets: {str(e)}"
        }
