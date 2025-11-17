# app/modules/ai/utils/wound_parser.py
from typing import Dict, Any

class WoundParser:
    @staticmethod
    def parse_classification(classification: str) -> Dict[str, Any]:
        """
        Parse wound classification string.
        
        Examples:
            "burn_moderate_blister" -> {wound_type: "burn", severity: "moderate", sub_type: "blister"}
            "abrasion_mild" -> {wound_type: "abrasion", severity: "mild", sub_type: None}
        """
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
        """
        Parse when wound_type and severity are separate.
        
        Args:
            wound_type: "burn"
            severity: "moderate_blister" or "moderate"
        """
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