# TRIFUSION — Dashboard Kapal Otonom KKI 2026

Dashboard desktop satu halaman untuk monitoring kapal TRIFUSION. Sistem terdiri dari React/Vite/TypeScript, FastAPI, OpenCV, WebSocket telemetry, dua MJPEG camera feed, deteksi buoy merah/hijau, panduan koridor, dan peta SVG Rute A/B.

## Struktur

- `frontend/`: dashboard, peta, kamera, telemetry, dan pengujian Vitest.
- `backend/`: API, WebSocket, OpenCV detector, camera adapter, navigation guide, dan pytest.
- `backend/config/detection.yaml`: seluruh HSV, filter contour, ROI, smoothing, serta switch deteksi kamera.
- `config/routes.json`: waypoint dan warna Rute A/B.
- `assets/`: logo resmi sumber; aset disalin ke `frontend/public/assets` untuk penyajian web.

## Menjalankan cepat

Prasyarat: Python 3.11+ dan Node.js 20+.

Windows PowerShell:

```powershell
Copy-Item .env.example .env
.\start-dev.ps1
```

Linux/Raspberry Pi:

```bash
cp .env.example .env
chmod +x start-dev.sh
./start-dev.sh
```

Buka `http://localhost:5173`; dokumentasi API ada di `http://localhost:8000/docs`. Script menjalankan backend pada port 8000 dan frontend pada 5173.

## Konfigurasi kamera dan simulasi

Edit `.env`. Gunakan `SIMULATION_MODE=true` untuk menguji sistem tanpa hardware. Frame sintetis berisi buoy merah dan hijau; telemetry bergerak setiap detik.

```dotenv
SIMULATION_MODE=false
MAIN_CAMERA_SOURCE=0
UNDERWATER_CAMERA_SOURCE=1
```

Nomor `0`/`1` memilih USB camera. URL atau path juga diterima langsung:

```dotenv
MAIN_CAMERA_SOURCE=rtsp://user:password@192.168.1.10:554/stream
UNDERWATER_CAMERA_SOURCE=http://192.168.1.11:8080/video
# atau C:/video/uji.mp4
```

Jika perangkat gagal dibaca, backend tetap hidup dan UI menampilkan `Camera Offline`. Aktifkan deteksi underwater melalui `detection_enabled.underwater: true` di `backend/config/detection.yaml`.

## Kalibrasi deteksi

Edit `backend/config/detection.yaml` atau gunakan `PUT /api/detection/config`. OpenCV memakai dua rentang merah (hue rendah dan tinggi), satu hijau, Gaussian blur, morphology open/close, luas, circularity, radius, ROI proporsional, dan smoothing. Kalibrasikan HSV pada kondisi cahaya lokasi lomba; nilai hue OpenCV adalah 0–179. Endpoint `GET /api/detection/config` menampilkan konfigurasi aktif.

## Menjalankan manual dan pengujian

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
uvicorn backend.app:app --reload
```

Terminal lain:

```powershell
cd frontend
npm install
npm run dev
```

Validasi lengkap:

```powershell
.\.venv\Scripts\python -m pytest
cd frontend
npm test
npm run lint
npm run build
```

## Raspberry Pi

Gunakan Raspberry Pi OS 64-bit, Python 3.11+, Node 20, dan sebaiknya virtual environment. Jalankan `start-dev.sh`. Untuk produksi, jalankan `uvicorn backend.app:app --host 0.0.0.0 --port 8000`, build frontend dengan `npm run build`, lalu sajikan `frontend/dist` lewat Nginx. Untuk kamera CSI, ekspos sebagai V4L2 (`/dev/video0`) atau stream HTTP/RTSP yang dapat dibaca OpenCV. `opencv-python-headless` tidak membutuhkan desktop GUI.

## API

- `GET /health`, `GET /api/system/status`
- `GET|POST /api/telemetry`
- `GET /api/routes`, `GET|POST /api/routes/active`
- `GET|PUT /api/detection/config`
- `GET /api/cameras/main/stream`, `GET /api/cameras/underwater/stream`
- `GET /api/cameras/{id}/detections`
- `WS /ws/telemetry`

Payload telemetry divalidasi untuk latitude/longitude, heading, speed, distance, baterai, dan packet loss. Kapal dianggap offline bila heartbeat melewati `HEARTBEAT_TIMEOUT_SECONDS`.

## Integrasi hardware berikutnya

Jenis GPS, sensor jarak, protokol ESP32/Raspberry Pi, kalibrasi heading, resolusi/FPS kamera, dan kredensial stream perlu ditentukan dari hardware asli. Adapter saat ini menerima telemetry lewat HTTP dan sumber video yang didukung OpenCV; tidak ada perintah motor/actuator yang dikirim oleh garis panduan.
