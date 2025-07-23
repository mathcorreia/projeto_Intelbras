import time
import threading
import cv2
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from starlette.middleware.cors import CORSMiddleware

# Importações locais
from database import models, database
from adapters import bronze_adapter, onvif_adapter
import crud, schemas

# Cria as tabelas no banco de dados
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

# Permite que o frontend Angular acesse a API
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
}

# Função para obter a sessão do banco de dados
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Endpoints da API ---

@app.post("/cameras/", response_model=schemas.Camera)
def create_camera(camera: schemas.CameraCreate, db: Session = Depends(get_db)):
    return crud.create_camera(db=db, camera=camera)

@app.get("/cameras/", response_model=list[schemas.Camera])
def read_cameras(db: Session = Depends(get_db)):
    return crud.get_cameras(db)

@app.get("/events/{camera_id}", response_model=list[schemas.Event])
def read_events(camera_id: int, db: Session = Depends(get_db)):
    return crud.get_events_for_camera(db, camera_id=camera_id)

def generate_frames(camera_ip, username, password):
    # URL do stream RTSP. O formato pode variar com o modelo da câmera.
    rtsp_url = f"rtsp://{username}:{password}@{camera_ip}:554/cam/realmonitor?channel=1&subtype=0"
    cap = cv2.VideoCapture(rtsp_url)
    while True:
        success, frame = cap.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.get("/video_feed/{camera_id}")
def video_feed(camera_id: int, db: Session = Depends(get_db)):
    camera = crud.get_camera(db, camera_id=camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    return StreamingResponse(generate_frames(camera.ip_address, camera.username, camera.password), 
                             media_type='multipart/x-mixed-replace; boundary=frame')

# --- Lógica de Polling em Background ---

def poll_camera_events(db_session_factory):
    while True:
        db = db_session_factory()
        cameras = crud.get_cameras(db)
        for cam in cameras:
            Adapter = ADAPTER_MAP.get(cam.camera_type, bronze_adapter.BronzeCameraAdapter)
            adapter_instance = Adapter(cam.ip_address, cam.username, cam.password)
            events = adapter_instance.get_events()
            for event_data in events:
                event = schemas.EventCreate(event_type=event_data['type'])
                crud.create_event(db, event=event, camera_id=cam.id)
        db.close()
        time.sleep(10) # Espera 10 segundos para a próxima verificação

# Inicia o polling em uma thread separada
polling_thread = threading.Thread(target=poll_camera_events, args=(database.SessionLocal,), daemon=True)
polling_thread.start()