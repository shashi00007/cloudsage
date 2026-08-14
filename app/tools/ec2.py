"""
EC2 Operational Tool for CloudSage.
Provides read-only inspection of EC2 instances, states, configurations, and IPs.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
import boto3
from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError

from app.services import aws_session


def list_ec2_instances(session: Optional[boto3.Session] = None) -> Dict[str, Any]:
    """
    Retrieves all EC2 instances in the configured AWS region.
    Extracts instance metadata including ID, state, type, IPs, and Name tag.
    """
    sess = session or aws_session.get_aws_session()
    region = sess.region_name or "us-east-1"

    try:
        ec2_client = aws_session.get_aws_client("ec2", session=sess)
        paginator = ec2_client.get_paginator("describe_instances")
        page_iterator = paginator.paginate()

        instances: List[Dict[str, Any]] = []

        for page in page_iterator:
            for reservation in page.get("Reservations", []):
                for inst in reservation.get("Instances", []):
                    # Extract Name tag if present
                    name_tag: Optional[str] = None
                    for tag in inst.get("Tags", []):
                        if tag.get("Key") == "Name":
                            name_tag = tag.get("Value")
                            break

                    # Format launch time to ISO
                    launch_time = inst.get("LaunchTime")
                    launch_time_str = (
                        launch_time.isoformat()
                        if isinstance(launch_time, datetime)
                        else str(launch_time) if launch_time else None
                    )

                    instances.append({
                        "instance_id": inst.get("InstanceId"),
                        "name": name_tag,
                        "instance_type": inst.get("InstanceType"),
                        "state": inst.get("State", {}).get("Name", "unknown"),
                        "availability_zone": inst.get("Placement", {}).get("AvailabilityZone"),
                        "private_ip": inst.get("PrivateIpAddress"),
                        "public_ip": inst.get("PublicIpAddress"),
                        "launch_time": launch_time_str,
                    })

        return {
            "success": True,
            "region": region,
            "count": len(instances),
            "instances": instances,
            "error": None
        }

    except NoCredentialsError:
        return {
            "success": False,
            "region": region,
            "count": 0,
            "instances": [],
            "error": "AWS credentials are not configured or are invalid"
        }
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "ClientError")
        error_msg = e.response.get("Error", {}).get("Message", str(e))
        return {
            "success": False,
            "region": region,
            "count": 0,
            "instances": [],
            "error": f"AWS EC2 API error ({error_code}): {error_msg}"
        }
    except BotoCoreError as e:
        return {
            "success": False,
            "region": region,
            "count": 0,
            "instances": [],
            "error": f"AWS SDK error: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "region": region,
            "count": 0,
            "instances": [],
            "error": f"Unexpected error listing EC2 instances: {str(e)}"
        }
