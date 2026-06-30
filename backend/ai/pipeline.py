"""
AI Pipeline — per-camera background threads.

Design:
  - One thread per camera, polling RTSP at ~1 FPS.
  - Runs: people counting (YOLOv8) + face recognition (InsightFace) + emotion (DeepFace).
  - Suppression: if a camera delivers native ONVIF AI events, local AI is suspended for
    NATIVE_AI_SUPPRESS_WINDOW seconds to avoid double-counting.
  - Unknown face flow: no match → check active visitors → emit event type accordingly.
  - All events written to the shared Event table via crud (same schema as camera polling events).
"""

import time
import json
import threading
import datetime
import os
from typing import Optional

import cv2
import numpy as np

FACE_THRESHOLD = float(os.getenv("FACE_MATCH_THRESHOLD", "0.50"))
AI_FPS = float(os.getenv("AI_PIPELINE_FPS", "1.0"))
NATIVE_AI_SUPPRESS_WINDOW = int(os.getenv("NATIVE_AI_SUPPRESS_WINDOW", "60"))

# {camera_id: monotonic timestamp of last native AI event}
_native_ts: dict[int, float] = {}
_native_lock = threading.Lock()

_threads: dict[int, threading.Thread] = {}
_stop_flags: dict[int, threading.Event] = {}


# ── Public API ─────────────────────────────────────────────────────────────────

def notify_native_ai_event(camera_id: int) -> None:
    """Called by the ONVIF polling loop when a face/people event arrives natively."""
    with _native_lock:
        _native_ts[camera_id] = time.monotonic()


def start_camera_ai(camera_id: int, ip: str, username: str, password: str, db_factory) -> None:
    """Start AI thread for a camera. Idempotent — does nothing if already running."""
    if camera_id in _threads and _threads[camera_id].is_alive():
        return
    stop = threading.Event()
    _stop_flags[camera_id] = stop
    t = threading.Thread(
        target=_ai_loop,
        args=(camera_id, ip, username, password, db_factory, stop),
        daemon=True,
        name=f"ai-cam-{camera_id}",
    )
    _threads[camera_id] = t
    t.start()
    print(f"[AI] Pipeline started for camera {camera_id} @ {ip}")


def stop_camera_ai(camera_id: int) -> None:
    """Signal the AI thread for a camera to stop."""
    flag = _stop_flags.get(camera_id)
    if flag:
        flag.set()


def sync_cameras(cameras: list, db_factory) -> None:
    """
    Called periodically by main.py.
    Starts threads for new cameras, stops threads for cameras removed from DB.
    """
    active_ids = {cam.id for cam in cameras}

    for cam_id in list(_threads.keys()):
        if cam_id not in active_ids:
            stop_camera_ai(cam_id)
            _threads.pop(cam_id, None)
            _stop_flags.pop(cam_id, None)

    for cam in cameras:
        start_camera_ai(cam.id, cam.ip_address, cam.username, cam.password, db_factory)


# ── Internal ───────────────────────────────────────────────────────────────────

def _is_suppressed(camera_id: int) -> bool:
    with _native_lock:
        ts = _native_ts.get(camera_id)
    return ts is not None and (time.monotonic() - ts) < NATIVE_AI_SUPPRESS_WINDOW


def _open_rtsp(ip: str, username: str, password: str) -> Optional[cv2.VideoCapture]:
    os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp|stimeout;3000000"
    for url in [
        f"rtsp://{username}:{password}@{ip}:554/cam/realmonitor?channel=1&subtype=1",
        f"rtsp://{username}:{password}@{ip}:554/cam/realmonitor?channel=1&subtype=0",
    ]:
        cap = cv2.VideoCapture(url)
        if cap.isOpened():
            return cap
    return None


