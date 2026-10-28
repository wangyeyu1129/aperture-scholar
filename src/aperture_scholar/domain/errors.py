"""Errors callers can handle without knowing a provider's implementation."""


class ApertureError(Exception):
    """Base application error."""


class EvidenceRejected(ApertureError):
    """A quotation cannot be verified in its declared source."""


class CapabilityNotImplemented(ApertureError):
    """An explicitly unfinished capability was requested."""


class ProviderError(ApertureError):
    """An external provider failed or returned an invalid payload."""


class QualityGateRejected(ApertureError):
    """An intermediate artifact must not proceed downstream."""
