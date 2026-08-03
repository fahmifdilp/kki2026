from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[1]

class Settings(BaseSettings):
    simulation_mode: bool = True
    main_camera_source: str = "0"
    underwater_camera_source: str = "1"
    heartbeat_timeout_seconds: float = 5
    frontend_origin: str = "http://localhost:5173"
    detection_config_path: str = str(ROOT / "backend/config/detection.yaml")
    routes_config_path: str = str(ROOT / "config/routes.json")
    model_config = SettingsConfigDict(env_file=ROOT / ".env", extra="ignore")

settings = Settings()
