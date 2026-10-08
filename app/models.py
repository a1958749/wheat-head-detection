from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


class RuntimeStatus(str, Enum):
    IDLE = "idle"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    FINISHED = "finished"
    ERROR = "error"


@dataclass
class DetectionItem:
    class_name: str
    display_name: str
    confidence: float
    box: List[int]

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "DetectionItem":
        return cls(
            class_name=str(data.get("class_name", "")),
            display_name=str(data.get("display_name", "")),
            confidence=float(data.get("confidence", 0.0)),
            box=[int(value) for value in data.get("box", [0, 0, 0, 0])],
        )


@dataclass
class ModelInfo:
    model_name: str
    weight_path: str
    weight_name: str
    baseline_name: str
    backbone: str
    device: str
    input_size: int
    confidence_threshold: float
    class_filter: Optional[str]
    improvement_points: List[str] = field(default_factory=list)
    metrics: Dict[str, str] = field(default_factory=dict)
    description: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "ModelInfo":
        return cls(
            model_name=str(data.get("model_name", "")),
            weight_path=str(data.get("weight_path", "")),
            weight_name=str(data.get("weight_name", "")),
            baseline_name=str(data.get("baseline_name", "YOLOv8")),
            backbone=str(data.get("backbone", "YOLOv8 Backbone")),
            device=str(data.get("device", "cpu")),
            input_size=int(data.get("input_size", 640)),
            confidence_threshold=float(data.get("confidence_threshold", 0.4)),
            class_filter=data.get("class_filter"),
            improvement_points=list(data.get("improvement_points", [])),
            metrics=dict(data.get("metrics", {})),
            description=str(data.get("description", "")),
        )


@dataclass
class DetectionRecord:
    record_uid: str
    record_id: int
    session_id: str
    timestamp: str
    source_type: str
    source_name: str
    source_path: str
    original_path: str
    result_path: str
    target_count: int
    average_confidence: float
    max_confidence: float
    inference_ms: float
    result_summary: str
    top_class: str
    class_counts: Dict[str, int]
    detections: List[DetectionItem]
    model_name: str
    model_weight: str
    progress_current: int = 1
    progress_total: int = 1
    storage_type: str = "structured"
    manifest_path: str = ""
    session_dir: str = ""

    def to_dict(self) -> Dict:
        data = asdict(self)
        data["detections"] = [item.to_dict() for item in self.detections]
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> "DetectionRecord":
        return cls(
            record_uid=str(data.get("record_uid", "")),
            record_id=int(data.get("record_id", 0)),
            session_id=str(data.get("session_id", "")),
            timestamp=str(data.get("timestamp", "")),
            source_type=str(data.get("source_type", "")),
            source_name=str(data.get("source_name", "")),
            source_path=str(data.get("source_path", "")),
            original_path=str(data.get("original_path", "")),
            result_path=str(data.get("result_path", "")),
            target_count=int(data.get("target_count", 0)),
            average_confidence=float(data.get("average_confidence", 0.0)),
            max_confidence=float(data.get("max_confidence", 0.0)),
            inference_ms=float(data.get("inference_ms", 0.0)),
            result_summary=str(data.get("result_summary", "")),
            top_class=str(data.get("top_class", "")),
            class_counts={str(key): int(value) for key, value in dict(data.get("class_counts", {})).items()},
            detections=[DetectionItem.from_dict(item) for item in data.get("detections", [])],
            model_name=str(data.get("model_name", "")),
            model_weight=str(data.get("model_weight", "")),
            progress_current=int(data.get("progress_current", 1)),
            progress_total=int(data.get("progress_total", 1)),
            storage_type=str(data.get("storage_type", "structured")),
            manifest_path=str(data.get("manifest_path", "")),
            session_dir=str(data.get("session_dir", "")),
        )

    @property
    def progress_ratio(self) -> float:
        if self.progress_total <= 0:
            return 0.0
        return self.progress_current / self.progress_total


@dataclass
class SessionSummary:
    session_id: str
    created_at: str
    updated_at: str
    record_count: int
    total_targets: int
    average_inference_ms: float
    average_targets_per_record: float
    input_type_counts: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "SessionSummary":
        return cls(
            session_id=str(data.get("session_id", "")),
            created_at=str(data.get("created_at", "")),
            updated_at=str(data.get("updated_at", "")),
            record_count=int(data.get("record_count", 0)),
            total_targets=int(data.get("total_targets", 0)),
            average_inference_ms=float(data.get("average_inference_ms", 0.0)),
            average_targets_per_record=float(data.get("average_targets_per_record", 0.0)),
            input_type_counts={str(key): int(value) for key, value in dict(data.get("input_type_counts", {})).items()},
        )


@dataclass
class RuntimeState:
    status: RuntimeStatus = RuntimeStatus.IDLE
    source_type: str = ""
    source_name: str = ""
    source_path: str = ""
    current_file_name: str = ""
    progress_current: int = 0
    progress_total: int = 0
    progress_text: str = "0 / 0"
    elapsed_ms: float = 0.0
    current_fps: float = 0.0
    message: str = "系统空闲"
    error_message: str = ""
    updated_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def to_dict(self) -> Dict:
        data = asdict(self)
        data["status"] = self.status.value
        return data


@dataclass
class AnalysisSummary:
    total_records: int
    total_targets: int
    average_confidence: float
    average_inference_ms: float
    latest_timestamp: str
    input_type_counts: Dict[str, int] = field(default_factory=dict)
    class_counts: Dict[str, int] = field(default_factory=dict)
    trend_points: List[Dict[str, float]] = field(default_factory=list)
    session_summary: Optional[SessionSummary] = None

    def to_dict(self) -> Dict:
        data = asdict(self)
        if self.session_summary is not None:
            data["session_summary"] = self.session_summary.to_dict()
        return data
