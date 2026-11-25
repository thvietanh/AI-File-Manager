import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

MODEL_NAME = "gemini-3.5-flash"


def understand_query(query):
    if not query or not query.strip():
        return query

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=query,
            config=types.GenerateContentConfig(
                system_instruction=(
                    "You are a Vietnamese search query understanding assistant. "
                    "Your task is to transform natural language requests into "
                    "concise semantic search queries. "
                    "Extract the main subject, important concepts and user intent. "
                    "Remove conversational words such as 'tìm', 'cho tôi xem', "
                    "'có', 'giúp tôi'. "
                    "Preserve all meaningful keywords and the original meaning. "
                    "Do not invent additional information. "
                    "Do not include file formats such as PDF or DOCX "
                    "unless they describe the actual content. "
                    "Return only the rewritten query in Vietnamese."
                ),
                temperature=0,
                max_output_tokens=100
            )
        )

        result = (response.text or "").strip()
        return result if result else query

    except Exception as e:
        print(f"Query Understanding error: {e}")
        return query
