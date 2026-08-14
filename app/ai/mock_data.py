"""
Realistic Mock Cloud Telemetry for Safe Local Development.
Used when AWS_MOCK_MODE=True or when real AWS credentials are unavailable.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List


def get_mock_ec2_instances() -> Dict[str, Any]:
    """Returns realistic mock EC2 instance inventory."""
    return {
        "success": True,
        "region": "us-east-1",
        "count": 3,
        "instances": [
            {
                "instance_id": "i-03fa78bc91204d8ef",
                "name": "web-prod-01",
                "instance_type": "t3.medium",
                "state": "running",
                "availability_zone": "us-east-1a",
                "private_ip": "172.31.16.42",
                "public_ip": "54.210.88.19",
                "launch_time": "2026-08-01T08:15:00+00:00"
            },
            {
                "instance_id": "i-09b62a488e1709c31",
                "name": "api-prod-02",
                "instance_type": "t3.large",
                "state": "running",
                "availability_zone": "us-east-1b",
                "private_ip": "172.31.22.105",
                "public_ip": "52.90.14.73",
                "launch_time": "2026-08-05T14:30:00+00:00"
            },
            {
                "instance_id": "i-07e155bc90082a17f",
                "name": "worker-batch-03",
                "instance_type": "c6i.xlarge",
                "state": "stopped",
                "availability_zone": "us-east-1a",
                "private_ip": "172.31.30.12",
                "public_ip": None,
                "launch_time": "2026-07-20T06:00:00+00:00"
            }
        ],
        "error": None
    }


def get_mock_s3_buckets() -> Dict[str, Any]:
    """Returns realistic mock S3 bucket inventory."""
    return {
        "success": True,
        "count": 4,
        "buckets": [
            {
                "name": "cloudsage-prod-data-lake",
                "creation_date": "2026-01-12T10:20:00+00:00"
            },
            {
                "name": "cloudsage-app-backups-us-east-1",
                "creation_date": "2026-02-18T16:45:00+00:00"
            },
            {
                "name": "cloudsage-static-frontend-assets",
                "creation_date": "2026-03-01T09:00:00+00:00"
            },
            {
                "name": "cloudsage-access-logs-archive",
                "creation_date": "2026-04-10T11:15:00+00:00"
            }
        ],
        "error": None
    }


def get_mock_cloudwatch_cpu(instance_id: str = "i-03fa78bc91204d8ef", hours: int = 1) -> Dict[str, Any]:
    """Returns realistic mock CPU utilization telemetry for an EC2 instance."""
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(hours=hours)

    # Generate 12 sample datapoints
    datapoints: List[Dict[str, Any]] = []
    base_cpu = 18.5 if "api" in instance_id.lower() else 24.2
    
    for i in range(12):
        ts = start_time + timedelta(minutes=i * (hours * 60 / 12))
        avg = round(base_cpu + (i * 2.3) % 15.0 - (i % 3) * 4.1, 2)
        mx = round(avg + 18.4, 2)
        mn = round(max(1.2, avg - 8.5), 2)
        
        datapoints.append({
            "timestamp": ts.isoformat(),
            "average": avg,
            "maximum": mx,
            "minimum": mn,
            "unit": "Percent"
        })

    averages = [dp["average"] for dp in datapoints]
    overall_avg = round(sum(averages) / len(averages), 2)
    overall_max = max([dp["maximum"] for dp in datapoints])
    overall_min = min([dp["minimum"] for dp in datapoints])

    return {
        "success": True,
        "region": "us-east-1",
        "instance_id": instance_id,
        "metric_name": "CPUUtilization",
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "period_seconds": int((hours * 3600) / 12),
        "datapoint_count": len(datapoints),
        "average_cpu": overall_avg,
        "max_cpu": overall_max,
        "min_cpu": overall_min,
        "datapoints": datapoints,
        "message": f"Successfully retrieved {len(datapoints)} mock CPU utilization datapoints.",
        "error": None
    }


def get_mock_cost_summary(days: int = 30) -> Dict[str, Any]:
    """Returns realistic mock AWS Cost Explorer spend breakdown."""
    today = datetime.now(timezone.utc).date()
    start_date = today - timedelta(days=days)

    services = [
        {"service": "Amazon Elastic Compute Cloud - Compute", "cost": 245.10, "percentage": 50.8},
        {"service": "Amazon Relational Database Service", "cost": 142.50, "percentage": 29.5},
        {"service": "Amazon Simple Storage Service", "cost": 54.20, "percentage": 11.2},
        {"service": "Amazon CloudWatch", "cost": 40.50, "percentage": 8.5}
    ]
    total_cost = round(sum(s["cost"] for s in services), 2)

    return {
        "success": True,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": today.strftime("%Y-%m-%d"),
        "total_cost": total_cost,
        "currency": "USD",
        "top_service": "Amazon Elastic Compute Cloud - Compute",
        "service_count": len(services),
        "services": services,
        "error": None
    }
