# Document Image Ingest + Assessment + Preprocessing (MVP)

A FastAPI app that receives medical-order images (file upload or phone camera),
decodes them to RGB, measures objective quality metrics, then automatically
preprocesses each page using those metrics, and stores everything for review.
No human intervention between stages; no OCR yet.

Modules are separated at the seams where this will later split into
microservices. For the MVP they run in one process behind small ports, wired at
a single composition root.

---

## Pipeline (fully automatic, per page)

```
POST /images (files)
  → decode      bytes -> RGB pages          (image | multi-page PDF)
  → assess      measure quality metrics      (does NOT change pixels)
  → preprocess  consume metrics, clean page  (does NOT re-measure)
  → store       original + processed + quality.json + report.json
  → ocr         2 calls on the processed page (Gemini):
                 (1) verbatim transcription  -> p<N>.json + p<N>.txt
                 (2) structured extraction   -> p<N>_structured.json
  → visualize   show the original to the user
```

`/qc` (evaluation only) shows original vs processed side by side, with the
quality metrics and the preprocessing decisions.

---

## Stages

| Stage | Name          | Responsibility                                              |
|-------|---------------|-------------------------------------------------------------|
| 1     | Upload UI     | Jinja2 page: file picker + phone camera.                    |
| 2     | Decode        | bytes → RGB pages (Pillow + pillow-heif; PyMuPDF for PDF).   |
| 3     | Assess        | Measure quality metrics on the decoded original.            |
| 4     | Preprocess    | Consume the metrics; crop / illumination / denoise / resize. |
| 5     | Store         | Persist original, processed, quality.json, report.json.     |
| 6     | OCR           | Transcribe the processed page via a provider (Gemini first). |
| 7     | Visualize/QC  | Show original to the user; image + transcription in `/qc`.   |

Assessment and preprocessing are separate concerns: assessment **only measures**,
preprocessing **only consumes** those measurements. Neither re-does the other's
work.

---

## Quality metrics (Stage 3, per page)

Measured on the decoded original and persisted as `<id>_p<N>_quality.json`
(with `image_id`, `page_index`, `page_count`, `upload_date`):

- `sharpness` (variance of Laplacian), `noise_sigma` (Immerkaer)
- `brightness`, `contrast`
- `illumination_unevenness` (large-scale luminance spread)
- `skew_angle` (advisory — unreliable on cluttered photos)
- `page_fill_ratio` (paper ÷ frame; low ⇒ background to crop)
- `document_bbox` (normalized crop region enclosing the paper)
- `width`, `height`, `megapixels`

Deliberately **not** measured: orientation (90/180/270) and document count.
Cheap CV gave confidently-wrong answers on real handwritten orders, so they are
excluded rather than shipped as unreliable signals. **Orientation is not handled
anywhere** — not in preprocessing and not at OCR.

---

## Preprocessing (Stage 4) — metric-driven, automatic

Each step reads the stored metrics and decides for itself; it never measures the
image again. Output stays continuous-tone RGB (never binarized), gentle by
default because some orders are handwritten.

| Step         | Fires when …                                   | Metric consumed            |
|--------------|------------------------------------------------|----------------------------|
| Crop         | `page_fill_ratio` below threshold + bbox present | `page_fill_ratio`, `document_bbox` |
| Deskew       | `0.5° < |skew_angle| ≤ 15°`                     | `skew_angle` (advisory)    |
| Illumination | `illumination_unevenness` above threshold      | `illumination_unevenness`  |
| Denoise      | `noise_sigma` above threshold                  | `noise_sigma`              |
| Resize       | longest side above `MAX_IMAGE_DIM`             | (dimensions)               |

No orientation step. Each decision is recorded and persisted as
`<id>_p<N>_report.json` and shown in `/qc`.

---

## Architecture — ports & adapters, one composition root

```
app/
  main.py              composition root: builds + injects all adapters
  config.py            Settings from .env
  api/routes.py        HTTP: /, /images, /qc, /health
  domain/
    models.py          LoadedImage, QualityReport
    ports.py           PageDecoder, QualityAssessor, Preprocessor, ImageStore
    errors.py
  adapters/
    decoder.py         ImageDecoder, PdfDecoder      (Stage 2)
    quality.py         OpenCvQualityAssessor         (Stage 3)
    preprocess.py      MetricDrivenPreprocessor      (Stage 4)
    storage.py         FilesystemImageStore          (Stage 5)
    render.py          decoded RGB -> data URI       (Stage 6)
  templates/  static/
```

