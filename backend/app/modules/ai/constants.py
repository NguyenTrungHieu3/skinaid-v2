class WoundConstants:
    WOUND_TYPES = ["abrasion", "bruise", "burn"]
    SEVERITIES = ["mild", "moderate"]
    BURN_SUBTYPES = ["blister", "skintear"]
    
    # Validation
    VALID_AI_CLASSES = [
        "abrasion_mild",
        "abrasion_moderate",
        "bruise_mild",
        "bruise_moderate",
        "burn_mild",
        "burn_moderate_blister",
        "burn_moderate_skintear"
    ]