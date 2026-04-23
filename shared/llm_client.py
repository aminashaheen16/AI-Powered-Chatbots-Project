import os
from groq import Groq
from dotenv import load_dotenv
import json

load_dotenv()

class LLMClient:
    def __init__(self, model_name="llama-3.3-70b-versatile"):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables.")
        self.client = Groq(api_key=api_key)
        self.model = model_name
        self.system_prompt = "You are NEXUS, a friendly, professional, and intelligent AI Assistant. Always respond naturally and helpfully to the user. Never say you have no greeting to respond to."

    def generate(self, prompt, system_instruction=None):
        sys_msg = system_instruction if system_instruction else self.system_prompt
        messages = [
            {"role": "system", "content": sys_msg},
            {"role": "user", "content": prompt}
        ]
        
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.8,
            max_tokens=1024,
        )
        return completion.choices[0].message.content.strip()

    def generate_stream(self, prompt, system_instruction=None):
        sys_msg = system_instruction if system_instruction else self.system_prompt
        messages = [
            {"role": "system", "content": sys_msg},
            {"role": "user", "content": prompt}
        ]
        
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True,
        )
        for chunk in completion:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def generate_json(self, prompt, system_instruction=None):
        # When generating JSON, we need to be strict
        messages = [
            {"role": "system", "content": "You are a JSON assistant. Respond ONLY with valid JSON. No prose."},
            {"role": "user", "content": prompt}
        ]
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            response_format={"type": "json_object"}
        )
        return completion.choices[0].message.content.strip()
