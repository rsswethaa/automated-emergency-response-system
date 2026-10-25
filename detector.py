import math
import random
from statistics import median
from typing import Iterable, Mapping


def classify_severity(impact_g: float, motion_after_impact: bool) -> str:
    """Classify a validated impact magnitude for the educational simulator."""
    impact_g = float(impact_g)
    if not math.isfinite(impact_g) or not 0 <= impact_g <= 100:
        raise ValueError("impact_g must be a finite value between 0 and 100")
    if impact_g >= 6 and not motion_after_impact:
        return "CRITICAL"
    if impact_g >= 4:
        return "HIGH"
    if impact_g >= 2:
        return "MEDIUM"
    return "LOW"


def _sample_magnitude(sample: float | Mapping[str, float]) -> float:
    """Return acceleration magnitude in g for a scalar or x/y/z sample."""
    if isinstance(sample, Mapping):
        try:
            x, y, z = (float(sample[key]) for key in ("x", "y", "z"))
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("vector samples require finite x, y and z values") from exc
        if not all(math.isfinite(value) for value in (x, y, z)):
            raise ValueError("accelerometer samples must be finite")
        return math.sqrt(x * x + y * y + z * z)

    try:
        magnitude = float(sample)
    except (TypeError, ValueError) as exc:
        raise ValueError("accelerometer samples must be numeric") from exc
    if not math.isfinite(magnitude) or magnitude < 0:
        raise ValueError("accelerometer magnitudes must be finite and non-negative")
    return magnitude


def detect_impact(
    samples: Iterable[float | Mapping[str, float]], spike_threshold_g: float = 1.5
) -> dict:
    """Detect an impact spike from a short accelerometer time series.

    The detector estimates the normal acceleration baseline with the median and
    measures the largest positive deviation from that baseline. It is deliberately
    simple and explainable: this is a portfolio simulator, not a certified crash
    detector.
    """
    magnitudes = [_sample_magnitude(sample) for sample in samples]
    if len(magnitudes) < 3:
        raise ValueError("at least three accelerometer samples are required")
    threshold = float(spike_threshold_g)
    if not math.isfinite(threshold) or threshold <= 0:
        raise ValueError("spike_threshold_g must be a positive finite number")

    baseline_g = median(magnitudes)
    peak_g = max(magnitudes)
    impact_delta_g = max(0.0, peak_g - baseline_g)
    peak_index = magnitudes.index(peak_g)
    return {
        "triggered": impact_delta_g >= threshold,
        "baseline_g": round(baseline_g, 4),
        "peak_g": round(peak_g, 4),
        "impact_delta_g": round(impact_delta_g, 4),
        "peak_index": peak_index,
        "sample_count": len(magnitudes),
        "threshold_g": round(threshold, 4),
    }


def simulate_accelerometer(
    impact_g: float, sample_count: int = 41, noise_g: float = 0.03, seed: int = 7
) -> list[float]:
    """Create a deterministic 1 g baseline series with one simulated shock spike."""
    impact_g = float(impact_g)
    if not math.isfinite(impact_g) or not 0 <= impact_g <= 100:
        raise ValueError("impact_g must be a finite value between 0 and 100")
    if sample_count < 5:
        raise ValueError("sample_count must be at least 5")
    rng = random.Random(seed)
    series = [max(0.0, 1.0 + rng.gauss(0.0, noise_g)) for _ in range(sample_count)]
    series[sample_count // 2] = 1.0 + impact_g
    return series


def build_alert_message(incident_id: int, severity: str, latitude: float, longitude: float) -> str:
    return (
        f"Simulated emergency incident #{incident_id}: {severity} severity at "
        f"{latitude:.5f}, {longitude:.5f}. Please review the incident dashboard."
    )
