
import os
from google import genai
from google.genai import types

def transcribe_audio(audio_bytes: bytes, mime_type: str = "audio/mp3") -> str:
    """
    Transcribes audio using Google's Gemini model.
    """
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable not set.")

    client = genai.Client(api_key=api_key)
    
    prompt = "Please provide a highly accurate transcription of this sales call audio. Identify speakers if possible (e.g., Speaker 1, Speaker 2)."

    response = client.models.generate_content(
        model="gemini-2.0-flash-exp",
        contents=[
            types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
            prompt
        ]
    )
    
    return response.text
