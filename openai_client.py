import os
from openai import OpenAI
import prompts
from ai_client import AIClient

class OpenAIClient(AIClient):
    def __init__(self, api_key: str):
        super().__init__("OpenAI")
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4.1-mini-2025-04-14"

    def init_chat(self):
        self.messages = [
            { "role": "system", "content": prompts.AGENT_ROLE }
        ]
    
        self.log_role(prompts.AGENT_ROLE)

    def prompt(self, text: str):
        self.messages.append({ "role": "user", "content": text })
        self.log_prompt(text)

    def get_response(self):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            temperature=1.0,
            timeout=20
        )

        text = response.choices[0].message.content
        self.messages.append({ "role": "assistant", "content": text })
        return text
    
    def get_json_response(self, type):
        try:
            completion = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=self.messages,
                response_format=type,
                temperature=1.0,
                timeout=20
            )
        except Exception:
            print('retrying ...')
            completion = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=self.messages,
                response_format=type,
                temperature=1.0,
                timeout=20
            )

        data = completion.choices[0].message.parsed
        self.log_response_object(data)

        return data
