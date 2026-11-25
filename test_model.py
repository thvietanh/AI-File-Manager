
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    print("ERROR: GEMINI_API_KEY not found in .env")
    exit()

client = genai.Client(api_key=API_KEY)

MODELS = [
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-3.0-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.8-flash"
]

for model in MODELS:
    print(f"\nTesting: {model}")

    try:
        response = client.models.generate_content(
            model=model,
            contents="Viết lại truy vấn: tìm tài liệu về giao thông",
        )

        print("SUCCESS")
        print("Response:", response.text)

    except Exception as e:
        print("FAILED")
        print("Error:", str(e))
