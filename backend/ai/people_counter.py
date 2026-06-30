import numpy as np
from typing import Optional

_model = None


def _get_model():
    global _model
    if _model is None:
        from ultralytics import YOLO
        _model = YOLO("yolov8n.pt")
    return _model


def count_persons(frame: np.ndarray) -> tuple[int, list[list[int]]]:
    """Detect and count persons in a frame. Returns (count, list of [x1,y1,x2,y2])."""
    try:
        model = _get_model()
        results = model(frame, classes=[0], verbose=False)
        boxes = []
        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                boxes.append([int(x1), int(y1), int(x2), int(y2)])
        return len(boxes), boxes
    except Exception as e:
        print(f"[AI/people_counter] error: {e}")
        return 0, []
