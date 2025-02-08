from mistralai import Mistral
import prompts
from pprint import pprint
import httpx
from ai_client import AIClient

class MistralClient(AIClient):
    def __init__(self, api_key: str):
        super().__init__("Mistral")
        timeout_settings = httpx.Timeout(
            connect=5.0,  # Maximum time to establish a connection
            read=10.0,     # Maximum time to wait for data
            write=5.0,    # Maximum time to send data
            pool=10.0     # Maximum time to wait for an available connection in the pool
        )

        # Create an HTTP client with the timeout settings
        http_client = httpx.Client(timeout=timeout_settings)
        self.client = Mistral(api_key=api_key, client=http_client)
        self.model = "mistral-small-latest"

    def init_chat(self):
        self.messages = [
            { "role": "system", "content": prompts.AGENT_ROLE }
        ]
    
        self.log_role(prompts.AGENT_ROLE)

    def prompt(self, text: str):
        self.messages.append({ "role": "user", "content": text })
        self.log_prompt(text)

    def get_response(self):
        response = self.client.chat.complete(
            model=self.model,
            messages=self.messages,
            temperature=1.0
        )

        text = response.choices[0].message.content
        self.messages.append({ "role": "assistant", "content": text })

        self.log_response_text(text)

        return text
    
    def get_json_response(self, type):
        try:
            print('get_json_response 1 ...')
            completion = self.client.chat.parse(
                model=self.model,
                messages=self.messages,
                temperature=0,
                response_format=type
            )
        except Exception as e:
            # One retry attempt
            print('get_json_response 2 ...')
            completion = self.client.chat.parse(
                model=self.model,
                messages=self.messages,
                temperature=0,
                response_format=type
            )

        print('get json_data 1 ...')
        json_data = completion.choices[0].message.content
        self.log_response_json(json_data)

        data = type.model_validate_json(json_data)
        self.log_response_object(data)

        return data