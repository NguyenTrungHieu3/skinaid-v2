import asyncio
from app.modules.firstaid.schemas.domain import FirstAidGuideBase, NO_SEVERITY_TYPES

def test():
    try:
        model = FirstAidGuideBase(title="Test", wound_type="psoriasis")
        print(f"Model created: wound_type={model.wound_type}, severity={model.severity}")
    except Exception as e:
        print(f"Error: {e}")

test()
