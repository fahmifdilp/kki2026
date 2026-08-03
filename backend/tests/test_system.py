from datetime import datetime, timedelta, timezone
import cv2, numpy as np, pytest, yaml
from fastapi.testclient import TestClient
from backend.detector import BuoyDetector
from backend.navigation import NavigationGuide
from backend.models import Telemetry, default_telemetry
from backend.app import app, is_online

@pytest.fixture
def detector():
    with open("backend/config/detection.yaml") as f: return BuoyDetector(yaml.safe_load(f))

@pytest.mark.parametrize("hue,color",[(0,"red"),(179,"red"),(60,"green")])
def test_detect_synthetic_circle(detector,hue,color):
    hsv=np.zeros((300,400,3),np.uint8); cv2.circle(hsv,(200,150),35,(hue,255,255),-1); frame=cv2.cvtColor(hsv,cv2.COLOR_HSV2BGR)
    result=detector.detect(frame,"main")
    assert any(d["color"]==color and abs(d["center_x"]-200)<3 for d in result["detections"])

def test_small_noise_rejected(detector):
    frame=np.zeros((300,400,3),np.uint8); cv2.circle(frame,(200,150),3,(0,0,255),-1)
    assert detector.detect(frame,"main")["detections"]==[]

def test_navigation_corridor_and_limited():
    nav=NavigationGuide(1); r={"center_x":100,"center_y":80}; g={"center_x":300,"center_y":100}
    assert nav.calculate(r,g).target==(200,90)
    assert nav.calculate(r,None).status=="Panduan Terbatas"

def test_telemetry_validation_and_offline():
    data=default_telemetry().model_dump(); data["battery_percent"]=101
    with pytest.raises(Exception): Telemetry.model_validate(data)
    old=default_telemetry(); old.heartbeat_at=datetime.now(timezone.utc)-timedelta(seconds=20)
    assert not is_online(old)

def test_route_selection():
    with TestClient(app) as client:
        for route in ("A","B"):
            assert client.post("/api/routes/active",json={"route_id":route}).json()["route_id"]==route
        assert client.post("/api/routes/active",json={"route_id":"C"}).status_code==422
