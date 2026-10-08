from __future__ import annotations

import ast
import os
from pathlib import Path
from typing import Dict, List

import yaml

from app.models import ModelInfo


PROJECT_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_DIR / "config" / "configs.yaml"


DEFAULT_CONFIG: Dict = {
    "APP": {
        "system_title": "小麦麦穗检测识别系统",
        "system_subtitle": "基于改进 YOLOv8 的小麦麦穗智能检测与分析平台",
        "overview_description": "系统面向精准农业场景，提供小麦麦穗目标检测、结果管理、数据分析与工程化配置管理能力，可服务于田间巡检、产量评估与农情辅助分析。",
    },
    "MODEL": {
        "weight": "./weights/yolov8n_c2fema_wiou_best.pt",
        "device": "0",
        "conf": 0.4,
        "classes": None,
        "imgsize": 768,
        "baseline_name": "YOLOv8n",
        "model_name": "YOLOv8n-C2fEMA-WIoU",
        "backbone": "YOLOv8n + C2f-EMA + WIoU",
        "description": "基于YOLOv8n并融合C2f-EMA结构与WIoU定位约束的小麦麦穗检测模型，适用于图像、视频与实时流检测任务。",
        "improvement_points": ["C2f内部EMA注意力增强", "WIoU边界框定位优化"],
        "metrics": {
            "mAP50": "0.944603",
            "Precision": "0.923962",
            "Recall": "0.886569",
            "F1": "0.904879",
            "mAP50_95": "0.544774",
        },
    },
    "PATHS": {
        "output_root": "./output/sessions",
        "hero_image": "./icon/zhutu2.png",
        "background_image": "./icon/background.jpg",
        "sample_dir": "./img",
        "weights_root": "./weights",
    },
    "RUNTIME": {
        "camera_index": 0,
        "playback_interval_ms": 80,
        "history_limit": 2000,
        "default_theme": "agriculture_light",
        "default_image_mode": "dual",
        "default_table_font_size": 10,
    },
    "FEATURES": {
        "auto_save_result_image": True,
        "auto_save_structured_record": True,
        "auto_export_session_summary": False,
        "enable_model_switch": True,
    },
    "DISPLAY": {
        "theme": "agriculture_light",
        "image_view_mode": "dual",
        "table_font_size": 10,
    },
    "LABELS": {
        "all_targets": "全部目标",
        "no_target": "无检测目标",
    },
    "CLASS_MAP": {
        "wheat": "麦穗",
    },
}


def deep_merge(base: Dict, override: Dict) -> Dict:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def migrate_legacy_config(raw_config: Dict) -> Dict:
    if not raw_config:
        return {}

    migrated: Dict = {}

    model_cfg = raw_config.get("MODEL", {})
    if model_cfg:
        migrated["MODEL"] = {
            "weight": model_cfg.get("weight", model_cfg.get("WEIGHT")),
            "device": model_cfg.get("device", model_cfg.get("DEVICE", "cpu")),
            "conf": model_cfg.get("conf", model_cfg.get("CONF", 0.4)),
            "classes": model_cfg.get("classes", model_cfg.get("CLASSES")),
            "imgsize": model_cfg.get("imgsize", model_cfg.get("IMGSIZE", 640)),
        }

    runtime_cfg = raw_config.get("CONFIG", {})
    if runtime_cfg:
        migrated["RUNTIME"] = {
            "camera_index": runtime_cfg.get("camera_index", runtime_cfg.get("camera_num", 0)),
        }
        class_map = runtime_cfg.get("chinese_name", {})
        if isinstance(class_map, dict):
            migrated["CLASS_MAP"] = {
                str(key): str(value)
                for key, value in class_map.items()
                if str(key).lower() not in {"no_target", "无目标", "全部目标"}
            }

    ui_cfg = raw_config.get("UI", {})
    if ui_cfg:
        migrated["APP"] = {
            "system_title": ui_cfg.get("title", DEFAULT_CONFIG["APP"]["system_title"]),
            "system_subtitle": ui_cfg.get("label_title", DEFAULT_CONFIG["APP"]["system_subtitle"]),
        }
        migrated["PATHS"] = {
            "hero_image": ui_cfg.get("zhutu2", DEFAULT_CONFIG["PATHS"]["hero_image"]),
            "background_image": ui_cfg.get("background", DEFAULT_CONFIG["PATHS"]["background_image"]),
        }
    return migrated


def load_config(config_path: Path = CONFIG_PATH) -> Dict:
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as config_file:
            raw = yaml.safe_load(config_file) or {}
    else:
        raw = {}
    config = deep_merge(DEFAULT_CONFIG, migrate_legacy_config(raw))
    config = deep_merge(config, raw)
    return config


def save_config(config: Dict, config_path: Path = CONFIG_PATH) -> None:
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as config_file:
        yaml.safe_dump(config, config_file, allow_unicode=True, sort_keys=False)


def restore_default_config(config_path: Path = CONFIG_PATH) -> Dict:
    save_config(DEFAULT_CONFIG, config_path)
    return load_config(config_path)


def resolve_path(path_value: str) -> Path:
    candidate = Path(path_value)
    if candidate.is_absolute():
        return candidate
    return (PROJECT_DIR / candidate).resolve()


def to_project_relative(path_value: Path) -> str:
    try:
        relative = path_value.resolve().relative_to(PROJECT_DIR.resolve())
        return f"./{str(relative).replace(os.sep, '/')}"
    except ValueError:
        return str(path_value).replace(os.sep, "/")


def ensure_directory(path_value: Path) -> None:
    path_value.mkdir(parents=True, exist_ok=True)


def parse_classes_setting(raw_value):
    if raw_value in (None, "", "None", "null", "Null"):
        return None
    if isinstance(raw_value, (list, tuple, int)):
        return raw_value
    try:
        return ast.literal_eval(str(raw_value))
    except Exception:
        return None


def build_model_info(config: Dict) -> ModelInfo:
    model_cfg = config["MODEL"]
    weight_path = resolve_path(str(model_cfg.get("weight", "")))
    return ModelInfo(
        model_name=str(model_cfg.get("model_name", weight_path.stem if weight_path else "未命名模型")),
        weight_path=str(model_cfg.get("weight", "")),
        weight_name=weight_path.name if weight_path else "",
        baseline_name=str(model_cfg.get("baseline_name", "YOLOv8")),
        backbone=str(model_cfg.get("backbone", "YOLOv8 Backbone")),
        device=str(model_cfg.get("device", "cpu")),
        input_size=int(model_cfg.get("imgsize", 640)),
        confidence_threshold=float(model_cfg.get("conf", 0.4)),
        class_filter=None if model_cfg.get("classes") is None else str(model_cfg.get("classes")),
        improvement_points=list(model_cfg.get("improvement_points", [])),
        metrics=dict(model_cfg.get("metrics", {})),
        description=str(model_cfg.get("description", "")),
    )


def scan_weight_candidates(config: Dict) -> List[str]:
    weights_root = resolve_path(config["PATHS"].get("weights_root", "./weights"))
    candidates: List[str] = []
    if not weights_root.exists():
        return candidates
    for weight_path in sorted(weights_root.rglob("*.pt")):
        candidates.append(to_project_relative(weight_path))
    return candidates
