from app.services.planner import detect_category


def test_food_idea_maps_to_food_restaurants():
    out = detect_category("I want to start a food delivery startup for students")
    assert out["category"] == "food_restaurants"
    assert out["confidence"] > 0.3


def test_out_of_scope_returns_none_with_closest():
    out = detect_category("industrial drone repair workshop")
    assert out["category"] is None
    assert out["closest"] in {
        "food_restaurants", "grocery", "beauty_personal_care", "fashion",
        "electronics", "software_apps", "ecommerce_retail", "education",
    }


def test_endpoint_returns_detection(client):
    r = client.get("/api/detect-category", params={"idea": "online saree boutique"})
    assert r.status_code == 200
    assert r.json()["category"] == "fashion"


# --- Additional tests: pin the confidence-threshold bug fix and discriminate
# behavior the three tests above don't exercise (see task-8-report.md for the
# deliberate-breakage proof behind each one). ---


def test_single_keyword_match_is_enough_to_report_a_category():
    # This is the exact scenario from the reported bug: "grocery" is the ONLY
    # keyword hit (one match, confidence 0.33). Under the brief's original
    # CONFIDENCE_THRESHOLD = 0.34, 0.33 >= 0.34 is False and this idea was
    # wrongly reported as out-of-scope (category=None). It must match.
    out = detect_category("I want to open a grocery store")
    assert out["category"] == "grocery"
    assert out["confidence"] == 0.33


def test_higher_scoring_category_wins_over_a_weaker_cross_category_match():
    # "grocery" and "daily needs" both hit the grocery category (score 2);
    # "app" independently hits software_apps (score 1). Both categories have
    # genuine, non-zero matches, so this proves argmax picks the true highest
    # scorer rather than e.g. the first category with any match at all, or
    # the last category evaluated.
    out = detect_category("grocery app for daily needs")
    assert out["category"] == "grocery"
    assert out["closest"] == "grocery"


def test_confidence_increases_with_more_keyword_matches():
    one_match = detect_category("grocery store")
    two_matches = detect_category("grocery kirana shop")
    assert one_match["category"] == "grocery"
    assert two_matches["category"] == "grocery"
    assert two_matches["confidence"] > one_match["confidence"]
    assert one_match["confidence"] == 0.33
    assert two_matches["confidence"] == 0.67


def test_endpoint_surfaces_service_result_faithfully(client):
    idea = "industrial drone repair workshop"
    r = client.get("/api/detect-category", params={"idea": idea})
    assert r.status_code == 200
    # The router must forward the service's dict as-is (all three keys,
    # including a None category), not a status-only or partial response.
    assert r.json() == detect_category(idea)
