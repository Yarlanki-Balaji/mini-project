import json

from app.models.schema import CategoryInsight
from app.routers import analyze


def _seed(db):
    db.add(CategoryInsight(
        category="food_restaurants", agent="customer_insight",
        payload={"positive_pct": 60.0, "neutral_pct": 15.0, "negative_pct": 25.0,
                 "top_positive_keywords": ["taste"], "top_negative_keywords": ["delivery"]},
        dataset="Yelp Open Dataset (sampled)", sample_size=1000))
    db.commit()


def _events(resp):
    tokens, done = [], False
    for line in resp.iter_lines():
        if line.startswith("data: "):
            payload = json.loads(line[6:] or "{}")
            if "t" in payload:
                tokens.append(payload["t"])
        if line.startswith("event: done"):
            done = True
    return tokens, done


def _raw_lines(resp):
    return list(resp.iter_lines())


def test_stream_happy_path(client, db, monkeypatch):
    _seed(db)
    monkeypatch.setattr(analyze, "stream_strategy", lambda prompt: iter(["Great ", "plan"]))
    with client.stream("GET", "/api/strategy/stream",
                       params={"idea": "food delivery for students"}) as r:
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("text/event-stream")
        tokens, done = _events(r)
    assert "".join(tokens) == "Great plan"
    assert done


def test_stream_out_of_scope_is_friendly(client, db):
    with client.stream("GET", "/api/strategy/stream",
                       params={"idea": "industrial drone repair workshop"}) as r:
        tokens, done = _events(r)
    assert done
    assert "closest" in "".join(tokens).lower()


def test_stream_category_without_insights_is_friendly(client, db):
    # matched category but no precomputed row yet (e.g. ecommerce_retail in the slice)
    with client.stream("GET", "/api/strategy/stream",
                       params={"idea": "online store marketplace for resellers"}) as r:
        tokens, done = _events(r)
    assert done
    assert "not been computed" in "".join(tokens)


def test_stream_token_json_escaping_round_trips(client, db, monkeypatch):
    """A token containing a double quote and a newline must survive the wire
    format round trip: proves data: lines are JSON-encoded, not naive
    string interpolation (which would break the SSE framing / corrupt the
    JSON on quotes or embedded newlines)."""
    _seed(db)
    tricky = 'He said "hi"\nthen left'
    monkeypatch.setattr(analyze, "stream_strategy", lambda prompt: iter([tricky]))
    with client.stream("GET", "/api/strategy/stream",
                       params={"idea": "food delivery for students"}) as r:
        tokens, done = _events(r)
    assert "".join(tokens) == tricky
    assert done


def test_stream_happy_path_headers(client, db, monkeypatch):
    """The happy path must set Cache-Control and X-Accel-Buffering so
    proxies don't buffer the stream, in addition to the SSE content type."""
    _seed(db)
    monkeypatch.setattr(analyze, "stream_strategy", lambda prompt: iter(["hi"]))
    with client.stream("GET", "/api/strategy/stream",
                       params={"idea": "food delivery for students"}) as r:
        assert r.headers["content-type"].startswith("text/event-stream")
        assert r.headers["cache-control"] == "no-cache"
        assert r.headers["x-accel-buffering"] == "no"
        list(r.iter_lines())


def test_stream_done_is_always_the_final_frame(client, db, monkeypatch):
    """For all three outcomes, the `event: done` frame (the two SSE lines
    "event: done" then "data: {}") must be present and must be the last
    frame emitted -- otherwise a client reading the stream sequentially
    could see tokens arrive after "done" (or never see done at all),
    leaving EventSource open indefinitely."""
    _seed(db)
    monkeypatch.setattr(analyze, "stream_strategy", lambda prompt: iter(["Great ", "plan"]))
    with client.stream("GET", "/api/strategy/stream",
                       params={"idea": "food delivery for students"}) as r:
        lines = [l for l in _raw_lines(r) if l]
    assert lines[-2:] == ["event: done", "data: {}"]

    with client.stream("GET", "/api/strategy/stream",
                       params={"idea": "industrial drone repair workshop"}) as r:
        lines = [l for l in _raw_lines(r) if l]
    assert lines[-2:] == ["event: done", "data: {}"]

    with client.stream("GET", "/api/strategy/stream",
                       params={"idea": "online store marketplace for resellers"}) as r:
        lines = [l for l in _raw_lines(r) if l]
    assert lines[-2:] == ["event: done", "data: {}"]


def test_stream_prompt_contains_agent_payload_data(client, db, monkeypatch):
    """The prompt handed to stream_strategy must be built from the real
    agent payload (not a bare idea string) -- assert a distinctive seeded
    value ("delivery", the seeded top_negative_keywords entry) shows up in
    the captured prompt."""
    _seed(db)
    captured = {}

    def fake_stream(prompt):
        captured["prompt"] = prompt
        return iter(["ok"])

    monkeypatch.setattr(analyze, "stream_strategy", fake_stream)
    with client.stream("GET", "/api/strategy/stream",
                       params={"idea": "food delivery for students"}) as r:
        list(r.iter_lines())
    assert "delivery" in captured["prompt"]
    assert "taste" in captured["prompt"]
