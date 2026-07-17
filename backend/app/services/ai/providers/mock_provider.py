from app.services.ai.providers.base_provider import BaseProvider

class MockProvider(BaseProvider):
    """
    MockProvider delivers deterministic responses for offline usage,
    CI integration, and unit tests without external internet access.
    """

    def __init__(self, model_name_str: str = "mock-model"):
        self._model = model_name_str

    def generate(self, prompt: str) -> str:
        # Returns a mock audit explanation of findings
        return (
            "### Facts\n"
            "- Your monthly spending is under review.\n"
            "- We analyzed your financial records.\n\n"
            "### Observations\n"
            "- A potential duplicate transaction was identified.\n"
            "- Your category budget targets show overruns.\n\n"
            "### Recommendations\n"
            "1. Review subscription price adjustments.\n"
            "2. Establish weekend spending limits."
        )

    def health_check(self) -> bool:
        return True

    def provider_name(self) -> str:
        return "mock"

    def model_name(self) -> str:
        return self._model
