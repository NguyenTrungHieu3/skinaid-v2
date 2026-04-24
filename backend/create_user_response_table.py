import asyncio
from app.core.database import AsyncSessionLocal
from sqlalchemy import text

async def create_table():
    async with AsyncSessionLocal() as session:
        # Create table using raw SQL
        queries = [
            """
            CREATE TABLE IF NOT EXISTS user_questionnaire_responses (
                response_id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                analysis_id    UUID NOT NULL REFERENCES analyses(analysis_id) ON DELETE CASCADE,
                question_id    UUID NOT NULL REFERENCES questions(question_id) ON DELETE CASCADE,
                answer_id      UUID NOT NULL REFERENCES answer_options(answer_id) ON DELETE CASCADE,

                created_at     TIMESTAMP NOT NULL DEFAULT NOW()
            )
            """,
            "CREATE INDEX IF NOT EXISTS idx_user_questionnaire_responses_analysis ON user_questionnaire_responses(analysis_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_questionnaire_responses_question ON user_questionnaire_responses(question_id)"
        ]
        for query in queries:
            await session.execute(text(query))
        await session.commit()
        print("Table user_questionnaire_responses created successfully.")

if __name__ == "__main__":
    asyncio.run(create_table())
