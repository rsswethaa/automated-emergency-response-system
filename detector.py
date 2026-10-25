def classify_severity(impact_g: float, motion_after_impact: bool) -> str:
    """Simple educational rule engine for simulated accident severity."""
    if impact_g >= 6 and not motion_after_impact:
        return "CRITICAL"
    if impact_g >= 4:
        return "HIGH"
    if impact_g >= 2:
        return "MEDIUM"
    return "LOW"


def build_alert_message(incident_id: int, severity: str, latitude: float, longitude: float) -> str:
    return (
        f"Simulated emergency incident #{incident_id}: {severity} severity at "
        f"{latitude:.5f}, {longitude:.5f}. Please review the incident dashboard."
    )
