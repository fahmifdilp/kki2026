from datetime import datetime, timezone
import cv2
import numpy as np

class BuoyDetector:
    def __init__(self, config):
        self.config = config
        self.previous = {}

    def update(self, config): self.config = config

    def detect(self, frame, camera_id="main"):
        cfg = self.config
        if not cfg["detection_enabled"].get(camera_id, False): return {"camera_id":camera_id,"timestamp":datetime.now(timezone.utc).isoformat(),"detections":[]}
        blurred = cv2.GaussianBlur(frame, (9, 9), 2)
        hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
        ranges = {
            "red": [(cfg["red_hsv_1"]["lower"], cfg["red_hsv_1"]["upper"]), (cfg["red_hsv_2"]["lower"], cfg["red_hsv_2"]["upper"])],
            "green": [(cfg["green_hsv"]["lower"], cfg["green_hsv"]["upper"])]}
        h, w = frame.shape[:2]; roi = cfg["roi"]
        x0,y0=int(roi["x"]*w),int(roi["y"]*h); x1,y1=int((roi["x"]+roi["width"])*w),int((roi["y"]+roi["height"])*h)
        kernel=np.ones((5,5),np.uint8); found=[]
        for color, bounds in ranges.items():
            mask=np.zeros((h,w),np.uint8)
            for lo,hi in bounds: mask=cv2.bitwise_or(mask,cv2.inRange(hsv,np.array(lo),np.array(hi)))
            region=np.zeros_like(mask); region[max(0,y0):min(h,y1),max(0,x0):min(w,x1)]=mask[max(0,y0):min(h,y1),max(0,x0):min(w,x1)]
            region=cv2.morphologyEx(region,cv2.MORPH_OPEN,kernel); region=cv2.morphologyEx(region,cv2.MORPH_CLOSE,kernel)
            contours,_=cv2.findContours(region,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
            candidates=[]
            for c in contours:
                area=cv2.contourArea(c); perimeter=cv2.arcLength(c,True)
                circularity=4*np.pi*area/(perimeter*perimeter) if perimeter else 0
                (cx,cy),radius=cv2.minEnclosingCircle(c)
                if area>=cfg["minimum_area"] and circularity>=cfg["minimum_circularity"] and radius>=cfg["minimum_radius"]:
                    candidates.append((area,circularity,cx,cy,radius))
            if candidates:
                area,circ,cx,cy,radius=max(candidates)
                prev=self.previous.get((camera_id,color)); a=cfg["smoothing_factor"]
                if prev: cx=a*cx+(1-a)*prev[0]; cy=a*cy+(1-a)*prev[1]; radius=a*radius+(1-a)*prev[2]
                self.previous[(camera_id,color)]=(cx,cy,radius); x=int(cx-radius); y=int(cy-radius); size=int(radius*2)
                found.append({"id":len(found)+1,"color":color,"label":"BOLA MERAH" if color=="red" else "BOLA HIJAU","confidence":round(min(0.99,.55+.35*circ+.1*min(area/4000,1)),2),"center_x":int(cx),"center_y":int(cy),"radius":round(radius,1),"bbox":{"x":x,"y":y,"width":size,"height":size}})
        return {"camera_id":camera_id,"timestamp":datetime.now(timezone.utc).isoformat(),"detections":found}
