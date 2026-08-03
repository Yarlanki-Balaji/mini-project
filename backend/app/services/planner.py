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


def detect_category(idea: str) -> dict:
    text = idea.lower()
    scores = {
        slug: sum(1 for kw in kws if kw in text) for slug, kws in KEYWORDS.items()
    }
    best = max(scores, key=scores.get)
    confidence = round(min(1.0, scores[best] / 3), 2)
    return {
        "category": best if confidence >= CONFIDENCE_THRESHOLD else None,
        "confidence": confidence,
        "closest": best,
    }
