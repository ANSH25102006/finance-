import logging
from app.config import Settings as AISettings, get_settings as get_ai_settings
from app.services.ai.providers.base_provider import BaseProvider
from app.services.ai.providers.openai_provider import OpenAIProvider
from app.services.ai.providers.mock_provider import MockProvider

logger = logging.getLogger("provider_factory")


class ProviderFactory:
    """
    ProviderFactory instantiates the selected LLM provider based on settings.
    Allows decoupling routers and services from provider implementations.
    """

    @staticmethod
    def get_provider(settings: AISettings = None) -> BaseProvider:
        if settings is None:
            settings = get_ai_settings()

        provider_name = settings.ai_provider.strip().lower()
        logger.info(f"Selecting LLM Provider: {provider_name}")

        if provider_name == "openai":
            return OpenAIProvider(settings)
        elif provider_name == "mock":
            return MockProvider(settings.ai_model)
        else:
            logger.error(f"Attempted to configure unsupported LLM provider: {provider_name}")
            raise ValueError(
                f"Unsupported AI provider: '{provider_name}'. Supported options are 'openai', 'mock'."
            )
