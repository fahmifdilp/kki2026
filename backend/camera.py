import threading, time
import cv2
import numpy as np
from .navigation import NavigationGuide

def parse_source(value): return int(value) if str(value).strip().isdigit() else value

class CameraFeed:
    def __init__(self, camera_id, source, simulation, detector):
        self.camera_id=camera_id; self.source=parse_source(source); self.simulation=simulation; self.detector=detector
        self.guide=NavigationGuide(detector.config["smoothing_factor"]); self.online=simulation; self.last_detection={"camera_id":camera_id,"detections":[]}; self._cap=None; self._lock=threading.Lock()

    def _simulation_frame(self):
        frame=np.full((540,960,3),(34,43,48),np.uint8); t=time.time(); shift=int(35*np.sin(t*.55))
        cv2.rectangle(frame,(0,300),(960,540),(105,76,45),-1); cv2.circle(frame,(340+shift,240),34,(0,0,245),-1); cv2.circle(frame,(620+shift,230),32,(0,220,30),-1)
        cv2.putText(frame,"TRIFUSION // SIMULATION",(28,42),cv2.FONT_HERSHEY_SIMPLEX,.7,(240,240,240),2); return frame

    def _read(self):
        if self.simulation: self.online=True; return self._simulation_frame()
        if self._cap is None or not self._cap.isOpened(): self._cap=cv2.VideoCapture(self.source)
        ok,frame=self._cap.read(); self.online=bool(ok)
        if not ok: return np.full((540,960,3),(34,34,34),np.uint8)
        return frame

    def jpeg(self):
        with self._lock:
            frame=self._read(); result=self.detector.detect(frame,self.camera_id); self.last_detection=result
            for d in result["detections"]:
                c=(50,60,245) if d["color"]=="red" else (60,220,90); b=d["bbox"]
                cv2.rectangle(frame,(b["x"],b["y"]),(b["x"]+b["width"],b["y"]+b["height"]),c,2)
                cv2.putText(frame,f'{d["label"]} {d["confidence"]:.0%}',(b["x"],max(25,b["y"]-8)),cv2.FONT_HERSHEY_SIMPLEX,.55,c,2)
                cv2.circle(frame,(d["center_x"],d["center_y"]),3,c,-1)
            if self.camera_id=="main":
                red=next((d for d in result["detections"] if d["color"]=="red"),None); green=next((d for d in result["detections"] if d["color"]=="green"),None)
                guide=self.guide.calculate(red,green); start=(frame.shape[1]//2,frame.shape[0]-8)
                if guide.target: cv2.line(frame,start,guide.target,guide.color,4)
                cv2.putText(frame,guide.status,(28,frame.shape[0]-25),cv2.FONT_HERSHEY_SIMPLEX,.62,guide.color,2)
            ok,data=cv2.imencode(".jpg",frame,[cv2.IMWRITE_JPEG_QUALITY,82]); return data.tobytes() if ok else b""

    def stream(self):
        while True:
            yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n"+self.jpeg()+b"\r\n"; time.sleep(.08)
