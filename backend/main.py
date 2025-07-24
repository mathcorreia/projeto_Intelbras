import time
import threading
import cv2
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from starlette.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .database import models, core
from .adapters import bronze_adapter, onvif_adapter
from . import crud, schemas

models.Base.metadata.create_all(bind=core.engine)
app = FastAPI()
app.mount("/faces", StaticFiles(directory="face_images"), name="faces")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ADAPTER_MAP = {"bronze": bronze_adapter.BronzeCameraAdapter,"onvif": onvif_adapter.OnvifAdapter}

def get_db():
    db = core.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/cameras/", response_model=schemas.Camera)
def create_camera(camera: schemas.CameraCreate, db: Session = Depends(get_db)):
    return crud.create_camera(db=db, camera=camera)

@app.get("/cameras/", response_model=list[schemas.Camera])
def read_cameras(db: Session = Depends(get_db)):
    return crud.get_cameras(db)

@app.get("/cameras/{camera_id}", response_model=schemas.Camera)
def read_camera(camera_id: int, db: Session = Depends(get_db)):
    db_camera = crud.get_camera(db, camera_id=camera_id)
    if db_camera is None:
        raise HTTPException(status_code=404, detail="Camera not found")
    return db_camera

@app.get("/events/{camera_id}", response_model=list[schemas.Event])
def read_events(camera_id: int, db: Session = Depends(get_db)):
    return crud.get_events_for_camera(db, camera_id=camera_id)

# =================================================================
# LÓGICA DE VÍDEO REATIVADA
# =================================================================
def generate_frames(camera_ip, username, password):
    # ATENÇÃO: Verifique se este formato de URL RTSP é o correto para o seu modelo de câmara Intelbras.
    rtsp_url = f"rtsp://{username}:{password}@{camera_ip}:554/cam/realmonitor?channel=1&subtype=0"

    cap = cv2.VideoCapture(rtsp_url)
    if not cap.isOpened():
        print(f"ERRO: Não foi possível abrir o stream RTSP em {rtsp_url}")

    while True:
        success, frame = cap.read()
        if not success:
            print(f"Falha ao ler frame do stream RTSP em {camera_ip}. A tentar reconectar...")
            time.sleep(5)
            cap.release()
            cap.open(rtsp_url)
            continue
        else:
            _, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.get("/video_feed/{camera_id}")
def video_feed(camera_id: int, db: Session = Depends(get_db)):
    camera = crud.get_camera(db, camera_id=camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    return StreamingResponse(generate_frames(camera.ip_address, camera.username, camera.password), media_type='multipart/x-mixed-replace; boundary=frame')

def poll_camera_events(db_session_factory):
    while True:
        db = db_session_factory()
        cameras = crud.get_cameras(db)
        for cam in cameras:
            Adapter = ADAPTER_MAP.get(cam.camera_type, bronze_adapter.BronzeCameraAdapter)
            adapter_instance = Adapter(cam.ip_address, cam.username, cam.password)
            events = adapter_instance.get_events()
            for event_data in events:
                event = schemas.EventCreate(**event_data)
                crud.create_event(db, event=event, camera_id=cam.id)
        db.close()
        time.sleep(10)

# Deixamos a thread de eventos de IA comentada por agora para focar no vídeo
polling_thread = threading.Thread(target=poll_camera_events, args=(core.SessionLocal,), daemon=True)
polling_thread.start()