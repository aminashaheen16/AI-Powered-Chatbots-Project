import os
import google.generativeai as genai
from dotenv import load_dotenv
import json

load_dotenv()

class LLMClient:
    def __init__(self, model_name="models/gemini-flash-latest"):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables.")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

    def generate(self, prompt, system_instruction=None):
        full_prompt = f"{system_instruction}\n\nUser: {prompt}" if system_instruction else prompt
        response = self.model.generate_content(full_prompt)
        return response.text.strip()

    def generate_stream(self, prompt, system_instruction=None):
        full_prompt = f"{system_instruction}\n\nUser: {prompt}" if system_instruction else prompt
        response = self.model.generate_content(full_prompt, stream=True)
        for chunk in response:
            if chunk.text:
                yield chunk.text

    def generate_json(self, prompt, system_instruction=None):
        json_prompt = f"{prompt}\n\nRespond ONLY with a valid JSON object. Do not include markdown formatting like ```json."
        full_prompt = f"{system_instruction}\n\n{json_prompt}" if system_instruction else json_prompt
        
        response = self.model.generate_content(full_prompt)
        text = response.text.strip()
        
        if text.startswith("```"):
            text = text.split("\n", 1)[-1].rsplit("\n", 1)[0].strip()
            if text.startswith("json"):
                text = text[4:].strip()
                
        return text
