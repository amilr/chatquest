from groq import Groq
import prompts
from ai_client import AIClient

class GroqClient(AIClient):
    def __init__(self, api_key: str):
        super().__init__("Groq")
        self.client = Groq(api_key=api_key)
        self.model = "llama3-70b-8192"

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
