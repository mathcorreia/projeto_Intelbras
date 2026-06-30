import time
from datetime import datetime, timedelta
import threading
import cv2
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from starlette.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from adapters.mibo_driver import MiboDriver
from adapters.alarm.tcp_receiver import AlarmTCPReceiver
from database import models, core
from adapters import bronze_adapter, onvif_adapter, intelbras_adapter, mibo_driver
from routes import persons, visitors, alarms, access, gates, guarita
from auth.jwt_middleware import get_current_tenant_id
import ai.pipeline as ai_pipeline
import crud
import schemas
import os

# Cria tabelas na BD
models.Base.metadata.create_all(bind=core.engine)

app = FastAPI(title="Koreon Tech Monitoring API", version="1.0.0")

os.makedirs("face_images", exist_ok=True)
app.mount("/faces", StaticFiles(directory="face_images"), name="faces")

_CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:4200").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", tags=["health"])
def health():
    return {"status": "ok", "service": "koreon-backend", "version": "1.0.0"}


# --- Routers por domínio ---
app.include_router(persons.router)
app.include_router(visitors.router)
app.include_router(alarms.router)
app.include_router(access.router)
app.include_router(gates.router)
app.include_router(guarita.router)

# --- Servidor TCP de alarmes (Contact ID) ---
ALARM_TCP_PORT = int(os.getenv("ALARM_TCP_PORT", "9009"))
_alarm_receiver = AlarmTCPReceiver(host="0.0.0.0", port=ALARM_TCP_PORT)
_alarm_thread = threading.Thread(target=_alarm_receiver.start, daemon=True, name="alarm-tcp")
_alarm_thread.start()

# --- Sync do pipeline de IA (inicia/para threads conforme câmeras cadastradas) ---
def _ai_sync_loop(db_factory):
    while True:
        try:
            db = db_factory()
            cameras = crud.get_cameras(db)
            db.close()
            ai_pipeline.sync_cameras(cameras, db_factory)
        except Exception as e:
            print(f"[AI sync] error: {e}")
        time.sleep(30)

threading.Thread(target=_ai_sync_loop, args=(core.SessionLocal,), daemon=True, name="ai-sync").start()

ADAPTER_MAP = {
    "bronze": bronze_adapter.BronzeCameraAdapter,
    "onvif": onvif_adapter.OnvifAdapter, 
    "intelbras": intelbras_adapter.IntelbrasAdapter,
    "mibo": mibo_driver.MiboDriver
}

def get_db():
    db = core.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- ROTAS DE CÂMARAS ---

@app.post("/cameras/", response_model=schemas.Camera)
def create_camera(
    camera: schemas.CameraCreate,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_current_tenant_id),
):
    return crud.create_camera(db=db, camera=camera, tenant_id=tenant_id)

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
def read_cameras(
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_current_tenant_id),
):
    return crud.get_cameras(db, tenant_id=tenant_id)

@app.get("/cameras/{camera_id}", response_model=schemas.Camera)
def read_camera(camera_id: int, db: Session = Depends(get_db)):
    db_camera = crud.get_camera(db, camera_id=camera_id)
    if db_camera is None:
        raise HTTPException(status_code=404, detail="Camera not found")
    return db_camera

@app.get("/cameras/{camera_id}/mibo/audio")
def get_camera_audio_config(camera_id: int, db: Session = Depends(get_db)):
    camera = crud.get_camera(db, camera_id=camera_id)
    if not camera or camera.camera_type not in ["mibo", "intelbras"]:
        raise HTTPException(status_code=400, detail="Câmara inválida ou não suporta configs avançadas")
    
    driver = mibo_driver.MiboDriver(camera.ip_address, camera.username, camera.password)
    config = driver.get_audio_config()
    return {"audio_config": config}

# Rota do Volume Corrigida (Cuidado com o int() para evitar o erro 500)
# Rota do Volume - Elegante e à prova de falhas
@app.post("/cameras/{camera_id}/mibo/audio/volume")
def set_camera_volume(camera_id: int, payload: dict, db: Session = Depends(get_db)):
    volume = int(payload.get("volume", 50))
    camera = crud.get_camera(db, camera_id=camera_id)
    if not camera: raise HTTPException(status_code=404, detail="Câmara não encontrada")
    
    driver = mibo_driver.MiboDriver(camera.ip_address, camera.username, camera.password)
    success = driver.set_audio_volume(volume)
    
    if not success:
        # A câmara recusou, mas não damos erro 500 para não quebrar o Frontend
        return {"message": "Aviso: Hardware bloqueia controlo de volume externo", "success": False}
        
    return {"message": f"Volume alterado para {volume}%", "success": True}


