import httpx
from dotenv import load_dotenv
import os
import asyncio

load_dotenv()
AI_API_KEY = os.getenv("AI_API_KEY")
AI_SERVER_URL = "http://localhost:8001/detect_and_classify"

print(f"Using API Key: {AI_API_KEY}")
print(f"Server URL: {AI_SERVER_URL}")

async def call_ai(image_path):
    if not os.path.exists(image_path):
        print(f"Image file not found: {image_path}")
        return
    
    headers = {"X-API-Key": AI_API_KEY}
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            with open(image_path, "rb") as f:
                files = {"file": (os.path.basename(image_path), f, "image/jpeg")}
                response = await client.post(AI_SERVER_URL, files=files, headers=headers)
                
                print(f"📊 Response Status: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    print("✅ SUCCESS!")
                    print(f"📋 Response: {result}")
                    return result
                else:
                    print(f"❌ ERROR: {response.status_code}")
                    print(f"📄 Response text: {response.text}")
                    return None
                    
    except Exception as e:
        print(f"💥 Exception occurred: {e}")
        return None

async def main():
    image_path = r"D:\NCKH\C1SE.24_SkinAid_Capstone1\ai_ml\data\raw_dataset\yolo_dataset\wound_dataset_1_class_1489_images\test\images\gettyimages-173007195-612x612_jpg.rf.1bfc352344f975eddd1280be72b465ab.jpg"
    
    print("=== Testing AI Service with API Key ===")
    await call_ai(image_path)

if __name__ == "__main__":
    asyncio.run(main())