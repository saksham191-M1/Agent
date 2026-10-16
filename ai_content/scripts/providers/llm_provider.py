from abc import ABC, abstractmethod

class LLMProvider(ABC):
    @abstractmethod
    def generate_json(self, system_prompt: str, user_prompt: str) -> dict:
        """
        Generates structured JSON output given a system prompt and a user prompt.
        """
        pass
