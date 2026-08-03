from app.config import get_settings


def test_settings_read_env(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./x.db")
    monkeypatch.setenv("GEMINI_API_KEY", "g-key")
    monkeypatch.setenv("GROQ_API_KEY", "q-key")
    get_settings.cache_clear()
    s = get_settings()
    assert s.database_url == "sqlite:///./x.db"
    assert s.gemini_api_key == "g-key"
    assert s.groq_api_key == "q-key"
    assert s.cors_origins == ["http://localhost:5173"]
