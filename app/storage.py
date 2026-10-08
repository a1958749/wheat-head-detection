from __future__ import annotations

import ast
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional

import cv2
import numpy as np

from app.config import ensure_directory, resolve_path, to_project_relative
from app.models import DetectionItem, DetectionRecord, ModelInfo, SessionSummary
from tool.tools import writecsv, writexls


def current_time_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def current_file_timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")


def sanitize_filename(name: str) -> str:
    cleaned = []
    for char in str(name):
        if char.isalnum() or char in {"-", "_"}:
            cleaned.append(char)
        else:
            cleaned.append("_")
    return "".join(cleaned).strip("_") or "record"


def read_image(path_value: str):
    if not path_value:
        return None
    path_obj = resolve_path(path_value) if str(path_value).startswith(".") else Path(path_value)
    if not path_obj.exists():
        return None
    return cv2.imdecode(np.fromfile(str(path_obj), dtype=np.uint8), cv2.IMREAD_COLOR)


def write_image(path_value: Path, image) -> None:
    if image is None:
        return
    ensure_directory(path_value.parent)
    cv2.imencode(".jpg", image)[1].tofile(str(path_value))


def parse_timestamp(value: str) -> datetime:
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    except Exception:
        return datetime.min


def read_text_lines_with_fallback(path: Path):
    for encoding in ("utf-8", "gbk", "gb2312", "utf-8-sig", "latin-1"):
        try:
            with open(path, "r", encoding=encoding) as text_file:
                return text_file.readlines()
        except UnicodeDecodeError:
            continue
    with open(path, "r", encoding="utf-8", errors="ignore") as text_file:
        return text_file.readlines()


def format_source_type(source_type: str) -> str:
    mapping = {
        "image": "单张图像",
        "folder": "图像文件夹",
        "video": "视频文件",
        "camera": "实时摄像头",
        "legacy": "旧版记录",
    }
    return mapping.get(source_type, source_type or "未选择")


def infer_source_type(path_value: str) -> str:
    text = str(path_value).lower()
    if text.startswith("camera"):
        return "camera"
    suffix = Path(str(path_value)).suffix.lower()
    if suffix in {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}:
        return "image"
    if suffix in {".mp4", ".avi", ".mov", ".mkv"}:
        return "video"
    if Path(str(path_value)).is_dir():
        return "folder"
    return "legacy"


def build_result_summary(items: List[DetectionItem], no_target_label: str) -> str:
    if not items:
        return no_target_label
    counts = Counter(item.display_name for item in items)
    return "，".join(f"{name} {count}" for name, count in counts.items())


def build_class_counts(items: List[DetectionItem]):
    return {name: int(count) for name, count in Counter(item.display_name for item in items).items()}


def build_top_class(items: List[DetectionItem], no_target_label: str) -> str:
    if not items:
        return no_target_label
    return Counter(item.display_name for item in items).most_common(1)[0][0]


