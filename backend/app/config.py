from dataclasses import dataclass
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)


@dataclass(frozen=True)
class Settings:
    app_name: str = "IRCTC Booking Platform API"
    api_prefix: str = "/api"
    environment: str = os.getenv("ENVIRONMENT", "development")
    database_url: str = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR / 'irctc.db'}")
    allowed_origins: tuple[str, ...] = tuple(
        o.strip() for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:4200,http://localhost:5500,*").split(",") if o.strip()
    )
    pnr_seed: int = int(os.getenv("PNR_SEED", "1000000000"))


settings = Settings()
