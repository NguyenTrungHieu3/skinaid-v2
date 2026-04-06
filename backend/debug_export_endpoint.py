"""
Debug helper - patches the export endpoint to return the actual traceback
Run: python debug_export_endpoint.py
"""
import asyncio
import sys
import traceback
sys.stdout = open('debug_export.txt', 'w', encoding='utf-8')
sys.stderr = sys.stdout

async def debug():
    try:
        # Simulate what the router does
        from uuid import UUID
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
        
        # Load env
        from dotenv import load_dotenv
        import os
        load_dotenv('.env')
        db_url = os.environ.get('DATABASE_URL', '')
        print(f"DB URL: {db_url[:50]}...")
        
        if not db_url:
            print("ERROR: DATABASE_URL not found")
            return
            
        # Async engine
        engine = create_async_engine(db_url)
        SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        q_id = UUID("9f95d368-058f-406f-8d65-5f2ef17e2825")
        
        async with SessionLocal() as session:
            from app.modules.questionnaires.repository import QuestionnaireRepository
            from app.modules.questionnaires import import_export_service as ie
            
            repo = QuestionnaireRepository(session)
            q = await repo.get_by_id(q_id)
            
            if not q:
                print("ERROR: Questionnaire not found")
                return
            
            print(f"Found: {q.title}")
            print(f"Questions: {len(q.questions or [])}")
            for question in (q.questions or []):
                print(f"  Q{question.order_index}: {question.question_text[:50]} | Answers: {len(question.answers or [])}")
                for ans in (question.answers or []):
                    print(f"    A: {ans.answer_text[:30]} | triage: {ans.triage_level}")
            
            try:
                csv_bytes = ie.export_to_csv(q)
                print(f"\nCSV export OK: {len(csv_bytes)} bytes")
                print("First 500 chars:")
                print(csv_bytes.decode('utf-8-sig')[:500])
            except Exception as e:
                print(f"\nCSV EXPORT ERROR: {e}")
                traceback.print_exc()
                
            try:
                excel_bytes = ie.export_to_excel(q)
                print(f"\nExcel export OK: {len(excel_bytes)} bytes")
            except Exception as e:
                print(f"\nExcel EXPORT ERROR: {e}")
                traceback.print_exc()
                
        await engine.dispose()
        
    except Exception as e:
        print(f"SETUP ERROR: {e}")
        traceback.print_exc()

asyncio.run(debug())
sys.stdout.flush()
