"""
Tests for CloudSage AWS Integrations and Operational Tools.
Uses unittest.mock to mock boto3 clients for deterministic local execution.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from botocore.exceptions import ClientError, NoCredentialsError
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# ==============================================================================
# 1. AWS Connection & STS Status Tests
# ==============================================================================

def test_aws_status_connected():
    """Verify /api/aws/status when credentials are valid."""
    mock_sts = MagicMock()
    mock_sts.get_caller_identity.return_value = {
        "Account": "123456789012",
        "Arn": "arn:aws:iam::123456789012:user/cloudsage-admin",
        "UserId": "AIDAEXAMPLEUSERID"
    }

    mock_session = MagicMock()
    mock_session.region_name = "us-east-1"
    mock_session.client.return_value = mock_sts

    with patch("app.services.aws_session.get_aws_session", return_value=mock_session):
        response = client.get("/api/aws/status")
        assert response.status_code == 200
        data = response.json()
        assert data["connected"] is True
        assert data["account_id"] == "123456789012"
        assert data["region"] == "us-east-1"
        assert "successful" in data["message"].lower()


def test_aws_status_missing_credentials():
    """Verify /api/aws/status when credentials are not configured."""
    mock_sts = MagicMock()
    mock_sts.get_caller_identity.side_effect = NoCredentialsError()

    mock_session = MagicMock()
    mock_session.region_name = "us-east-1"
    mock_session.client.return_value = mock_sts

    with patch("app.services.aws_session.get_aws_session", return_value=mock_session):
        response = client.get("/api/aws/status")
        assert response.status_code == 200
        data = response.json()
        assert data["connected"] is False
        assert data["error_type"] == "NoCredentialsError"
        assert "not configured" in data["message"]


def test_aws_status_client_error():
    """Verify /api/aws/status when AWS STS returns an authentication error."""
    mock_sts = MagicMock()
    mock_sts.get_caller_identity.side_effect = ClientError(
        {"Error": {"Code": "InvalidClientTokenId", "Message": "The security token included in the request is invalid."}},
        "GetCallerIdentity"
    )

    mock_session = MagicMock()
    mock_session.region_name = "us-east-1"
    mock_session.client.return_value = mock_sts

    with patch("app.services.aws_session.get_aws_session", return_value=mock_session):
        response = client.get("/api/aws/status")
        assert response.status_code == 200
        data = response.json()
        assert data["connected"] is False
        assert data["error_type"] == "InvalidClientTokenId"


# ==============================================================================
# 2. EC2 Inspector Tests
# ==============================================================================

def test_ec2_instances_success():
    """Verify /api/aws/ec2/instances parses instance attributes correctly."""
    mock_ec2 = MagicMock()
    mock_paginator = MagicMock()
    mock_paginator.paginate.return_value = [
        {
            "Reservations": [
                {
                    "Instances": [
                        {
                            "InstanceId": "i-0123456789abcdef0",
                            "InstanceType": "t3.micro",
                            "State": {"Name": "running"},
                            "Placement": {"AvailabilityZone": "us-east-1a"},
                            "PrivateIpAddress": "172.31.16.50",
                            "PublicIpAddress": "54.210.10.20",
                            "LaunchTime": datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
                            "Tags": [
                                {"Key": "Environment", "Value": "Production"},
                                {"Key": "Name", "Value": "web-prod-01"}
                            ]
                        },
                        {
                            "InstanceId": "i-0abcdef0123456789",
                            "InstanceType": "m5.large",
                            "State": {"Name": "stopped"},
                            "Placement": {"AvailabilityZone": "us-east-1b"},
                            "PrivateIpAddress": "172.31.20.10",
                            "PublicIpAddress": None,
                            "LaunchTime": datetime(2026, 2, 1, 8, 30, 0, tzinfo=timezone.utc),
                            "Tags": []
                        }
                    ]
                }
            ]
        }
    ]
    mock_ec2.get_paginator.return_value = mock_paginator

    mock_session = MagicMock()
    mock_session.region_name = "us-east-1"
    mock_session.client.return_value = mock_ec2

    with patch("app.services.aws_session.get_aws_session", return_value=mock_session):
        response = client.get("/api/aws/ec2/instances")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["count"] == 2
        assert len(data["instances"]) == 2

        first = data["instances"][0]
        assert first["instance_id"] == "i-0123456789abcdef0"
        assert first["name"] == "web-prod-01"
        assert first["instance_type"] == "t3.micro"
        assert first["state"] == "running"
        assert first["public_ip"] == "54.210.10.20"

        second = data["instances"][1]
        assert second["name"] is None
        assert second["state"] == "stopped"


def test_ec2_instances_empty():
    """Verify /api/aws/ec2/instances with zero instances."""
    mock_ec2 = MagicMock()
    mock_paginator = MagicMock()
    mock_paginator.paginate.return_value = [{"Reservations": []}]
    mock_ec2.get_paginator.return_value = mock_paginator

    mock_session = MagicMock()
    mock_session.region_name = "us-east-1"
    mock_session.client.return_value = mock_ec2

    with patch("app.services.aws_session.get_aws_session", return_value=mock_session):
        response = client.get("/api/aws/ec2/instances")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["count"] == 0
        assert data["instances"] == []


# ==============================================================================
# 3. S3 Explorer Tests
# ==============================================================================

def test_s3_buckets_success():
    """Verify /api/aws/s3/buckets parses buckets and creation dates."""
    mock_s3 = MagicMock()
    mock_s3.list_buckets.return_value = {
        "Buckets": [
            {
                "Name": "cloudsage-data-lake-prod",
                "CreationDate": datetime(2026, 1, 10, 12, 0, 0, tzinfo=timezone.utc)
            },
            {
                "Name": "cloudsage-app-backups",
                "CreationDate": datetime(2026, 3, 5, 15, 30, 0, tzinfo=timezone.utc)
            }
        ]
    }

    mock_session = MagicMock()
    mock_session.client.return_value = mock_s3

    with patch("app.services.aws_session.get_aws_session", return_value=mock_session):
        response = client.get("/api/aws/s3/buckets")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["count"] == 2
        assert data["buckets"][0]["name"] == "cloudsage-data-lake-prod"
        assert "2026-01-10" in data["buckets"][0]["creation_date"]


def test_s3_buckets_error():
    """Verify /api/aws/s3/buckets graceful error handling."""
    mock_s3 = MagicMock()
    mock_s3.list_buckets.side_effect = ClientError(
        {"Error": {"Code": "AccessDenied", "Message": "Access Denied"}},
        "ListBuckets"
    )

    mock_session = MagicMock()
    mock_session.client.return_value = mock_s3

    with patch("app.services.aws_session.get_aws_session", return_value=mock_session):
        response = client.get("/api/aws/s3/buckets")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["count"] == 0
        assert "AccessDenied" in data["error"]


# ==============================================================================
# 4. CloudWatch Telemetry Tests
# ==============================================================================

def test_cloudwatch_cpu_metrics_success():
    """Verify /api/aws/cloudwatch/ec2/{id}/cpu returns formatted metrics."""
    mock_cw = MagicMock()
    mock_cw.get_metric_statistics.return_value = {
        "Datapoints": [
            {
                "Timestamp": datetime(2026, 8, 14, 6, 30, 0, tzinfo=timezone.utc),
                "Average": 12.5,
                "Maximum": 25.0,
                "Minimum": 5.0,
                "Unit": "Percent"
            },
            {
                "Timestamp": datetime(2026, 8, 14, 7, 0, 0, tzinfo=timezone.utc),
                "Average": 18.2,
                "Maximum": 32.0,
                "Minimum": 8.0,
                "Unit": "Percent"
            }
        ]
    }

    mock_session = MagicMock()
    mock_session.region_name = "us-east-1"
    mock_session.client.return_value = mock_cw

    with patch("app.services.aws_session.get_aws_session", return_value=mock_session):
        response = client.get("/api/aws/cloudwatch/ec2/i-0123456789abcdef0/cpu?hours=2")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["instance_id"] == "i-0123456789abcdef0"
        assert data["datapoint_count"] == 2
        assert data["average_cpu"] == 15.35  # (12.5 + 18.2) / 2
        assert data["max_cpu"] == 32.0
        assert data["min_cpu"] == 5.0


def test_cloudwatch_cpu_metrics_empty():
    """Verify /api/aws/cloudwatch/ec2/{id}/cpu handles instance with no points."""
    mock_cw = MagicMock()
    mock_cw.get_metric_statistics.return_value = {"Datapoints": []}

    mock_session = MagicMock()
    mock_session.region_name = "us-east-1"
    mock_session.client.return_value = mock_cw

    with patch("app.services.aws_session.get_aws_session", return_value=mock_session):
        response = client.get("/api/aws/cloudwatch/ec2/i-empty-instance/cpu")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["datapoint_count"] == 0
        assert data["average_cpu"] is None
        assert "No CPU metrics found" in data["message"]


# ==============================================================================
# 5. Cost Explorer Intelligence Tests
# ==============================================================================

def test_cost_summary_success():
    """Verify /api/aws/cost/summary parses service spend and percentages."""
    mock_ce = MagicMock()
    mock_ce.get_cost_and_usage.return_value = {
        "ResultsByTime": [
            {
                "TimePeriod": {"Start": "2026-07-15", "End": "2026-08-14"},
                "Groups": [
                    {
                        "Keys": ["Amazon Elastic Compute Cloud - Compute"],
                        "Metrics": {"UnblendedCost": {"Amount": "145.50", "Unit": "USD"}}
                    },
                    {
                        "Keys": ["Amazon Simple Storage Service"],
                        "Metrics": {"UnblendedCost": {"Amount": "24.50", "Unit": "USD"}}
                    },
                    {
                        "Keys": ["Amazon Relational Database Service"],
                        "Metrics": {"UnblendedCost": {"Amount": "80.00", "Unit": "USD"}}
                    }
                ]
            }
        ]
    }

    mock_session = MagicMock()
    mock_session.client.return_value = mock_ce

    with patch("app.services.aws_session.get_aws_session", return_value=mock_session):
        response = client.get("/api/aws/cost/summary?days=30")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["total_cost"] == 250.0  # 145.50 + 24.50 + 80.00
        assert data["currency"] == "USD"
        assert data["top_service"] == "Amazon Elastic Compute Cloud - Compute"
        assert data["service_count"] == 3
        assert data["services"][0]["percentage"] == 58.2  # 145.5 / 250 * 100


def test_cost_summary_access_denied():
    """Verify /api/aws/cost/summary handles unconfigured or denied Cost Explorer."""
    mock_ce = MagicMock()
    mock_ce.get_cost_and_usage.side_effect = ClientError(
        {"Error": {"Code": "AccessDeniedException", "Message": "You need permissions to perform this action"}},
        "GetCostAndUsage"
    )

    mock_session = MagicMock()
    mock_session.client.return_value = mock_ce

    with patch("app.services.aws_session.get_aws_session", return_value=mock_session):
        response = client.get("/api/aws/cost/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "ce:GetCostAndUsage" in data["error"]


# ==============================================================================
# 6. Security Assurance Test
# ==============================================================================

def test_no_secret_leakage():
    """Verify that no AWS secret access key strings or credentials leak in API outputs."""
    response = client.get("/api/aws/status")
    text = response.text.lower()
    assert "secret_access_key" not in text
    assert "aws_secret" not in text
