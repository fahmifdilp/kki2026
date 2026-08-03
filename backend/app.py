import asyncio, json, logging, math, time
from contextlib import asynccontextmanager, suppress
from datetime import datetime, timezone
from pathlib import Path
import yaml
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from .camera import CameraFeed
from .detector import BuoyDetector
from .models import Telemetry, RouteSelection, default_telemetry
from .settings import settings

logging.basicConfig(level=logging.INFO,format="%(asctime)s | %(levelname)s | %(message)s"); log=logging.getLogger("trifusion")
with open(settings.detection_config_path,encoding="utf-8") as f: detection_config=yaml.safe_load(f)
with open(settings.routes_config_path,encoding="utf-8") as f: routes=json.load(f)["routes"]
detector=BuoyDetector(detection_config); cameras={"main":CameraFeed("main",settings.main_camera_source,settings.simulation_mode,detector),"underwater":CameraFeed("underwater",settings.underwater_camera_source,settings.simulation_mode,detector)}
telemetry=default_telemetry(); active_route="A"; clients=set(); started=time.monotonic(); simulation_task=None

def is_online(data=None):
    value=data or telemetry
    return value.connected and (datetime.now(timezone.utc)-value.heartbeat_at).total_seconds() <= settings.heartbeat_timeout_seconds

async def broadcast():
    payload=json.dumps(telemetry.model_dump(mode="json")|{"connected":is_online()})
    for ws in list(clients):
        try: await ws.send_text(payload)
        except Exception: clients.discard(ws)

async def simulate():
    global telemetry
    n=0
    while True:
        n+=1; now=datetime.now(timezone.utc); base=telemetry.model_dump()
        base.update({"connected":True,"heading_deg":(32+n*1.8)%360,"speed_mps":1.8+.25*math.sin(n/5),"front_distance_cm":470+80*math.sin(n/3),"battery_percent":max(10,92-n*.002),"packet_loss_percent":max(0,1.5+math.sin(n/4)),"heartbeat_at":now})
        base["position"]={"latitude":3.5952+n*.000002,"longitude":98.6722+n*.000003,"captured_at":now}
        telemetry=Telemetry.model_validate(base); await broadcast(); await asyncio.sleep(1)

@asynccontextmanager
async def lifespan(app):
    global simulation_task
    if settings.simulation_mode: simulation_task=asyncio.create_task(simulate())
    log.info("TRIFUSION backend started | simulation=%s",settings.simulation_mode); yield
    if simulation_task: simulation_task.cancel();
    with suppress(asyncio.CancelledError):
        if simulation_task: await simulation_task

app=FastAPI(title="TRIFUSION API",version="1.0.0",lifespan=lifespan)
app.add_middleware(CORSMiddleware,allow_origins=[settings.frontend_origin,"http://127.0.0.1:5173"],allow_methods=["*"],allow_headers=["*"])

@app.get("/health")
def health(): return {"status":"ok","simulation":settings.simulation_mode}
@app.get("/api/system/status")
def status(): return {"status":"Simulation" if settings.simulation_mode else ("Online" if is_online() else "Offline"),"uptime_seconds":int(time.monotonic()-started),"cameras":{k:{"online":v.online} for k,v in cameras.items()}}
@app.get("/api/telemetry")
def get_telemetry(): return telemetry.model_dump(mode="json")|{"connected":is_online()}
@app.post("/api/telemetry")
async def post_telemetry(data:Telemetry):
    global telemetry; telemetry=data; await broadcast(); return telemetry
@app.get("/api/routes")
def get_routes(): return {"routes":routes}
@app.get("/api/routes/active")
def get_active(): return {"route_id":active_route}
@app.post("/api/routes/active")
def set_active(data:RouteSelection):
    global active_route; active_route=data.route_id; return {"route_id":active_route}
@app.get("/api/detection/config")
def get_detection_config(): return detection_config
@app.put("/api/detection/config")
def put_detection_config(config:dict):
    required={"red_hsv_1","red_hsv_2","green_hsv","minimum_area","minimum_circularity","minimum_radius","roi","smoothing_factor","detection_enabled"}
    if not required.issubset(config): raise HTTPException(422,detail={"code":"invalid_detection_config","message":"Konfigurasi tidak lengkap"})
    detection_config.clear(); detection_config.update(config); detector.update(detection_config)
    with open(settings.detection_config_path,"w",encoding="utf-8") as f: yaml.safe_dump(config,f,sort_keys=False)
    return detection_config
@app.get("/api/cameras/{camera_id}/detections")
def get_detections(camera_id:str):
    if camera_id not in cameras: raise HTTPException(404,detail={"code":"camera_not_found","message":"Kamera tidak ditemukan"})
    return cameras[camera_id].last_detection
@app.get("/api/cameras/{camera_id}/stream")
def stream(camera_id:str):
    if camera_id not in cameras: raise HTTPException(404,detail={"code":"camera_not_found","message":"Kamera tidak ditemukan"})
    return StreamingResponse(cameras[camera_id].stream(),media_type="multipart/x-mixed-replace; boundary=frame")
@app.websocket("/ws/telemetry")
async def websocket(ws:WebSocket):
    await ws.accept(); clients.add(ws)
    try:
        await ws.send_json(telemetry.model_dump(mode="json")|{"connected":is_online()})
        while True: await ws.receive_text()
    except WebSocketDisconnect: clients.discard(ws)
