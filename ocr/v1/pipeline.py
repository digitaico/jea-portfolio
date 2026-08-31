"""The extraction pipeline: load -> preprocess -> transcribe -> persist."""

from app.domain.errors import PageError, UnsupportedFileError
from app.domain.models import DocumentResult, Page
from app.domain.ports import OcrEngine, Preprocessor, ResultSink, SourceLoader


class ExtractionPipeline:
    """Coordinates the four stages.

    DIP in action: this class receives the four ports by constructor injection
    and imports no concrete adapter. Swapping Gemini for another engine, or
    adding a new file format, never touches this file.
    """

    def __init__(
        self,
        loaders: list[SourceLoader],
        preprocessor: Preprocessor,
        ocr: OcrEngine,
        sink: ResultSink,
        model_name: str,
    ) -> None:
        self._loaders = loaders
        self._preprocessor = preprocessor
        self._ocr = ocr
        self._sink = sink
        self._model_name = model_name

    def _select_loader(
        self, filename: str, content_type: str | None
    ) -> SourceLoader:
        # OCP: loaders is a list. New formats are registered in the composition
        # root; this selection logic stays closed to modification.
        for loader in self._loaders:
            if loader.supports(filename, content_type):
                return loader
        raise UnsupportedFileError(
            f"No loader can handle '{filename}' ({content_type})."
        )

    async def run(
        self, data: bytes, filename: str, content_type: str | None
    ) -> DocumentResult:
        loader = self._select_loader(filename, content_type)
        images = loader.load(data, filename)

        pages: list[Page] = []
        for index, image in enumerate(images):
            # Per-page isolation: a failure here yields empty text for this page
            # only, so the rest of the document still returns.
            try:
                cleaned = self._preprocessor.clean(image)
                text = await self._ocr.transcribe(cleaned)
            except PageError:
                text = ""
            pages.append(Page(index=index, text=text))

        result = DocumentResult(
            source_filename=filename,
            model=self._model_name,
            pages=pages,
        )
        self._sink.save(result)
        return result
