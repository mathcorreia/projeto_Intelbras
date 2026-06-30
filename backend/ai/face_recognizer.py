import json
import numpy as np
from typing import Optional

_app = None


def _get_app():
    global _app
    if _app is None:
        from insightface.app import FaceAnalysis
        _app = FaceAnalysis(name="buffalo_sc", providers=["CPUExecutionProvider"])
        _app.prepare(ctx_id=0, det_size=(320, 320))
    return _app


def extract_faces(frame: np.ndarray) -> list[dict]:
    """Return list of {bbox: [x1,y1,x2,y2], embedding: np.ndarray} for each face."""
    try:
        app = _get_app()
        faces = app.get(frame)
        return [{"bbox": f.bbox.tolist(), "embedding": f.embedding} for f in faces if f.embedding is not None]
    except Exception as e:
        print(f"[AI/face_recognizer] extract_faces error: {e}")
        return []


def get_embedding(face_img: np.ndarray) -> Optional[np.ndarray]:
    """Generate InsightFace embedding from a single face crop."""
    try:
        app = _get_app()
        faces = app.get(face_img)
        if not faces:
            return None
        return faces[0].embedding
    except Exception as e:
        print(f"[AI/face_recognizer] get_embedding error: {e}")
        return None


def match_person(embedding: np.ndarray, persons: list) -> tuple[Optional[object], float]:
    """Cosine-similarity match against Person DB records.
    Returns (best_person, similarity) where similarity is in [0, 1].
    Returns (None, 0.0) when no person has a stored encoding.
    """
    best_person = None
    best_sim = 0.0
    norm_q = np.linalg.norm(embedding)
    if norm_q == 0:
        return None, 0.0

    for person in persons:
        if not person.face_encoding:
            continue
        try:
            stored = np.array(json.loads(person.face_encoding), dtype=np.float32)
            norm_s = np.linalg.norm(stored)
            if norm_s == 0:
                continue
            sim = float(np.dot(embedding, stored) / (norm_q * norm_s))
            if sim > best_sim:
                best_sim = sim
                best_person = person
        except Exception:
            continue

    return best_person, best_sim
