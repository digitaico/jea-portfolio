"""Domain-level exceptions.

Keeping these in the domain (not in adapters) means high-level code can react to
failures without importing any concrete library exception. That is DIP applied
to error handling.
"""


class TranscriptionError(Exception):
    """Base class for all domain errors in this service."""


class UnsupportedFileError(TranscriptionError):
    """No registered loader can handle the given file."""


class PageError(TranscriptionError):
    """A single page failed to process.

    Caught by the pipeline so one bad page becomes empty text instead of killing
    the whole request (per-page isolation).
    """
