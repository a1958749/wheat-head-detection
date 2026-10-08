import argparse
import ast
import hashlib
import json
import os
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", type=Path)
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    os.chdir(root)
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    for directory in (root / "app", root / "tool"):
        for source in directory.rglob("*.py"):
            ast.parse(source.read_text(encoding="utf-8-sig"), filename=str(source))

    from main import preload_ml_runtime
    preload_ml_runtime()
    from PyQt5 import QtWidgets
    from app.main_window import MainWindow
    app = QtWidgets.QApplication([])
    window = MainWindow()
    app.processEvents()
    pages = ["overview_page", "workbench_page", "analytics_page", "history_page", "settings_page"]
    for page in pages:
        assert getattr(window, page, None) is not None, page

    weight = root / "weights" / "yolov8n_c2fema_wiou_best.pt"
    result = {
        "source_parse": "passed",
        "ui_initialization": "passed",
        "weight_sha256": hashlib.sha256(weight.read_bytes()).hexdigest(),
    }
    if args.image:
        import cv2
        import numpy as np
        from app.config import build_model_info, load_config
        from app.detection import DetectionEngine
        image = cv2.imdecode(np.fromfile(str(args.image), dtype=np.uint8), cv2.IMREAD_COLOR)
        if image is None:
            raise RuntimeError("Unable to read input image")
        config = load_config()
        config["MODEL"]["device"] = args.device
        engine = DetectionEngine()
        engine.load(build_model_info(config))
        inference = engine.infer(image, config["CLASS_MAP"])
        cv2.imencode(".png", inference["result_image"])[1].tofile(str(root / "verification_preview.png"))
        result.update({"model_load": "passed", "inference": "passed", "device": args.device,
                       "detections": len(inference["detections"]), "inference_ms": inference["inference_ms"]})
    window.close()
    (root / "verification.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
