from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from app.config import parse_classes_setting, resolve_path
from app.models import DetectionItem, ModelInfo
from tool.tools import draw_info, format_data


class DetectionEngine:
    def __init__(self):
        self.model: Optional[Any] = None
        self.model_info: Optional[ModelInfo] = None

    def load(self, model_info: ModelInfo) -> None:
        weight_path = resolve_path(model_info.weight_path)
        if not weight_path.exists():
            raise FileNotFoundError(f"Model weight not found: {weight_path}")

        # Delay ultralytics/torch import to runtime so GUI can still start
        # even when local torch DLL initialization is unstable.
        try:
            from ultralytics import YOLO
        except Exception as error:
            detail = str(error)
            if "WinError 1114" in detail or "c10.dll" in detail:
                detail = (
                    f"{detail}\n"
                    "建议处理：\n"
                    "1) 使用 Python 3.10 环境运行；\n"
                    "2) 通过 main.py 启动程序，不要直接运行页面模块；\n"
                    "3) 若仍失败，重装与当前 Python 匹配的 torch/torchvision。"
                )
            raise RuntimeError(f"Failed to import ultralytics/torch: {detail}") from error

        self.model = YOLO(str(weight_path))
        self.model_info = model_info
        self.model.predict(
            np.zeros((320, 320, 3), dtype=np.uint8),
            imgsz=int(model_info.input_size),
            conf=float(model_info.confidence_threshold),
            device=str(model_info.device),
            classes=parse_classes_setting(model_info.class_filter),
            verbose=False,
        )

    def is_ready(self) -> bool:
        return self.model is not None and self.model_info is not None

    def infer(self, image, class_map: Dict[str, str]) -> Dict:
        if not self.is_ready():
            raise RuntimeError("Model is not loaded yet.")
        assert self.model is not None
        assert self.model_info is not None

        started_at = time.perf_counter()
        raw_results = self.model.predict(
            image.copy(),
            imgsz=int(self.model_info.input_size),
            conf=float(self.model_info.confidence_threshold),
            device=str(self.model_info.device),
            classes=parse_classes_setting(self.model_info.class_filter),
            verbose=False,
        )
        inference_ms = round((time.perf_counter() - started_at) * 1000, 2)

        detections: List[DetectionItem] = []
        for class_name, confidence, box in format_data(raw_results):
            detections.append(
                DetectionItem(
                    class_name=str(class_name),
                    display_name=str(class_map.get(class_name, class_name)),
                    confidence=round(float(confidence), 4),
                    box=[int(value) for value in box],
                )
            )

        draw_payload = [[item.class_name, item.confidence, item.box] for item in detections]
        result_image = draw_info(image.copy(), draw_payload) if detections else image.copy()
        return {
            "detections": detections,
            "result_image": result_image,
            "inference_ms": inference_ms,
        }

    def current_weight_name(self) -> str:
        if not self.model_info:
            return ""
        return Path(self.model_info.weight_path).name
