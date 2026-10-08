from __future__ import annotations

from collections import Counter, defaultdict
from typing import Dict, Iterable, List, Optional

from app.models import AnalysisSummary, DetectionRecord, SessionSummary
from app.storage import format_source_type


def average(values: Iterable[float]) -> float:
    values = list(values)
    return round(sum(values) / len(values), 4) if values else 0.0


def build_session_summary(records: List[DetectionRecord], session_id: str) -> SessionSummary:
    session_records = [record for record in records if record.session_id == session_id]
    input_type_counts = Counter(record.source_type for record in session_records)
    record_count = len(session_records)
    total_targets = sum(record.target_count for record in session_records)
    average_inference_ms = round(sum(record.inference_ms for record in session_records) / record_count, 2) if record_count else 0.0
    average_targets_per_record = round(total_targets / record_count, 2) if record_count else 0.0
    created_at = session_records[-1].timestamp if session_records else ""
    updated_at = session_records[0].timestamp if session_records else ""
    return SessionSummary(
        session_id=session_id,
        created_at=created_at,
        updated_at=updated_at,
        record_count=record_count,
        total_targets=total_targets,
        average_inference_ms=average_inference_ms,
        average_targets_per_record=average_targets_per_record,
        input_type_counts={key: int(value) for key, value in input_type_counts.items()},
    )


def build_analysis_summary(records: List[DetectionRecord], current_session_id: Optional[str] = None) -> AnalysisSummary:
    total_records = len(records)
    total_targets = sum(record.target_count for record in records)
    average_confidence = average(record.average_confidence for record in records if record.target_count > 0)
    average_inference_ms = round(sum(record.inference_ms for record in records) / total_records, 2) if total_records else 0.0
    latest_timestamp = records[0].timestamp if records else ""

    input_type_counts = Counter(format_source_type(record.source_type) for record in records)
    class_counts = Counter()
    trend_counter = defaultdict(int)
    confidence_distribution: List[float] = []
    for record in records:
        class_counts.update(record.class_counts)
        trend_counter[record.timestamp[:16]] += record.target_count
        if record.target_count:
            confidence_distribution.append(record.average_confidence)

    trend_points = [
        {"label": key, "value": value}
        for key, value in sorted(trend_counter.items(), key=lambda item: item[0])[-12:]
    ]
    session_summary = build_session_summary(records, current_session_id) if current_session_id else None

    summary = AnalysisSummary(
        total_records=total_records,
        total_targets=total_targets,
        average_confidence=average_confidence,
        average_inference_ms=average_inference_ms,
        latest_timestamp=latest_timestamp,
        input_type_counts={key: int(value) for key, value in input_type_counts.items()},
        class_counts={key: int(value) for key, value in class_counts.items()},
        trend_points=trend_points,
        session_summary=session_summary,
    )
    setattr(summary, "confidence_distribution", confidence_distribution)
    return summary


def build_recent_target_series(records: List[DetectionRecord], limit: int = 12) -> Dict[str, List]:
    recent_records = list(reversed(records[:limit]))
    labels = [record.source_name[:12] for record in recent_records]
    values = [record.target_count for record in recent_records]
    return {"labels": labels, "values": values}


def build_confidence_histogram(records: List[DetectionRecord]) -> List[float]:
    values = []
    for record in records:
        for detection in record.detections:
            values.append(detection.confidence)
    return values


def build_input_type_series(records: List[DetectionRecord]) -> Dict[str, List]:
    counts = Counter(format_source_type(record.source_type) for record in records)
    return {"labels": list(counts.keys()), "values": list(counts.values())}


def build_class_series(records: List[DetectionRecord]) -> Dict[str, List]:
    counts = Counter()
    for record in records:
        counts.update(record.class_counts)
    most_common = counts.most_common(8)
    return {"labels": [item[0] for item in most_common], "values": [item[1] for item in most_common]}