class RecordRepository:
    def __init__(self, output_root: str, model_info: ModelInfo):
        self.output_root = resolve_path(output_root)
        ensure_directory(self.output_root)
        self.legacy_root = self.output_root.parent
        self.model_info = model_info
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = self.output_root / self.session_id
        self.original_dir = self.session_dir / "originals"
        self.result_dir = self.session_dir / "results"
        ensure_directory(self.original_dir)
        ensure_directory(self.result_dir)
        self.manifest_path = self.session_dir / "session.json"
        self.session_records: List[DetectionRecord] = []
        self.created_at = current_time_text()
        self._write_manifest()

    @classmethod
    def scan_history(cls, output_root: str, limit: Optional[int] = None) -> List[DetectionRecord]:
        repo = cls.__new__(cls)
        repo.output_root = resolve_path(output_root)
        ensure_directory(repo.output_root)
        repo.legacy_root = repo.output_root.parent
        records = repo._load_structured_records() + repo._load_legacy_records()
        records.sort(key=lambda item: parse_timestamp(item.timestamp), reverse=True)
        return records[:limit] if limit else records

    def build_session_summary(self) -> SessionSummary:
        record_count = len(self.session_records)
        total_targets = sum(record.target_count for record in self.session_records)
        average_inference_ms = round(
            sum(record.inference_ms for record in self.session_records) / record_count, 2
        ) if record_count else 0.0
        average_targets_per_record = round(total_targets / record_count, 2) if record_count else 0.0
        input_type_counts = Counter(record.source_type for record in self.session_records)
        return SessionSummary(
            session_id=self.session_id,
            created_at=self.created_at,
            updated_at=current_time_text(),
            record_count=record_count,
            total_targets=total_targets,
            average_inference_ms=average_inference_ms,
            average_targets_per_record=average_targets_per_record,
            input_type_counts={key: int(value) for key, value in input_type_counts.items()},
        )

    def _write_manifest(self) -> None:
        summary = self.build_session_summary()
        payload = {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "updated_at": current_time_text(),
            "model": self.model_info.to_dict(),
            "summary": summary.to_dict(),
            "records": [record.to_dict() for record in self.session_records],
        }
        with open(self.manifest_path, "w", encoding="utf-8") as manifest_file:
            json.dump(payload, manifest_file, ensure_ascii=False, indent=2)

    def append_record(
        self,
        record: DetectionRecord,
        original_frame,
        result_frame,
        auto_save_result_image: bool = True,
        auto_save_structured_record: bool = True,
    ) -> DetectionRecord:
        if auto_save_result_image:
            file_name = f"{sanitize_filename(Path(record.source_name).stem)}_{current_file_timestamp()}.jpg"
            original_path = self.original_dir / file_name
            result_path = self.result_dir / file_name
            write_image(original_path, original_frame)
            write_image(result_path, result_frame)
            record.original_path = to_project_relative(original_path)
            record.result_path = to_project_relative(result_path)

        self.session_records.append(record)
        if auto_save_structured_record:
            self._write_manifest()
        return record

    def delete_record(self, record_uid: str) -> bool:
        target_record = next((item for item in self.session_records if item.record_uid == record_uid), None)
        if target_record is None:
            manifest_path = None
            session_records = self._load_structured_records()
            target_record = next((item for item in session_records if item.record_uid == record_uid), None)
            if target_record is None:
                return False
            manifest_path = Path(target_record.manifest_path)
            if not manifest_path.exists():
                return False
            with open(manifest_path, "r", encoding="utf-8") as manifest_file:
                payload = json.load(manifest_file)
            payload["records"] = [item for item in payload.get("records", []) if item.get("record_uid") != record_uid]
            remaining = [DetectionRecord.from_dict(item) for item in payload["records"]]
            record_count = len(remaining)
            total_targets = sum(item.target_count for item in remaining)
            average_inference_ms = round(sum(item.inference_ms for item in remaining) / record_count, 2) if record_count else 0.0
            average_targets_per_record = round(total_targets / record_count, 2) if record_count else 0.0
            input_type_counts = Counter(item.source_type for item in remaining)
            payload["summary"] = SessionSummary(
                session_id=str(payload.get("session_id", "")),
                created_at=str(payload.get("created_at", "")),
                updated_at=current_time_text(),
                record_count=record_count,
                total_targets=total_targets,
                average_inference_ms=average_inference_ms,
                average_targets_per_record=average_targets_per_record,
                input_type_counts={key: int(value) for key, value in input_type_counts.items()},
            ).to_dict()
            payload["updated_at"] = current_time_text()
            self._cleanup_record_images(target_record)
            with open(manifest_path, "w", encoding="utf-8") as manifest_file:
                json.dump(payload, manifest_file, ensure_ascii=False, indent=2)
            return True

        self.session_records = [item for item in self.session_records if item.record_uid != record_uid]
        self._cleanup_record_images(target_record)
        self._write_manifest()
        return True

    def clear_session_records(self) -> None:
        for record in list(self.session_records):
            self._cleanup_record_images(record)
        self.session_records = []
        self._write_manifest()

    def _cleanup_record_images(self, record: DetectionRecord) -> None:
        for path_value in (record.original_path, record.result_path):
            if not path_value:
                continue
            file_path = resolve_path(path_value) if str(path_value).startswith(".") else Path(path_value)
            if file_path.exists():
                try:
                    file_path.unlink()
                except OSError:
                    pass

    def export_records(self, records: Iterable[DetectionRecord], save_path: str, export_type: str) -> None:
        rows = [[
            "记录编号", "检测时间", "输入类型", "原始文件名", "原始路径", "目标数",
            "平均置信度", "最大置信度", "耗时(ms)", "结果摘要", "结果图路径",
            "模型名称", "权重文件", "会话ID",
        ]]
        for record in records:
            rows.append([
                record.record_uid,
                record.timestamp,
                format_source_type(record.source_type),
                record.source_name,
                record.source_path,
                record.target_count,
                round(record.average_confidence, 4),
                round(record.max_confidence, 4),
                round(record.inference_ms, 2),
                record.result_summary,
                record.result_path,
                record.model_name,
                record.model_weight,
                record.session_id,
            ])
        if export_type == "xls":
            writexls(rows, save_path)
        else:
            writecsv(rows, save_path)

    def _load_structured_records(self) -> List[DetectionRecord]:
        records: List[DetectionRecord] = []
        if not self.output_root.exists():
            return records
        for manifest_path in sorted(self.output_root.glob("*/session.json"), reverse=True):
            try:
                with open(manifest_path, "r", encoding="utf-8") as manifest_file:
                    payload = json.load(manifest_file)
            except (OSError, json.JSONDecodeError):
                continue
            session_id = str(payload.get("session_id", manifest_path.parent.name))
            for record_data in payload.get("records", []):
                record = DetectionRecord.from_dict(record_data)
                record.session_id = session_id
                record.manifest_path = str(manifest_path)
                record.session_dir = str(manifest_path.parent)
                if not record.record_uid:
                    record.record_uid = f"structured::{session_id}::{record.record_id}"
                records.append(record)
        return records

    def _load_legacy_records(self) -> List[DetectionRecord]:
        records: List[DetectionRecord] = []
        if not self.legacy_root.exists():
            return records
        for output_dir in sorted(self.legacy_root.iterdir(), reverse=True):
            if not output_dir.is_dir() or output_dir.name == "sessions":
                continue
            result_txt = output_dir / "result.txt"
            if not result_txt.exists():
                continue
            try:
                lines = read_text_lines_with_fallback(result_txt)[1:]
            except OSError:
                continue
            for row_index, line in enumerate(lines, start=1):
                text = line.strip()
                if not text:
                    continue
                try:
                    row = ast.literal_eval(f"[{text}]")
                except (ValueError, SyntaxError):
                    continue
                if len(row) < 7:
                    continue
                items = [
                    DetectionItem(
                        class_name=str(item[0]),
                        display_name=str(item[0]),
                        confidence=float(item[1]),
                        box=[int(value) for value in item[2]],
                    )
                    for item in (row[3] or [])
                    if len(item) >= 3
                ]
                max_conf = max((item.confidence for item in items), default=0.0)
                record = DetectionRecord(
                    record_uid=f"legacy::{output_dir.name}::{row_index}",
                    record_id=row_index,
                    session_id=output_dir.name,
                    timestamp=str(row[2]),
                    source_type=infer_source_type(str(row[1])),
                    source_name=Path(str(row[1])).name if str(row[1]) not in {"camera", ""} else f"legacy_{row_index}",
                    source_path=str(row[1]),
                    original_path=str(row[1]) if Path(str(row[1])).suffix else "",
                    result_path=str(row[6]),
                    target_count=int(row[4]),
                    average_confidence=round(sum(item.confidence for item in items) / len(items), 4) if items else 0.0,
                    max_confidence=max_conf,
                    inference_ms=float(str(row[5]).replace("s", "")) * 1000 if "s" in str(row[5]) else float(str(row[5]).replace("ms", "") or 0),
                    result_summary=build_result_summary(items, "无检测目标"),
                    top_class=build_top_class(items, "无检测目标"),
                    class_counts=build_class_counts(items),
                    detections=items,
                    model_name="旧版模型记录",
                    model_weight="legacy",
                    storage_type="legacy",
                    manifest_path=str(result_txt),
                    session_dir=str(output_dir),
                )
                records.append(record)
        return records