def _ai_loop(
    camera_id: int,
    ip: str,
    username: str,
    password: str,
    db_factory,
    stop: threading.Event,
) -> None:
    interval = 1.0 / max(AI_FPS, 0.1)
    cap: Optional[cv2.VideoCapture] = None

    while not stop.is_set():
        if _is_suppressed(camera_id):
            time.sleep(5)
            continue

        if cap is None or not cap.isOpened():
            cap = _open_rtsp(ip, username, password)
            if cap is None:
                time.sleep(15)
                continue

        ret, frame = cap.read()
        if not ret:
            cap.release()
            cap = None
            time.sleep(5)
            continue

        t0 = time.monotonic()
        try:
            _process_frame(camera_id, frame, db_factory)
        except Exception as e:
            print(f"[AI] camera {camera_id} processing error: {e}")

        elapsed = time.monotonic() - t0
        remaining = interval - elapsed
        if remaining > 0:
            stop.wait(timeout=remaining)

    if cap:
        cap.release()
    print(f"[AI] Pipeline stopped for camera {camera_id}")


def _process_frame(camera_id: int, frame: np.ndarray, db_factory) -> None:
    from ai.people_counter import count_persons
    from ai.face_recognizer import extract_faces, match_person
    from ai.emotion_detector import detect_emotion
    import crud
    import schemas

    db = db_factory()
    try:
        # ── 1. People counting ──────────────────────────────────────────────────
        count, bboxes = count_persons(frame)
        if count > 0:
            crud.create_event(
                db,
                schemas.EventCreate(
                    event_type="people_count",
                    event_data=json.dumps({"count": count, "bboxes": bboxes}),
                ),
                camera_id=camera_id,
            )

        # ── 2. Face recognition + emotion ───────────────────────────────────────
        persons_db = crud.get_persons_with_face_encoding(db)
        detected = extract_faces(frame)
        device = crud.get_access_device_by_camera(db, camera_id)

        for face in detected:
            embedding = face["embedding"]
            bbox = face["bbox"]
            face_crop = _crop_face(frame, bbox)

            matched, confidence = match_person(embedding, persons_db)

            if matched and confidence >= FACE_THRESHOLD:
                emotion = detect_emotion(face_crop)
                crud.create_event(
                    db,
                    schemas.EventCreate(
                        event_type="face_recognized",
                        event_data=json.dumps({
                            "person_id": matched.id,
                            "person_name": matched.name,
                            "confidence": round(confidence, 3),
                            "emotion": emotion,
                            "bbox": bbox,
                        }),
                    ),
                    camera_id=camera_id,
                )
                # Fase 4: se há dispositivo vinculado a esta câmera, processar acesso
                if device:
                    import access_control
                    access_control.handle_face_access(
                        db=db, person=matched, device=device,
                        confidence=confidence, camera_id=camera_id,
                    )
            else:
                # Unknown face — check if any active visitor is registered
                active_visitors = crud.get_active_visitors(db)
                event_type = "visitor_detected" if active_visitors else "unknown_face"
                emotion = detect_emotion(face_crop)
                face_path = _save_face_crop(face_crop, camera_id)

                crud.create_event(
                    db,
                    schemas.EventCreate(
                        event_type=event_type,
                        event_data=json.dumps({
                            "confidence": round(confidence, 3),
                            "emotion": emotion,
                            "bbox": bbox,
                            "active_visitors": len(active_visitors),
                            "device_id": device.id if device else None,
                        }),
                        face_image_path=face_path,
                    ),
                    camera_id=camera_id,
                )
    finally:
        db.close()


def _crop_face(frame: np.ndarray, bbox: list) -> np.ndarray:
    x1, y1, x2, y2 = (max(0, int(v)) for v in bbox)
    if x2 <= x1 or y2 <= y1:
        return frame
    return frame[y1:y2, x1:x2]


def _save_face_crop(face_img: np.ndarray, camera_id: int) -> Optional[str]:
    if face_img is None or face_img.size == 0:
        return None
    try:
        ts = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"unknown_cam{camera_id}_{ts}.jpg"
        path = os.path.join("face_images", filename)
        cv2.imwrite(path, face_img)
        return filename
    except Exception:
        return None
