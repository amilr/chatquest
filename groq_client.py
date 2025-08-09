from groq import Groq
import prompts
import json
import os
from ai_client import AIClient

GROQ_MODEL = os.getenv('GROQ_MODEL', 'openai/gpt-oss-20b')

class GroqClient(AIClient):
    def __init__(self, api_key: str):
        super().__init__("Groq")
        self.client = Groq(api_key=api_key)
        #self.model = "moonshotai/kimi-k2-instruct"
        self.model = GROQ_MODEL

    def init_chat(self):
        self.messages = [
            {"role": "system", "content": prompts.AGENT_ROLE}
        ]
        self.log_role(prompts.AGENT_ROLE)

    def prompt(self, text: str):
        self.messages.append({"role": "user", "content": text})
        self.log_prompt(text)

    def get_response(self):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            temperature=1.0
        )
        text = response.choices[0].message.content
        self.messages.append({"role": "assistant", "content": text})
        return text

    def get_json_response(self, type):
        json_schema_text = json.dumps(type.model_json_schema(), indent=2)
        self.messages[-1]["content"] += f"\nThe response must be in JSON of this schema: {json_schema_text}"
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            temperature=0,
            response_format={
                "type": "json_object",
                "schema": type.model_json_schema(),
            }
        )
        json_data = completion.choices[0].message.content
        self.log_response_json(json_data)
        data = type.model_validate_json(json_data)
        self.log_response_object(data)
        return data
