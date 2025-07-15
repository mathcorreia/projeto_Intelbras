from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import threading
import time
import cv2
from fastapi.responses import StreamingResponse

from .database import crud, models, schemas
from .database.database import SessionLocal, engine
from adapters import bronze_adapter, silver_adapter, gold_adapter # Importando os adaptadores

# Cria as tabelas no banco de dados
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Mapeamento de adaptadores
ADAPTER_MAP = {
    "bronze": bronze_adapter.BronzeCameraAdapter,
    "silver": silver_adapter.SilverCameraAdapter,
    "gold": gold_adapter.GoldCameraAdapter,
}
camera_threads = {}

# Dependência para obter a sessão do banco de dados
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def poll_camera_events(camera_id: int, ip_address: str, level: str):
    adapter_class = ADAPTER_MAP.get(level)
    if not adapter_class:
        print(f"Nenhum adaptador encontrado para o nível: {level}")
        return
    
    # Simula usuário e senha
    adapter = adapter_class(ip_address, "admin", "admin")
    
    print(f"Iniciando monitoramento para a câmera {camera_id} (Nível: {level})")
    while camera_id in camera_threads:
        events = adapter.get_events()
        if events:
            db = SessionLocal()
            for event in events:
                print(f"Novo evento da câmera {camera_id}: {event}")
                crud.create_event(db, event_data=event, camera_id=camera_id)
            db.close()
        time.sleep(5) # Poll a cada 5 segundos

@app.on_event("startup")
def load_cameras_on_startup():
    db = SessionLocal()
    cameras = crud.get_cameras(db)
    for cam in cameras:
        thread = threading.Thread(
            target=poll_camera_events, 
            args=(cam.id, cam.ip_address, cam.level),
            daemon=True
        )
        camera_threads[cam.id] = thread
        thread.start()
    db.close()

@app.post("/cameras/", response_model=schemas.Camera)
def create_camera_endpoint(camera: schemas.CameraCreate, db: Session = Depends(get_db)):
    db_camera = crud.create_camera(db=db, camera=camera)
    thread = threading.Thread(
        target=poll_camera_events, 
        args=(db_camera.id, db_camera.ip_address, db_camera.level),
        daemon=True
    )
    camera_threads[db_camera.id] = thread
    thread.start()
    return db_camera

@app.get("/cameras/", response_model=List[schemas.Camera])
def read_cameras(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    cameras = crud.get_cameras(db, skip=skip, limit=limit)
    return cameras

@app.get("/events/{camera_id}", response_model=List[schemas.Event])
def read_events_for_camera(camera_id: int, db: Session = Depends(get_db)):
    camera = crud.get_camera(db, camera_id=camera_id)
    if camera is None:
        raise HTTPException(status_code=404, detail="Câmera não encontrada")
    return camera.events[-10:] # Retorna os últimos 10 eventos

def generate_video_frames(camera_ip: str):
    # Neste exemplo, vamos gerar um vídeo falso para não depender de uma câmera real
    # Para uma câmera real, use: cap = cv2.VideoCapture(f"rtsp://user:pass@{camera_ip}...")
    
    # Vídeo Falso de Simulação
    while True:
        frame = cv2.imread('placeholder.jpg') # Crie uma imagem placeholder.jpg no dir do backend
        if frame is None: # Se a imagem não existir, cria uma preta
            frame = cv2.UMat(480, 640, cv2.CV_8UC3).get()
            cv2.putText(frame, f"Simulando Camera: {camera_ip}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
        (flag, encodedImage) = cv2.imencode(".jpg", frame)
        if not flag:
            continue
        yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + bytearray(encodedImage) + b'\r\n')
        time.sleep(0.1) # Limita o framerate

@app.get("/video_feed/{camera_id}")
def video_feed(camera_id: int, db: Session = Depends(get_db)):
    camera = crud.get_camera(db, camera_id=camera_id)
    if camera is None:
        raise HTTPException(status_code=404, detail="Câmera não encontrada")
    return StreamingResponse(generate_video_frames(camera.ip_address),
                    media_type='multipart/x-mixed-replace; boundary=frame')