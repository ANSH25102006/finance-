from abc import ABC, abstractmethod

class BaseProvider(ABC):
    """
    BaseProvider is the abstract interface defining LLM interaction.
    Allows easy addition of other providers (Gemini, Claude, Azure, Ollama)
    without modifying routing or service endpoints.
    """

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Submit full structured prompt to the provider client and return text response."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Return True if connection to the client endpoint resolves successfully."""
        pass

    @abstractmethod
    def provider_name(self) -> str:
        """Return provider identifier name (e.g. 'openai', 'mock')."""
        pass

    @abstractmethod
    def model_name(self) -> str:
        """Return active model name configured."""
        pass
