class WoundConstants:
    WOUND_TYPES = ["abrasion", "bruise", "burn", "cut", "acne", "fungal", "psoriasis"]
    SEVERITIES = ["mild", "moderate", "severe"]
    BURN_SUBTYPES = ["blister", "skintear"]

    # Dermatological conditions that map from AI class names to wound types
    DERM_TYPE_MAP = {
        "acne": "acne",
        "ringworm": "fungal",
        "psoriasis": "psoriasis",
    }

    VALID_AI_CLASSES = [
        "abrasion_mild",
        "abrasion_moderate",
        "abrasion_severe",
        "bruise_mild",
        "bruise_moderate",
        "bruise_severe",
        "burn_mild",
        "burn_moderate_blister",
        "burn_moderate_skintear",
        "burn_severe",
        "cut_mild",
        "cut_moderate",
        "cut_severe",
        # Dermatological conditions
        "acne_mild",
        "acne_moderate",
        "acne_severe",
        "ringworm",
        "psoriasis",
    ]