**SOLID:** each adapter has one job (SRP); new format/step/backend is a new
adapter or a new step in the list (OCP); adapters sit behind ports and are
injected at the composition root (DIP); ports are small and focused (ISP); any
implementation substitutes for its port (LSP).

Preprocessing steps are individual `PreprocessStep` classes run by
`MetricDrivenPreprocessor` — reorder/add/remove by editing one list in
`main.py`.

---

## Storage layout (`STORAGE_DIR`, default `app/storage`)

Per page, keyed by one `image_id` per upload:

```
<id>_p<N>_original.png     decoded, normalized RGB (QC baseline)
<id>_p<N>_processed.png    preprocessed RGB
<id>_p<N>_quality.json     metrics + provenance
<id>_p<N>_report.json      preprocessing decisions
```

---

## Configuration (`.env`, nothing hardcoded)

`APP_TITLE`, `MAX_UPLOAD_MB`, `PDF_DPI`, `STORAGE_DIR`, `MAX_IMAGE_DIM`.

## Dependencies

`fastapi`, `uvicorn[standard]`, `jinja2`, `python-multipart`, `pydantic-settings`,
`numpy`, `pillow`, `pillow-heif`, `pymupdf`, `opencv-python-headless`.

## Deferred

OCR (Gemini/Mistral), auth on `/qc` and `/files`, object storage, event-driven
service split. Each is a clean addition at an existing seam.

---

## OCR (Stage 6) — automatic, provider-agnostic

After preprocessing, the page selected by `OCR_INPUT` (`processed` by default) is
sent to an OCR provider behind the `OcrProvider` port. Gemini Flash is the first
adapter; Mistral or others swap in without touching the pipeline (OCP/LSP/DIP).
Free-form, Spanish-first transcription — no orientation handling.

Results per page:

```
<id>_p<N>.json    { image_id, page_index, page_count, model, source,
                    transcribed_at, text }
<id>_p<N>.txt     plain transcription
```

Shown in `/qc` beside the image. Per-page isolation: an OCR failure records an
error for that page and does not stop the batch.

### OCR configuration (`.env`)

`GEMINI_API_KEY`, `GEMINI_MODEL`, `GEMINI_MAX_RETRIES`, `GEMINI_TIMEOUT`,
`GEMINI_TEMPERATURE`, `GEMINI_MAX_OUTPUT_TOKENS`, `OCR_INPUT`
(`processed` | `original`), `OCR_LANGUAGE_HINT`.

---

## OCR outputs (Stage 6) — transcription + structured extraction

Two Gemini calls per page (MVP; a single combined call is a later production
optimization behind the same ports):

1. **Transcription** — verbatim free-form text (unchanged): `p<N>.txt` + `p<N>.json`.
2. **Structured extraction** — JSON keyed by the semantic areas, schema-enforced,
   missing values `null`, content outside the areas dropped: `p<N>_structured.json`.
   Stored for a future database service; not consumed yet.

### Prompts and areas — file-driven, no code edits

Paths come from `.env`:

- `OCR_TRANSCRIPTION_PROMPT_FILE` — template with `{language_hint}`.
- `OCR_EXTRACTION_PROMPT_FILE` — template with `{language_hint}` and `{areas}`.
- `OCR_AREAS_FILE` — a richer schema mapping each area to its sub-fields, e.g.

  ```json
  {
    "datos_paciente":  ["nombre", "identificacion", "fecha_nacimiento", "sexo"],
    "datos_examen":    ["tipo", "fecha", "indicacion"],
    "diagnostico":     ["texto", "codigo_cie"],
    "medico_tratante": ["nombre", "registro", "firma_presente"]
  }
  ```

The areas file drives three things at once: the `{areas}` text injected into the
extraction prompt, the JSON response schema Gemini must return, and (later) the
database columns. Edit the file to change what is extracted — no code changes.

Ports: `OcrProvider` (transcribe) and `StructuredExtractor` (extract) are
separate, so transcription and extraction can use different models or later
collapse into one call, without touching the pipeline.
