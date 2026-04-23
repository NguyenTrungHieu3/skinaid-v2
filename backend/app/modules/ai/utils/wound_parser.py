from typing import Dict, Any

# AI class names that are dermatological conditions with no severity suffix
# and need to be remapped to the canonical wound_type stored in the DB.
_DERM_SINGLE_WORD = {
    "ringworm": ("fungal", "mild"),
    "psoriasis": ("psoriasis", "mild"),
}

# Multi-word dermatological prefixes whose first token is the wound type
# but must still be remapped (e.g. "acne" stays "acne", "ringworm" → "fungal")
_DERM_TYPE_REMAP = {
    "ringworm": "fungal",
}


class WoundParser:
    @staticmethod
    def parse_classification(classification: str) -> Dict[str, Any]:
        normalized = classification.lower().strip()

        if normalized in _DERM_SINGLE_WORD:
            wound_type, severity = _DERM_SINGLE_WORD[normalized]
            return {
                "wound_type": wound_type,
                "severity": severity,
                "sub_type": None,
            }

        parts = normalized.split("_")

        if len(parts) < 2:
            return {
                "wound_type": normalized,
                "severity": "mild",
                "sub_type": None,
            }

        raw_type = parts[0]
        wound_type = _DERM_TYPE_REMAP.get(raw_type, raw_type)

        return {
            "wound_type": wound_type,
            "severity": parts[1],
            "sub_type": "_".join(parts[2:]) if len(parts) > 2 else None,
        }

    @staticmethod
    def parse_from_separate_fields(wound_type: str, severity: str) -> Dict[str, Any]:
        normalized_type = wound_type.lower().strip()
        normalized_type = _DERM_TYPE_REMAP.get(normalized_type, normalized_type)

        parts = severity.lower().strip().split("_")

        base_severity = "mild"
        for part in parts:
            if part in ["mild", "moderate", "severe"]:
                base_severity = part
                break

        severity_idx = -1
        for i, part in enumerate(parts):
            if part in ["mild", "moderate", "severe"]:
                severity_idx = i
                break

        sub_type = None
        if severity_idx != -1 and severity_idx < len(parts) - 1:
            sub_type = "_".join(parts[severity_idx + 1:])

        return {
            "wound_type": normalized_type,
            "severity": base_severity,
            "sub_type": sub_type,
        }

    @staticmethod
    def map_wound_type_for_database(ai_wound_type: str) -> str:
        import logging
        logger = logging.getLogger(__name__)
        normalized = ai_wound_type.lower().strip()

        if normalized.startswith("burn"):
            return "burn"
        if normalized in ["cut", "laceration", "incision"]:
            return "cut"
        if normalized in ["abrasion", "scrape", "graze"]:
            return "abrasion"
        if normalized in ["bruise", "contusion", "ecchymosis"]:
            return "bruise"
        # Dermatological remaps
        if normalized in _DERM_TYPE_REMAP:
            return _DERM_TYPE_REMAP[normalized]
        if normalized in ["acne", "psoriasis", "fungal"]:
            return normalized

        logger.warning(f"Unknown wound type '{normalized}', using as-is")
        return normalized

    @staticmethod
    def map_sub_type_for_database(ai_sub_type: str) -> str:
        """Map AI sub_types to Vietnamese equivalents used in the FirstAidGuide database."""
        if not ai_sub_type:
            return ai_sub_type
            
        normalized = ai_sub_type.lower().strip()
        
        # Translation map
        mapping = {
            "skintear": "rách da",
            "blister": "phồng rộp"
        }
        
        return mapping.get(normalized, ai_sub_type)