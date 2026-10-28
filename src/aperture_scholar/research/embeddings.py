"""Replaceable embedding implementation; no model loads during imports."""

from collections.abc import Sequence

from aperture_scholar.domain.errors import CapabilityNotImplemented


class ScientificEmbeddings:
    def embed(self, texts: Sequence[str]) -> Sequence[Sequence[float]]:
        """TODO E04: SPECTER2/API adapter with versioned model, batching and vector cache.

        Return vectors in input order; never substitute random or lexical vectors.
        """
        raise CapabilityNotImplemented("E04: scientific embeddings adapter")
