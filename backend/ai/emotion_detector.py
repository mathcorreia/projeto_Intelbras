import numpy as np
from typing import Optional


def detect_emotion(face_img: np.ndarray) -> Optional[dict]:
    """Detect dominant emotion in a face image crop.
    Returns {emotion: str, confidence: float} or None on failure.
    """
    if face_img is None or face_img.size == 0:
        return None
    try:
        from deepface import DeepFace
        result = DeepFace.analyze(
            face_img,
            actions=["emotion"],
            enforce_detection=False,
            silent=True,
        )
        if isinstance(result, list):
            result = result[0]
        dominant = result.get("dominant_emotion")
        scores = result.get("emotion", {})
        confidence = round(scores.get(dominant, 0) / 100.0, 3) if dominant else 0.0
        return {"emotion": dominant, "confidence": confidence}
    except Exception as e:
        print(f"[AI/emotion_detector] error: {e}")
        return None
