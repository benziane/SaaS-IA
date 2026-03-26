"""
saas-ia-client -- Official SaaS-IA Python SDK

Usage::

    from saas_ia import SaaSIAClient

    async with SaaSIAClient(base_url="http://localhost:8004") as client:
        await client.login("user@example.com", "password")
        transcriptions = await client.transcription.list()
"""

from saas_ia.client import SaaSIAClient  # noqa: F401
from saas_ia.exceptions import SaaSIAError  # noqa: F401

__version__ = "1.0.0"
__all__ = ["SaaSIAClient", "SaaSIAError"]
