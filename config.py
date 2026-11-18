import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.engine import URL

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent
ssl_ca_value = (os.getenv("DB_SSL_CA") or "").strip()

if ssl_ca_value:
    ssl_ca_path = Path(ssl_ca_value)
    if not ssl_ca_path.is_absolute():
        ssl_ca_path = PROJECT_ROOT / ssl_ca_path
    ssl_ca = str(ssl_ca_path)
else:
    ssl_ca = None


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-this-key")
    MAIL_SERVER = os.getenv("MAIL_SERVER")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587") or "587")
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "True").lower() == "true"
    MAIL_USERNAME = (os.getenv("MAIL_USERNAME") or "").strip() or None
    MAIL_PASSWORD = (os.getenv("MAIL_PASSWORD") or "").strip() or None
    MAIL_DEFAULT_SENDER = (os.getenv("MAIL_DEFAULT_SENDER") or "").strip() or None
    SQLALCHEMY_DATABASE_URI = URL.create(
        drivername="mysql+pymysql",
        username=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306") or "3306"),
        database=os.getenv("DB_NAME", "financas_inteligentes"),
        query={"charset": "utf8mb4"},
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    engine_options = {"pool_pre_ping": True}
    if ssl_ca:
        engine_options["connect_args"] = {"ssl": {"ca": ssl_ca}}
    SQLALCHEMY_ENGINE_OPTIONS = engine_options

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("VERCEL", "0") == "1"
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)