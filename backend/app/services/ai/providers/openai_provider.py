import time
import logging
import openai
from openai import OpenAI
from app.services.ai.providers.base_provider import BaseProvider
from app.config import Settings as AISettings

logger = logging.getLogger("openai_provider")


class OpenAIProvider(BaseProvider):
    """
    OpenAIProvider wraps connection and request executions to the OpenAI API completions client,
    implementing retries, exponential backoffs, and error isolation.
    """

    def __init__(self, settings: AISettings):
        self.settings = settings
        if not self.settings.openai_api_key:
            logger.error("Attempted to initialize OpenAIProvider without OPENAI_API_KEY.")
            raise ValueError("OPENAI_API_KEY environment variable is not configured.")
        
        self.client = OpenAI(
            api_key=self.settings.openai_api_key,
            timeout=self.settings.openai_timeout
        )

    def generate(self, prompt: str) -> str:
        model = self.settings.openai_model or self.settings.ai_model
        temp = self.settings.openai_temperature
        max_tok = self.settings.openai_max_tokens
        
        retries = self.settings.ai_retry_count
        backoff = self.settings.ai_retry_backoff

        logger.info(f"Submitting completion request to OpenAI (model: {model}, timeout: {self.settings.openai_timeout}s)")
        
        for attempt in range(retries + 1):
            try:
                start_time = time.time()
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temp,
                    max_tokens=max_tok
                )
                latency = time.time() - start_time
                logger.info(f"OpenAI completion request succeeded in {latency:.2f}s (Attempt {attempt + 1})")

                if not response.choices or not response.choices[0].message.content:
                    raise ValueError("Empty response returned from OpenAI completions endpoint.")
                
                return response.choices[0].message.content.strip()

            except (openai.RateLimitError, openai.APITimeoutError, openai.APIConnectionError) as e:
                logger.warning(f"Transient error encountered in OpenAI query: {str(e)} (Attempt {attempt + 1})")
                if attempt == retries:
                    logger.error("Maximum retry attempts exhausted for OpenAI completions request.")
                    raise e
                time.sleep(backoff * (attempt + 1))
            except Exception as e:
                logger.error(f"Unrecoverable error encountered in OpenAI completions request: {str(e)}")
                raise e

        raise openai.APIError("Completions generation failed to yield results.")

    def health_check(self) -> bool:
        """Submit a tiny ping request to check endpoint and API key validity."""
        try:
            self.client.chat.completions.create(
                model=self.settings.openai_model,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=5
            )
            return True
        except Exception as e:
            logger.warning(f"OpenAI provider health check failed: {str(e)}")
            return False

    def provider_name(self) -> str:
        return "openai"

    def model_name(self) -> str:
        return self.settings.openai_model
