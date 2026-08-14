"""
FastAPI Route Handlers for AWS Integrations and Telemetry Tools.
Separates route definitions from boto3 operational tool logic.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.services import aws_session
from app.tools import ec2, s3, cloudwatch, cost_explorer

router = APIRouter(tags=["AWS"])


# ==============================================================================
# Pydantic Response Models
# ==============================================================================

class AWSStatusResponse(BaseModel):
    connected: bool
    account_id: Optional[str] = None
    arn: Optional[str] = None
    region: Optional[str] = None
    error_type: Optional[str] = None
    message: str


class EC2InstanceModel(BaseModel):
    instance_id: Optional[str]
    name: Optional[str]
    instance_type: Optional[str]
    state: str
    availability_zone: Optional[str]
    private_ip: Optional[str]
    public_ip: Optional[str]
    launch_time: Optional[str]


class EC2InstancesResponse(BaseModel):
    success: bool
    region: str
    count: int
    instances: List[EC2InstanceModel]
    error: Optional[str] = None


class S3BucketModel(BaseModel):
    name: Optional[str]
    creation_date: Optional[str]


class S3BucketsResponse(BaseModel):
    success: bool
    count: int
    buckets: List[S3BucketModel]
    error: Optional[str] = None


class CloudWatchDatapoint(BaseModel):
    timestamp: str
    average: float
    maximum: float
    minimum: float
    unit: str


class CloudWatchCPUResponse(BaseModel):
    success: bool
    region: str
    instance_id: str
    metric_name: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    period_seconds: Optional[int] = None
    datapoint_count: int
    average_cpu: Optional[float] = None
    max_cpu: Optional[float] = None
    min_cpu: Optional[float] = None
    datapoints: List[CloudWatchDatapoint]
    message: Optional[str] = None
    error: Optional[str] = None


class CostServiceBreakdown(BaseModel):
    service: str
    cost: float
    percentage: float


class CostSummaryResponse(BaseModel):
    success: bool
    start_date: str
    end_date: str
    total_cost: float
    currency: str
    top_service: Optional[str] = None
    service_count: int = 0
    services: List[CostServiceBreakdown]
    error: Optional[str] = None


# ==============================================================================
# Route Endpoints
# ==============================================================================

@router.get("/status", response_model=AWSStatusResponse)
async def get_aws_status() -> AWSStatusResponse:
    """
    Tests communication with AWS using STS get_caller_identity.
    Returns connectivity status, masked/actual account ID, and active region.
    """
    res = aws_session.check_aws_connection()
    return AWSStatusResponse(**res)


@router.get("/ec2/instances", response_model=EC2InstancesResponse)
async def get_ec2_instances() -> EC2InstancesResponse:
    """
    Lists EC2 instances in the configured region with state, IPs, and tags.
    """
    res = ec2.list_ec2_instances()
    return EC2InstancesResponse(**res)


@router.get("/s3/buckets", response_model=S3BucketsResponse)
async def get_s3_buckets() -> S3BucketsResponse:
    """
    Lists S3 buckets in the AWS account with creation dates.
    """
    res = s3.list_s3_buckets()
    return S3BucketsResponse(**res)


@router.get("/cloudwatch/ec2/{instance_id}/cpu", response_model=CloudWatchCPUResponse)
async def get_ec2_cpu(
    instance_id: str,
    hours: int = Query(default=1, ge=1, le=168, description="Time window in hours")
) -> CloudWatchCPUResponse:
    """
    Retrieves CPU utilization telemetry for a specific EC2 instance over the last N hours.
    """
    res = cloudwatch.get_ec2_cpu_utilization(instance_id=instance_id, hours=hours)
    return CloudWatchCPUResponse(**res)


@router.get("/cost/summary", response_model=CostSummaryResponse)
async def get_cost(
    days: int = Query(default=30, ge=1, le=365, description="Lookback window in days")
) -> CostSummaryResponse:
    """
    Retrieves AWS Cost Explorer estimated spend and service breakdown.
    """
    res = cost_explorer.get_cost_summary(days=days)
    return CostSummaryResponse(**res)
