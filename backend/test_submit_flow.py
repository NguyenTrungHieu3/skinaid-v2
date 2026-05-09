import asyncio
import httpx
from app.core.database import AsyncSessionLocal
from app.modules.ai.models.analysis import Analysis
from app.modules.questionnaires.models.question import Question
from app.modules.questionnaires.models.answer_option import AnswerOption
from sqlmodel import select

async def get_test_data():
    async with AsyncSessionLocal() as session:
        # Get an analysis
        analysis = (await session.execute(select(Analysis).limit(1))).scalars().first()
        if not analysis:
            print("No analysis found in DB")
            return None, None, None
            
        # Get a question and its answers
        question = (await session.execute(select(Question).limit(1))).scalars().first()
        if not question:
            print("No questions found in DB")
            return None, None, None
            
        answer = (await session.execute(select(AnswerOption).where(AnswerOption.question_id == question.question_id).limit(1))).scalars().first()
        if not answer:
            print("No answers found for question")
            return None, None, None
            
        return str(analysis.analysis_id), str(question.question_id), str(answer.answer_id)

async def test_apis():
    print("Fetching test data from DB...")
    analysis_id, question_id, answer_id = await get_test_data()
    
    if not analysis_id:
        print("Cannot proceed without test data.")
        return

    print(f"Test Data:")
    print(f"Analysis ID: {analysis_id}")
    print(f"Question ID: {question_id}")
    print(f"Answer ID:   {answer_id}\n")

    payload = {
        "analysis_id": analysis_id,
        "detections": [{"wound_type": "burn"}],
        "answers": [{
            "question_id": question_id,
            "answer_ids": [answer_id]
        }],
        "forward_to_synthesis": False
    }

    print("1. Submitting to POST /api/v1/wound-responses/submit")
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000") as client:
        # We don't have token but the route might not be protected or we use guest mode
        response = await client.post("/api/v1/wound-responses/submit", json=payload)
        print(f"Status: {response.status_code}")
        print("Response:", response.json())
        print("\n------------------\n")
        
        print(f"2. Fetching history from GET /api/v1/ai/analysis/{analysis_id}")
        response = await client.get(f"/api/v1/ai/analysis/{analysis_id}")
        print(f"Status: {response.status_code}")
        data = response.json()
        print("Response (user_responses only):")
        if "data" in data and "user_responses" in data["data"]:
            import json
            print(json.dumps(data["data"]["user_responses"], indent=2))
        else:
            print(data)

if __name__ == "__main__":
    asyncio.run(test_apis())
