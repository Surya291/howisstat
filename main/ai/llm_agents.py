import base64
import os
from google import genai
from google.genai import types

from pydantic import BaseModel
class GeminiAgent:
    def __init__(self, model_name: str, temperature: float = 0):
        assert model_name in ["gemini-flash-latest", "gemini-3-pro-preview", "gemini-3-flash-preview"] 
        self.model = model_name 
        self.client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY")) 
        self.temperature = temperature 
        self.thinking_budget = 0  

    def get_structured_output(self, system_instruction: str, input_text: str, response_obj: BaseModel) -> dict:
        """ 
        - given the input json comparision  return the judgement 
        """
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=str(input_text)),
                ],
            ),
        ]

        generate_content_config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(
                thinking_budget=self.thinking_budget,
            ),
            temperature=self.temperature,
            response_mime_type="application/json",
            response_json_schema=response_obj.model_json_schema(),
            system_instruction=[types.Part.from_text(text=system_instruction)],
        )

        out = self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=generate_content_config,
        )
        response_out = response_obj.model_validate_json(out.text)
        return response_out.model_dump()

# To run this code you need to install the following dependencies:

