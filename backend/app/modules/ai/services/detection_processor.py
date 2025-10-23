from typing import Dict, Any, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class DetectionProcessor:
    SEVERITY_PRIORITY = {"moderate": 2, "mild": 1}
    BURN_SUBTYPE_PRIORITY = {"skintear": 2, "blister": 1}
    MIN_CONFIDENCE_THRESHOLD = 0.65

    WOUND_TYPE_MAPPING = {
        "abrasion": "abrasion",
        "bruise": "bruise",
        "burn": "burn",
    }

    AVAILABLE_WOUND_TYPES = ["abrasion", "bruise", "burn"]

    @classmethod
    def extract_base_severity(cls, severity_str: str) -> str:
        if not severity_str:
            return "mild"

        severity_lower = severity_str.lower().strip()
        parts = severity_lower.split("_")

        for part in parts:
            if part in cls.SEVERITY_PRIORITY:
                logger.debug(f"Extracted severity '{part}' from '{severity_str}'")
                return part

        logger.warning(f"No valid severity in '{severity_str}', defaulting to 'mild'")
        return "mild"

    @classmethod
    def extract_burn_subtype(cls, severity_str: str, wound_type: str = "") -> str:
        burn_subtypes = ["blister", "skintear"]

        search_text = f"{wound_type}_{severity_str}".lower()
        parts = search_text.split("_")

        for part in parts:
            if part in burn_subtypes:
                logger.debug(f"Found burn sub-type '{part}'")
                return part

        return ""

    @classmethod
    def parse_burn_classification(
        cls,
        wound_type: str,
        severity: Optional[str] = None
    ) -> Tuple[str, str, str]:
        """
        Parse burn classification.
        """
        base_severity = cls.extract_base_severity(severity) if severity else "mild"
        sub_type = cls.extract_burn_subtype(severity or "", wound_type)

        logger.debug(
            f"Parsed burn: {wound_type}/{severity} -> "
            f"base={base_severity}, sub_type={sub_type}"
        )

        return "burn", base_severity, sub_type

    @classmethod
    def map_wound_type_for_database(cls, ai_wound_type: str) -> str:
        """
        Map AI wound type sang database wound type.
        """
        if ai_wound_type.lower().startswith("burn"):
            return "burn"

        ai_wound_type_lower = ai_wound_type.lower().strip()
        mapped_type = cls.WOUND_TYPE_MAPPING.get(ai_wound_type_lower, ai_wound_type_lower)
        if mapped_type not in cls.AVAILABLE_WOUND_TYPES:
            logger.warning(
                f"Wound type '{mapped_type}' not supported by AI, "
                f"using 'abrasion' as fallback"
            )
            mapped_type = "abrasion" 

        logger.debug(f"Mapped: {ai_wound_type} -> {mapped_type}")
        return mapped_type

    @classmethod
    def get_parsed_severity_for_storage(cls, wound_type: str, severity: str) -> tuple[str, Optional[str]]:
        """
        Lấy base_severity và sub_type để lưu vào database.
        """
        if not severity:
            return "mild", None

        # For burn, use specific parsing
        if wound_type.lower() == "burn":
            _, base_severity, sub_type = cls.parse_burn_classification(wound_type, severity)
            return base_severity, sub_type

        # For other wound types, extract base severity and check for sub_type
        base_severity = cls.extract_base_severity(severity)
        sub_type = cls.extract_sub_type(severity, wound_type)
        return base_severity, sub_type

    @classmethod
    def extract_sub_type(cls, severity_str: str, wound_type: str) -> Optional[str]:
        """
        Extract sub_type from severity string for non-burn wounds.
        """
        if not severity_str:
            return None

        severity_lower = severity_str.lower().strip()
        parts = severity_lower.split("_")

        # For burn, sub_types are blister, skintear
        if wound_type.lower() == "burn":
            burn_subtypes = ["blister", "skintear"]
            for part in parts[1:]:  # Skip first part as it's base severity
                if part in burn_subtypes:
                    return part

        # For other wounds, assume no sub_type for now
        return None

    @classmethod
    def calculate_detection_priority(cls, detection: Dict[str, Any]) -> Tuple[int, int, float]:

        severity_str = detection.get("severity", "mild")
        wound_type = detection.get("wound_type", "").lower()

        base_severity = cls.extract_base_severity(severity_str)
        severity_priority = cls.SEVERITY_PRIORITY.get(base_severity, 0)
        confidence = detection.get("confidence", 0)

        burn_subtype_priority = 0
        if wound_type == "burn" and base_severity == "moderate":
            sub_type = cls.extract_burn_subtype(severity_str, wound_type)
            if sub_type:
                burn_subtype_priority = cls.BURN_SUBTYPE_PRIORITY.get(sub_type, 0)
                logger.debug(
                    f"Burn: {severity_str} -> "
                    f"priority=({severity_priority}, {burn_subtype_priority}, {confidence:.2f})"
                )

        return (severity_priority, burn_subtype_priority, confidence)

    @classmethod
    def create_wound_group_key(cls, detection: Dict[str, Any]) -> str:
        """
        Tạo group key cho detection, xét đến subtype để phân biệt các vết thương khác nhau.
        """
        wound_type = detection.get("wound_type", "unknown")
        severity = detection.get("severity", "")

        # Với burn, xét đến subtype để phân biệt các loại khác nhau
        if wound_type.lower() == "burn":
            sub_type = cls.extract_burn_subtype(severity, wound_type)
            if sub_type:
                return f"{wound_type}_{sub_type}"

        # Với các loại khác hoặc burn không có subtype, dùng wound_type
        return wound_type

    @classmethod
    def determine_primary_and_secondary_detections(
        cls,
        detections: List[Dict[str, Any]]
    ) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Chọn primary và secondary detections.

        Logic:
        1. Filter: confidence >= 65%
        2. Select primary: highest priority
        3. Select secondary: best in each wound_type+subtype group (exclude primary group)
        4. Sort secondary by priority
        """
        if not detections:
            return None, []

        # Step 1: Filter reliable
        reliable_detections = [
            d for d in detections
            if d.get("confidence", 0) >= cls.MIN_CONFIDENCE_THRESHOLD
        ]

        if not reliable_detections:
            logger.warning(
                f"No detections meet threshold ({cls.MIN_CONFIDENCE_THRESHOLD:.0%})"
            )
            return None, []

        # Step 2: Select primary
        primary = max(reliable_detections, key=cls.calculate_detection_priority)
        primary["is_primary"] = True

        logger.info(
            f"Primary: {primary.get('wound_type')}/{primary.get('severity')} "
            f"(conf: {primary.get('confidence'):.2%})"
        )

        # Step 3: Select secondary
        remaining = [d for d in reliable_detections if d != primary]

        if not remaining:
            return primary, []

        # Group by wound_type + subtype (nếu có)
        groups = {}
        for det in remaining:
            group_key = cls.create_wound_group_key(det)
            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(det)

        # Select best in each group (exclude primary group)
        primary_group_key = cls.create_wound_group_key(primary)
        secondary = []

        for group_key, group_dets in groups.items():
            if group_key != primary_group_key:
                best = max(group_dets, key=cls.calculate_detection_priority)
                secondary.append(best)

        # Sort by priority
        secondary.sort(key=cls.calculate_detection_priority, reverse=True)

        logger.info(f"Secondary: {len(secondary)} detections")

        return primary, secondary