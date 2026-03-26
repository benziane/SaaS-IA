"""SDK exception types."""


class SaaSIAError(Exception):
    """Raised when the SaaS-IA API returns a non-2xx response."""

    def __init__(self, status: int, detail: str) -> None:
        self.status = status
        self.detail = detail
        super().__init__(f"SaaS-IA API error {status}: {detail}")
