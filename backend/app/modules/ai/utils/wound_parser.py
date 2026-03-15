from typing import Dict, Any

class WoundParser:
    @staticmethod
    def parse_classification(classification: str) -> Dict[str, Any]:
        parts = classification.split("_")

        if len(parts) < 2:
            return {
                "wound_type": classification,
                "severity": "mild",
                "sub_type": None
            }

        return {
            "wound_type": parts[0],
            "severity": parts[1],
            "sub_type": "_".join(parts[2:]) if len(parts) > 2 else None
        }

    @staticmethod
    def parse_from_separate_fields(wound_type: str, severity: str) -> Dict[str, Any]:
        parts = severity.lower().strip().split("_")

        base_severity = "mild"
        for part in parts:
            if part in ["mild", "moderate"]:
                base_severity = part
                break

        severity_idx = -1
        for i, part in enumerate(parts):
            if part in ["mild", "moderate"]:
                severity_idx = i
                break

        sub_type = None
        if severity_idx != -1 and severity_idx < len(parts) - 1:
            sub_type = "_".join(parts[severity_idx + 1:])

        return {
            "wound_type": wound_type.lower().strip(),
            "severity": base_severity,
            "sub_type": sub_type
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

        if normalized not in ["abrasion", "bruise", "burn", "cut"]:
            logger.warning(
                f"Unknown wound type '{normalized}', using as-is"
            )

        return normalized