# Rota do Switch Liga/Desliga - Elegante e à prova de falhas
@app.post("/cameras/{camera_id}/mibo/audio/toggle")
def toggle_camera_audio(camera_id: int, payload: dict, db: Session = Depends(get_db)):
    enable = payload.get("enable", True)
    camera = crud.get_camera(db, camera_id=camera_id)
    if not camera: raise HTTPException(status_code=404, detail="Câmara não encontrada")

    driver = mibo_driver.MiboDriver(camera.ip_address, camera.username, camera.password)
    success = driver.toggle_microphone(enable)
    
    if not success:
        return {"message": "Aviso: Hardware bloqueia controlo de áudio externo", "success": False}
        
    return {"message": f"Áudio {'ligado' if enable else 'desligado'}", "success": True}

@app.get("/cameras/{camera_id}/system-logs")
def get_device_logs(camera_id: int, db: Session = Depends(get_db)):
    camera = crud.get_camera(db, camera_id=camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail="Câmara não encontrada")
        
    if camera.camera_type not in ["mibo", "intelbras"]:
        raise HTTPException(status_code=400, detail="Este adaptador não suporta extração de logs do hardware")
    
    # Prepara as datas (últimas 24 horas)
    end_time = datetime.now()
    start_time = end_time - timedelta(days=1)
    start_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
    end_str = end_time.strftime("%Y-%m-%d %H:%M:%S")
    
    logs = []
    
    # Direciona para o adaptador correto
    if camera.camera_type == "mibo":
        driver = mibo_driver.MiboDriver(camera.ip_address, camera.username, camera.password)
        logs = driver.get_system_logs(start_str, end_str)
        
    elif camera.camera_type == "intelbras":
        adapter = intelbras_adapter.IntelbrasAdapter(camera.ip_address, camera.username, camera.password)
        logs = adapter.get_system_logs(start_str, end_str)
        
    return {"logs": logs}

@app.post("/cameras/{camera_id}/ptz")
def control_ptz(camera_id: int, payload: dict, db: Session = Depends(get_db)):
    # 1. Conexão "Flutuante": Vai buscar os dados da câmara à Base de Dados
    camera = crud.get_camera(db, camera_id=camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail="Câmara não encontrada")
    
    # 2. Bloqueio de segurança (só executa em câmaras compatíveis)
    if camera.camera_type not in ["mibo", "intelbras"]:
        raise HTTPException(status_code=400, detail="Esta câmara não suporta PTZ")

    # 3. Extrai os comandos enviados pelo Angular
    direction = payload.get('direction') # Ex: "Left"
    action = payload.get('action')       # Ex: "start"

    # 4. Injeta as credenciais dinâmicas no Driver
    # (A password lida do DB será o Código de Segurança da etiqueta da Mibo)
    driver = mibo_driver.MiboDriver(
        ip=camera.ip_address, 
        username=camera.username, 
        password=camera.password
    )
    
    # 5. Executa o movimento
    success = driver.move_ptz(direction=direction, action=action)
    
    if not success:
        raise HTTPException(status_code=500, detail="Falha ao comunicar com os motores da câmara")
        
    return {"message": f"PTZ {direction} {action} executado com sucesso."}

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
                        # Supprime IA local para câmeras que entregam eventos nativos de IA
                        if event_data.get("event_type") in ("face_recognized", "face_detection", "people_count"):
                            ai_pipeline.notify_native_ai_event(cam.id)
                except Exception as e:
                    print(f"Erro ao ler eventos da câmara {cam.ip_address}: {e}")
            db.close()
        except Exception as e:
            print(f"Erro na thread de polling: {e}")
            
        time.sleep(10)

polling_thread = threading.Thread(target=poll_camera_events, args=(core.SessionLocal,), daemon=True)
polling_thread.start()