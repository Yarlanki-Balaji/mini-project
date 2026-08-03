import re

KEYWORDS: dict[str, list[str]] = {
    "food_restaurants": ["food", "restaurant", "delivery", "cloud kitchen", "tiffin",
                         "cafe", "meal", "biryani", "canteen", "snack", "juice", "bakery"],
    "grocery": ["grocery", "groceries", "kirana", "supermarket", "vegetable", "fruit",
                "provision", "daily needs", "quick commerce"],
    "beauty_personal_care": ["beauty", "skincare", "cosmetic", "salon", "makeup",
                             "haircare", "grooming", "spa", "personal care"],
    "fashion": ["fashion", "clothing", "apparel", "saree", "boutique", "footwear",
                "jewellery", "jewelry", "tailor", "garment", "thrift"],
    "electronics": ["electronics", "gadget", "mobile", "laptop", "accessories",
                    "repair phone", "smartwatch", "headphone", "appliance"],
    "software_apps": ["app", "software", "saas", "platform", "website builder",
                      "automation", "ai tool", "chatbot", "developer"],
    "ecommerce_retail": ["ecommerce", "e-commerce", "online store", "marketplace",
                         "retail", "dropshipping", "reseller", "shop online"],
    "education": ["education", "edtech", "tuition", "coaching", "course", "learning",
                  "exam prep", "school", "college students", "training institute"],
}

# A single strong keyword match scores scores[best] / 3 == round(1/3, 2) == 0.33.
# The threshold must sit below that (with margin, so we're not relying on exact
# float equality) so one match is enough to report a category, while a genuine
# zero-match miss (confidence 0.0) still resolves to category=None.
CONFIDENCE_THRESHOLD = 0.3

# Word-boundary matching with plural tolerance: plain substring containment
# (`kw in text`) produced confidently wrong categories, e.g. "spa" matching
# inside "space", or "app" matching inside "apparel"/"appliance"/"happy".
# `\bkw(s|es)?\b` avoids that while still matching real plurals like
# "restaurants" for the singular keyword "restaurant" (a bare `\bkw\b` would
# NOT match the plural, since the boundary assertion fails between the "t"
# and the "s"). Compiled once at import time, not per call, since this runs
# on every keystroke via the debounced live-preview endpoint.
_KEYWORD_PATTERNS: dict[str, dict[str, re.Pattern]] = {
    slug: {kw: re.compile(rf"\b{re.escape(kw)}(s|es)?\b", re.IGNORECASE) for kw in kws}
    for slug, kws in KEYWORDS.items()
}


def detect_category(idea: str) -> dict:
    scores = {
        slug: sum(1 for pattern in patterns.values() if pattern.search(idea))
        for slug, patterns in _KEYWORD_PATTERNS.items()
    }
    best = max(scores, key=scores.get)
    confidence = round(min(1.0, scores[best] / 3), 2)
    return {
        "category": best if confidence >= CONFIDENCE_THRESHOLD else None,
        "confidence": confidence,
        "closest": best,
    }
