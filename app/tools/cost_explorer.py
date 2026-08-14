"""
Cost Explorer Operational Tool for CloudSage.
Provides cost and usage summaries and service-level expenditure breakdown.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
import boto3
from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError

from app.services import aws_session


def get_cost_summary(
    days: int = 30,
    session: Optional[boto3.Session] = None
) -> Dict[str, Any]:
    """
    Retrieves an AWS cost summary for the specified recent period (in days).
    Returns total estimated cost, currency, date range, and service-level breakdown.
    Does not fabricate data if Cost Explorer is unavailable or unconfigured.
    """
    sess = session or aws_session.get_aws_session()

    # Calculate date range in YYYY-MM-DD format
    today = datetime.now(timezone.utc).date()
    start_date = today - timedelta(days=days)
    
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = today.strftime("%Y-%m-%d")

    try:
        ce_client = aws_session.get_aws_client("ce", session=sess)
        
        response = ce_client.get_cost_and_usage(
            TimePeriod={"Start": start_str, "End": end_str},
            Granularity="MONTHLY",
            Metrics=["UnblendedCost"],
            GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}]
        )

        results_by_time = response.get("ResultsByTime", [])
        service_costs: Dict[str, float] = {}
        currency = "USD"

        for period in results_by_time:
            for group in period.get("Groups", []):
                service_name = group.get("Keys", ["Unknown"])[0]
                metrics = group.get("Metrics", {})
                cost_data = metrics.get("UnblendedCost", {})
                amount = float(cost_data.get("Amount", 0.0))
                unit = cost_data.get("Unit", "USD")
                if unit:
                    currency = unit

                service_costs[service_name] = service_costs.get(service_name, 0.0) + amount

        total_cost = sum(service_costs.values())

        # Sort services by cost descending
        breakdown: List[Dict[str, Any]] = []
        for svc, cost in sorted(service_costs.items(), key=lambda x: x[1], reverse=True):
            pct = round((cost / total_cost * 100), 1) if total_cost > 0 else 0.0
            breakdown.append({
                "service": svc,
                "cost": round(cost, 2),
                "percentage": pct
            })

        top_service = breakdown[0]["service"] if breakdown else "None"

        return {
            "success": True,
            "start_date": start_str,
            "end_date": end_str,
            "total_cost": round(total_cost, 2),
            "currency": currency,
            "top_service": top_service,
            "service_count": len(breakdown),
            "services": breakdown,
            "error": None
        }

    except NoCredentialsError:
        return {
            "success": False,
            "start_date": start_str,
            "end_date": end_str,
            "total_cost": 0.0,
            "currency": "USD",
            "services": [],
            "error": "AWS credentials are not configured or are invalid"
        }
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "ClientError")
        error_msg = e.response.get("Error", {}).get("Message", str(e))
        
        if error_code in ["AccessDeniedException", "UnauthorizedException"]:
            guidance = "Access denied for AWS Cost Explorer. Ensure the IAM identity has 'ce:GetCostAndUsage' permissions and Cost Explorer is enabled in the AWS Billing console."
        elif error_code in ["DataUnavailableException", "BillExpirationException"]:
            guidance = "Cost Explorer data is currently unavailable for this account or billing setup."
        else:
            guidance = f"AWS Cost Explorer API error ({error_code}): {error_msg}"

        return {
            "success": False,
            "start_date": start_str,
            "end_date": end_str,
            "total_cost": 0.0,
            "currency": "USD",
            "services": [],
            "error": guidance
        }
    except BotoCoreError as e:
        return {
            "success": False,
            "start_date": start_str,
            "end_date": end_str,
            "total_cost": 0.0,
            "currency": "USD",
            "services": [],
            "error": f"AWS SDK error: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "start_date": start_str,
            "end_date": end_str,
            "total_cost": 0.0,
            "currency": "USD",
            "services": [],
            "error": f"Unexpected error retrieving Cost Explorer summary: {str(e)}"
        }
