"""Custom exceptions for VelocityBench seed data generation."""


class VLLMError(Exception):
    """Base exception for vLLM-related errors during data generation."""

    pass


class VLLMTimeoutError(VLLMError):
    """Raised when vLLM request exceeds timeout threshold."""

    pass


class VLLMConnectionError(VLLMError):
    """Raised when unable to connect to vLLM server."""

    pass


class VLLMResponseError(VLLMError):
    """Raised when vLLM returns invalid or malformed response."""

    pass
