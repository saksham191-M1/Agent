from jarvis.ai_content.scripts.providers.llm_provider import LLMProvider

class OmniProvider(LLMProvider):
    def generate_json(self, system_prompt: str, user_prompt: str) -> dict:
        """
        Playwright-driven Omni 1.1 automation provider stub.
        Can be plugged into the pipeline without changing downstream consumers.
        """
        raise NotImplementedError("Omni Playwright to be implemented later - skeleton ready")
