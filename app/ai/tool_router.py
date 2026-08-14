"""
Tool Router & Tool Definitions for CloudSage AI Agent.
Exposes EC2, S3, CloudWatch, and Cost Explorer as callable tools.
Dispatches requests to real AWS tools or mock data based on configuration.
"""

from typing import Any, Dict, List, Optional
from app.config import get_settings
from app.ai import mock_data
from app.tools import ec2, s3, cloudwatch, cost_explorer

# ==============================================================================
# 1. Tool Definitions / Schemas
# ==============================================================================

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "inspect_ec2",
            "description": "Retrieve active and available EC2 instances, their IDs, instance types, running states, availability zones, private/public IPs, and Name tags.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "explore_s3",
            "description": "List S3 storage buckets in the AWS account along with creation dates.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_cloudwatch_metrics",
            "description": "Retrieve CPU utilization metrics for a specific EC2 instance across a time window (in hours).",
            "parameters": {
                "type": "object",
                "properties": {
                    "instance_id": {
                        "type": "string",
                        "description": "The EC2 instance ID (e.g. i-03fa78bc91204d8ef)"
                    },
                    "hours": {
                        "type": "integer",
                        "description": "Time window in hours for metric lookback (e.g. 1, 6, 24)",
                        "default": 1
                    }
                },
                "required": ["instance_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_cloud_cost",
            "description": "Retrieve estimated AWS cloud spend, currency, date range, and service-by-service cost breakdown using Cost Explorer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Number of lookback days to analyze spend (e.g. 7, 30, 90)",
                        "default": 30
                    }
                },
                "required": []
            }
        }
    }
]


# ==============================================================================
# 2. Tool Router Implementation
# ==============================================================================

class ToolRouter:
    """
    Executes operational tools against AWS or mock datasets.
    """

    def __init__(self, mock_mode: Optional[bool] = None):
        settings = get_settings()
        self.mock_mode = mock_mode if mock_mode is not None else settings.AWS_MOCK_MODE

    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Returns the list of tool definitions for LLM tool-calling."""
        return TOOL_DEFINITIONS

    def execute_tool(self, tool_name: str, arguments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Executes a named tool with provided arguments.
        Returns execution result dict with data_source ('aws' or 'mock').
        """
        args = arguments or {}
        settings = get_settings()
        is_mock = self.mock_mode or settings.AWS_MOCK_MODE

        if tool_name == "inspect_ec2":
            if is_mock:
                data = mock_data.get_mock_ec2_instances()
                return {
                    "tool_name": "inspect_ec2",
                    "success": True,
                    "data": data,
                    "data_source": "mock"
                }
            else:
                data = ec2.list_ec2_instances()
                # If credentials missing and mock fallback permitted
                if not data.get("success") and "credentials" in str(data.get("error", "")).lower():
                    mock_res = mock_data.get_mock_ec2_instances()
                    return {
                        "tool_name": "inspect_ec2",
                        "success": True,
                        "data": mock_res,
                        "data_source": "mock",
                        "note": "Fell back to development mock data because AWS credentials are unconfigured."
                    }
                return {
                    "tool_name": "inspect_ec2",
                    "success": data.get("success", False),
                    "data": data,
                    "data_source": "aws"
                }

        elif tool_name == "explore_s3":
            if is_mock:
                data = mock_data.get_mock_s3_buckets()
                return {
                    "tool_name": "explore_s3",
                    "success": True,
                    "data": data,
                    "data_source": "mock"
                }
            else:
                data = s3.list_s3_buckets()
                if not data.get("success") and "credentials" in str(data.get("error", "")).lower():
                    mock_res = mock_data.get_mock_s3_buckets()
                    return {
                        "tool_name": "explore_s3",
                        "success": True,
                        "data": mock_res,
                        "data_source": "mock",
                        "note": "Fell back to development mock data because AWS credentials are unconfigured."
                    }
                return {
                    "tool_name": "explore_s3",
                    "success": data.get("success", False),
                    "data": data,
                    "data_source": "aws"
                }

        elif tool_name == "get_cloudwatch_metrics":
            instance_id = args.get("instance_id", "i-03fa78bc91204d8ef")
            hours = int(args.get("hours", 1))

            if is_mock:
                data = mock_data.get_mock_cloudwatch_cpu(instance_id=instance_id, hours=hours)
                return {
                    "tool_name": "get_cloudwatch_metrics",
                    "success": True,
                    "data": data,
                    "data_source": "mock"
                }
            else:
                data = cloudwatch.get_ec2_cpu_utilization(instance_id=instance_id, hours=hours)
                if not data.get("success") and "credentials" in str(data.get("error", "")).lower():
                    mock_res = mock_data.get_mock_cloudwatch_cpu(instance_id=instance_id, hours=hours)
                    return {
                        "tool_name": "get_cloudwatch_metrics",
                        "success": True,
                        "data": mock_res,
                        "data_source": "mock",
                        "note": "Fell back to development mock data because AWS credentials are unconfigured."
                    }
                return {
                    "tool_name": "get_cloudwatch_metrics",
                    "success": data.get("success", False),
                    "data": data,
                    "data_source": "aws"
                }

        elif tool_name == "analyze_cloud_cost":
            days = int(args.get("days", 30))

            if is_mock:
                data = mock_data.get_mock_cost_summary(days=days)
                return {
                    "tool_name": "analyze_cloud_cost",
                    "success": True,
                    "data": data,
                    "data_source": "mock"
                }
            else:
                data = cost_explorer.get_cost_summary(days=days)
                if not data.get("success") and "credentials" in str(data.get("error", "")).lower():
                    mock_res = mock_data.get_mock_cost_summary(days=days)
                    return {
                        "tool_name": "analyze_cloud_cost",
                        "success": True,
                        "data": mock_res,
                        "data_source": "mock",
                        "note": "Fell back to development mock data because AWS credentials are unconfigured."
                    }
                return {
                    "tool_name": "analyze_cloud_cost",
                    "success": data.get("success", False),
                    "data": data,
                    "data_source": "aws"
                }

        else:
            return {
                "tool_name": tool_name,
                "success": False,
                "data": None,
                "error": f"Unknown tool name '{tool_name}'",
                "data_source": "mock" if is_mock else "aws"
            }
