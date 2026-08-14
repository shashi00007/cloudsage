"""
Currency Localization and Conversion Utility for CloudSage.
Provides USD to INR conversion, Indian number system formatting, and central currency configuration.
"""

from typing import Any, Dict, List, Optional
from app.config import get_settings


def get_configured_exchange_rate() -> float:
    """Returns the configured USD to INR exchange rate from application settings."""
    settings = get_settings()
    return float(getattr(settings, "USD_TO_INR_RATE", 85.0))


def get_currency_symbol() -> str:
    """Returns the default currency symbol (e.g. ₹)."""
    settings = get_settings()
    return getattr(settings, "CURRENCY_SYMBOL", "₹")


def get_default_currency() -> str:
    """Returns the default currency code (e.g. INR)."""
    settings = get_settings()
    return getattr(settings, "DEFAULT_CURRENCY", "INR")


def convert_usd_to_inr(amount_usd: float, rate: Optional[float] = None) -> float:
    """
    Converts a USD amount to INR using the configured or provided exchange rate.
    Rounds to 2 decimal places.
    """
    conversion_rate = rate if rate is not None else get_configured_exchange_rate()
    return round(amount_usd * conversion_rate, 2)


def format_inr(amount: float, symbol: bool = True) -> str:
    """
    Formats a numeric amount according to the Indian numbering system.
    Examples:
        40995.50 -> ₹40,995.50
        20833.50 -> ₹20,833.50
        142500.00 -> ₹1,42,500.00
        10000000.00 -> ₹1,00,00,000.00
    """
    sym = get_currency_symbol() if symbol else ""
    
    # Handle negative values
    is_negative = amount < 0
    abs_amount = abs(amount)
    
    # Split into integer and decimal parts
    formatted_float = f"{abs_amount:.2f}"
    int_part, dec_part = formatted_float.split(".")
    
    # Format integer part with Indian comma grouping (last 3 digits, then pairs of 2 digits)
    if len(int_part) <= 3:
        grouped_int = int_part
    else:
        last_three = int_part[-3:]
        remaining = int_part[:-3]
        
        # Group remaining digits in pairs of 2 from right to left
        groups = []
        while len(remaining) > 2:
            groups.insert(0, remaining[-2:])
            remaining = remaining[:-2]
        if remaining:
            groups.insert(0, remaining)
        
        grouped_int = ",".join(groups) + "," + last_three

    sign = "-" if is_negative else ""
    return f"{sign}{sym}{grouped_int}.{dec_part}"


def convert_and_format_cost(amount_usd: float, rate: Optional[float] = None, symbol: bool = True) -> str:
    """
    Converts a USD amount to INR and formats it with the ₹ currency symbol.
    Example: 482.30 -> ₹40,995.50 (at rate 85.0)
    """
    inr_amount = convert_usd_to_inr(amount_usd, rate=rate)
    return format_inr(inr_amount, symbol=symbol)


def convert_cost_summary(cost_data: Dict[str, Any], rate: Optional[float] = None) -> Dict[str, Any]:
    """
    Converts a complete AWS Cost Explorer summary dict from USD to INR.
    Preserves all original date ranges, service percentages, and structure.
    """
    conversion_rate = rate if rate is not None else get_configured_exchange_rate()
    orig_currency = cost_data.get("currency", "USD")
    
    # If already in INR, return formatted copy
    if orig_currency == "INR":
        return dict(cost_data)

    total_usd = float(cost_data.get("total_cost", 0.0))
    total_inr = convert_usd_to_inr(total_usd, conversion_rate)

    services_inr: List[Dict[str, Any]] = []
    for svc in cost_data.get("services", []):
        svc_usd = float(svc.get("cost", 0.0))
        svc_inr = convert_usd_to_inr(svc_usd, conversion_rate)
        services_inr.append({
            "service": svc.get("service", "Unknown"),
            "cost": svc_inr,
            "cost_formatted": format_inr(svc_inr),
            "percentage": svc.get("percentage", 0.0)
        })

    return {
        "success": cost_data.get("success", True),
        "start_date": cost_data.get("start_date", ""),
        "end_date": cost_data.get("end_date", ""),
        "total_cost": total_inr,
        "total_cost_formatted": format_inr(total_inr),
        "currency": "INR",
        "currency_symbol": get_currency_symbol(),
        "exchange_rate": conversion_rate,
        "original_currency": orig_currency,
        "top_service": cost_data.get("top_service", "None"),
        "service_count": len(services_inr),
        "services": services_inr,
        "error": cost_data.get("error")
    }
