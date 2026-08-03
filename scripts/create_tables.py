"""Create all tables in the DATABASE_URL from backend/.env. Run once against Supabase."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from sqlalchemy import create_engine  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.models.schema import Base  # noqa: E402

engine = create_engine(get_settings().database_url)
print("target DB:", engine.url.render_as_string(hide_password=True))
Base.metadata.create_all(engine)
print("tables created:", ", ".join(Base.metadata.tables))
