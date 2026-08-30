# OCR SERVICE

A RESTful service that extracts data from documents, like images, pdf`s including handwritten.

Capable of reading PDF, JPG, PNG, TIFF

## Stage 1 - Preprocessing

Returns an optimal image to the following stage which is OCR.

- Renders 300 dpi
- Orientation
- Perspective 
- Deskew
- Crop

### Enhance

If image is degrades:
- Illumination correction
- Contrast Normalization
- Denoise
- remove shadows

### Bad documents
- Background removal
- Adaptive threshold
- Additional enhancement


## Stage 2 - 

- Cloud provider -Gemini Flash OCR 2.0 or 2.7, compare

## Woekflow

### Ingestion



## Stack

- PyMuPDF
- OpenCv
- Numpy
- Pillow
- Pillow-heif


## Prompt
Transcribe all textual content in the document.
Preserve the textual content faithfully.
The document may contain printed text, handwriting, or both.
Do not describe images or visual elements.
Do not infer missing text.

## Image Quality Assessment

- Resolution
- Brightness
- Contrast
- Sharpness
- Illumination uniformity
- Sayuration / glare

Derives a quality score
