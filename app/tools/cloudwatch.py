"""
CloudWatch Operational Tool for CloudSage.
Provides metrics retrieval for EC2 and cloud infrastructure telemetry.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
import boto3
from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError

from app.services import aws_session


def get_ec2_cpu_utilization(
    instance_id: str,
    hours: int = 1,
    period_seconds: int = 300,
    session: Optional[boto3.Session] = None
) -> Dict[str, Any]:
    """
    Retrieves CPU utilization metrics for a given EC2 instance over the last N hours.
    Returns chronologically sorted metric datapoints and summary statistics.
    """
    sess = session or aws_session.get_aws_session()
    region = sess.region_name or "us-east-1"

    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(hours=hours)

    try:
        cw_client = aws_session.get_aws_client("cloudwatch", session=sess)
        response = cw_client.get_metric_statistics(
            Namespace="AWS/EC2",
            MetricName="CPUUtilization",
            Dimensions=[
                {"Name": "InstanceId", "Value": instance_id}
            ],
            StartTime=start_time,
            EndTime=end_time,
            Period=period_seconds,
            Statistics=["Average", "Maximum", "Minimum"],
            Unit="Percent"
        )

        raw_datapoints = response.get("Datapoints", [])
        
        # Sort chronologically
        raw_datapoints.sort(key=lambda dp: dp.get("Timestamp", datetime.min.replace(tzinfo=timezone.utc)))

        datapoints: List[Dict[str, Any]] = []
        averages: List[float] = []

        for dp in raw_datapoints:
            ts = dp.get("Timestamp")
            ts_str = ts.isoformat() if isinstance(ts, datetime) else str(ts)
            avg = round(dp.get("Average", 0.0), 2)
            mx = round(dp.get("Maximum", 0.0), 2)
            mn = round(dp.get("Minimum", 0.0), 2)
            averages.append(avg)

            datapoints.append({
                "timestamp": ts_str,
                "average": avg,
                "maximum": mx,
                "minimum": mn,
                "unit": dp.get("Unit", "Percent")
            })

        overall_avg = round(sum(averages) / len(averages), 2) if averages else None
        overall_max = max([dp["maximum"] for dp in datapoints]) if datapoints else None
        overall_min = min([dp["minimum"] for dp in datapoints]) if datapoints else None

        message = (
            f"Successfully retrieved {len(datapoints)} metric datapoints."
            if datapoints
            else "No CPU metrics found for this instance in the specified time window. Ensure the instance is active and reporting CloudWatch metrics."
        )

        return {
            "success": True,
            "region": region,
            "instance_id": instance_id,
            "metric_name": "CPUUtilization",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "period_seconds": period_seconds,
            "datapoint_count": len(datapoints),
            "average_cpu": overall_avg,
            "max_cpu": overall_max,
            "min_cpu": overall_min,
            "datapoints": datapoints,
            "message": message,
            "error": None
        }

    except NoCredentialsError:
        return {
            "success": False,
            "region": region,
            "instance_id": instance_id,
            "metric_name": "CPUUtilization",
            "datapoint_count": 0,
            "datapoints": [],
            "error": "AWS credentials are not configured or are invalid"
        }
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "ClientError")
        error_msg = e.response.get("Error", {}).get("Message", str(e))
        return {
            "success": False,
            "region": region,
            "instance_id": instance_id,
            "metric_name": "CPUUtilization",
            "datapoint_count": 0,
            "datapoints": [],
            "error": f"AWS CloudWatch API error ({error_code}): {error_msg}"
        }
    except BotoCoreError as e:
        return {
            "success": False,
            "region": region,
            "instance_id": instance_id,
            "metric_name": "CPUUtilization",
            "datapoint_count": 0,
            "datapoints": [],
            "error": f"AWS SDK error: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "region": region,
            "instance_id": instance_id,
            "metric_name": "CPUUtilization",
            "datapoint_count": 0,
            "datapoints": [],
            "error": f"Unexpected error retrieving CloudWatch metrics: {str(e)}"
        }
