import os

from openai_client import OpenAIClient
from together_client import TogetherClient
from groq_client import GroqClient
from mistral_client import MistralClient


def create_client(name: str):
    name = (name or "").lower()
    if name == "openai":
        return OpenAIClient(os.getenv("OPENAI_API_KEY"))
    elif name == "together":
        return TogetherClient(os.getenv("TOGETHER_API_KEY"))
    elif name == "groq":
        return GroqClient(os.getenv("GROQ_API_KEY"))
    elif name == "mistral":
        return MistralClient(os.getenv("MISTRAL_API_KEY"))
    else:
        raise ValueError(f"Unsupported AI client: {name}")
