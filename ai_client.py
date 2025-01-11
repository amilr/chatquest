from pprint import pprint

class AIClient:
    def __init__(self, name: str):
        self.name = name

    def log_prompt(self, prompt: str):
        label = "= " + self.name + " prompt "
        print(label + ("=" * (50 - len(label))))
        print(prompt.strip())
        print("=" * 50)

    def log_response_text(self, text: str):
        label = "= " + self.name + " response JSON "
        print(label + ("=" * (50 - len(label))))
        print(text)
        print("=" * 50)

    def log_response_json(self, json):
        label = "= " + self.name + " response JSON "
        print(label + ("=" * (50 - len(label))))
        pprint(json)
        print("=" * 50)

    def log_response_object(self, obj):
        label = "= " + self.name + " response object "
        print(label + ("=" * (50 - len(label))))
        pprint(obj)
        print("=" * 50)
