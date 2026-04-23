import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

class LLMClient:
    def __init__(self, model_name="gemini-1.5-flash"):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            # Fallback for testing or if environment isn't set yet
            api_key = "dummy_key" 
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

    def generate(self, prompt, system_instruction=None):
        if system_instruction:
            full_prompt = f"System: {system_instruction}\n\nUser: {prompt}"
        else:
            full_prompt = prompt
        
        response = self.model.generate_content(full_prompt)
        return response.text.strip()

    def generate_json(self, prompt, system_instruction=None):
        response = self.model.generate_content(
            f"{system_instruction}\n\n{prompt}" if system_instruction else prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        return response.text.strip()
