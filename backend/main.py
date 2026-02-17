import time
import threading
import cv2
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from starlette.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from database import models, core
from adapters import bronze_adapter, onvif_adapter, intelbras_adapter
import crud
import schemas
import os

# Cria tabelas na BD
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

ADAPTER_MAP = {
    "bronze": bronze_adapter.BronzeCameraAdapter,
    "onvif": onvif_adapter.OnvifAdapter, 
    "intelbras": intelbras_adapter.IntelbrasAdapter
}

def get_db():
    db = core.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- ROTAS DE CÂMARAS ---

@app.post("/cameras/", response_model=schemas.Camera)
def create_camera(camera: schemas.CameraCreate, db: Session = Depends(get_db)):
    return crud.create_camera(db=db, camera=camera)

@app.delete("/cameras/{camera_id}")
def remove_camera(camera_id: int, db: Session = Depends(get_db)):
    success = crud.delete_camera(db, camera_id=camera_id)
    if not success:
        raise HTTPException(status_code=404, detail="Camera not found")
    return {"message": "Camera deleted successfully"}
@app.put("/cameras/{camera_id}", response_model=schemas.Camera)
def update_camera_endpoint(camera_id: int, camera: schemas.CameraCreate, db: Session = Depends(get_db)):
    db_camera = crud.update_camera(db, camera_id=camera_id, camera_data=camera)
    if db_camera is None:
        raise HTTPException(status_code=404, detail="Camera not found")
    return db_camera

@app.get("/cameras/", response_model=list[schemas.Camera])
def read_cameras(db: Session = Depends(get_db)):
    return crud.get_cameras(db)

@app.get("/cameras/{camera_id}", response_model=schemas.Camera)
def read_camera(camera_id: int, db: Session = Depends(get_db)):
    db_camera = crud.get_camera(db, camera_id=camera_id)
    if db_camera is None:
        raise HTTPException(status_code=404, detail="Camera not found")
    return db_camera

# --- ROTAS DE EVENTOS (Correção Importante) ---

# 1. Eventos Gerais (Para a página de Logs e Polling da Dashboard)
@app.get("/events/", response_model=list[schemas.Event])
def read_all_events(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    events = db.query(models.Event).order_by(models.Event.timestamp.desc()).offset(skip).limit(limit).all()
    return events

# 2. Eventos de UMA Câmara (Faltava esta rota no teu código anterior!)
@app.get("/events/{camera_id}", response_model=list[schemas.Event])
def read_events(camera_id: int, db: Session = Depends(get_db)):
    return crud.get_events_for_camera(db, camera_id=camera_id)

# --- VÍDEO OTIMIZADO ---

def generate_frames(camera_ip, username, password):
    # --- OTIMIZAÇÃO CRÍTICA ---
    # Define um timeout de 3 segundos (3000000 microssegundos)
    # Força transporte TCP (mais estável para web e evita artefactos cinzentos)
    os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp|stimeout;3000000"

    # URLs
    rtsp_sub = f"rtsp://{username}:{password}@{camera_ip}:554/cam/realmonitor?channel=1&subtype=1"
    rtsp_main = f"rtsp://{username}:{password}@{camera_ip}:554/cam/realmonitor?channel=1&subtype=0"

    print(f"[{camera_ip}] A tentar conexão rápida (Sub-stream)...")
    cap = cv2.VideoCapture(rtsp_sub)
    
    # Se falhar ou não abrir em 3 segundos, troca imediatamente
    if not cap.isOpened():
        print(f"[{camera_ip}] Sub-stream falhou ou demorou. Trocando para Main-stream...")
        cap = cv2.VideoCapture(rtsp_main)

    if not cap.isOpened():
        print(f"ERRO CRÍTICO: Não foi possível conectar a {camera_ip}")
        return

    # print(f"[{camera_ip}] Conexão de vídeo estabelecida!") 

    while True:
        success, frame = cap.read()
        if not success:
            # Se perder conexão, tenta reconectar
            # print(f"[{camera_ip}] Frame perdido. A reconectar...")
            time.sleep(2) 
            cap.release()
            
            # Tenta recuperar o sub-stream primeiro
            cap.open(rtsp_sub)
            if not cap.isOpened():
                cap.open(rtsp_main)
            continue
        else:
            try:
                # Mantém o resize para 640px para performance
                height, width = frame.shape[:2]
                new_width = 640
                if width > new_width:
                    scaling_factor = new_width / float(width)
                    new_height = int(height * scaling_factor)
                    frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)

                ret, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 50])
                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            except Exception:
                continue

@app.get("/video_feed/{camera_id}")
def video_feed(camera_id: int, db: Session = Depends(get_db)):
    camera = crud.get_camera(db, camera_id=camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    return StreamingResponse(
        generate_frames(camera.ip_address, camera.username, camera.password), 
        media_type='multipart/x-mixed-replace; boundary=frame'
    )

# --- POLLING DE EVENTOS ---

def poll_camera_events(db_session_factory):
    while True:
        try:
            db = db_session_factory()
            cameras = crud.get_cameras(db)
            for cam in cameras:
                try:
                    Adapter = ADAPTER_MAP.get(cam.camera_type, bronze_adapter.BronzeCameraAdapter)
                    adapter_instance = Adapter(cam.ip_address, cam.username, cam.password)
                    
                    events = adapter_instance.get_events()
                    
                    for event_data in events:
                        event = schemas.EventCreate(**event_data)
                        crud.create_event(db, event=event, camera_id=cam.id)
                except Exception as e:
                    print(f"Erro ao ler eventos da câmara {cam.ip_address}: {e}")
            db.close()
        except Exception as e:
            print(f"Erro na thread de polling: {e}")
            
        time.sleep(10)

polling_thread = threading.Thread(target=poll_camera_events, args=(core.SessionLocal,), daemon=True)
polling_thread.start()