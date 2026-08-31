"""Domain errors."""


class IngestError(Exception):
    """Base class for ingest errors."""


class UnsupportedFileError(IngestError):
    """No decoder can handle the given file."""


class DecodeError(IngestError):
    """The bytes could not be decoded into a usable image."""
